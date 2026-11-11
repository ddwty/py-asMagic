"""Camera-only frames share the proven AR RGB codec and receive path."""
import inspect
import io
import json
from pathlib import Path
import threading

import numpy as np
from PIL import Image
import pytest

import asmagic
from asmagic import ARDataSubscriber, CameraDataSubscriber, CameraFrame, subscribe
from asmagic.diagnostics import inspect_frame, run_stream_check
from asmagic.proto import phone_msg_pb2
from test_images_geometry import hevc_sequence


@pytest.fixture
def jpeg_message():
    image = np.zeros((12, 18, 3), dtype=np.uint8)
    image[:6, :9] = (240, 20, 10)
    image[:6, 9:] = (20, 230, 30)
    image[6:, :9] = (10, 30, 240)
    image[6:, 9:] = (220, 200, 10)
    data = io.BytesIO()
    Image.fromarray(image).save(data, format="JPEG", quality=95, subsampling=0)
    return phone_msg_pb2.Phone(
        timestamp=1700000000.25, source_timestamp=12.5, frame_id=1,
        rgb_width=18, rgb_height=12, color_img=data.getvalue(), rgb_codec=1,
        image_rotation_quarter_turns_clockwise=1)


def test_camera_public_api_metadata_rgb_and_rotation(jpeg_message):
    frame = CameraDataSubscriber.decode(jpeg_message.SerializeToString())
    assert isinstance(frame, CameraFrame)
    assert frame.timestamp == 1700000000.25 and frame.source_timestamp == 12.5
    assert frame.frame_id == 1 and (frame.width, frame.height) == (18, 12)
    assert frame.image.shape == (12, 18, 3) and frame.image.dtype == np.uint8
    assert frame.image is frame.image and frame.image is frame.color_array
    assert frame.has_image and frame.image_bytes == jpeg_message.color_img
    assert frame.rgb_codec_name == "jpeg" and frame.image_rotation_quarter_turns_clockwise == 1
    np.testing.assert_equal(frame.image_upright, np.rot90(frame.image, -1))
    assert frame.image[0, 0, 0] > 200 and frame.image[0, 0, 2] < 60
    for name in ("depth", "depth_img", "local_pose", "global_pose", "camera_intrinsics", "has_pose", "session_identifier"):
        assert not hasattr(frame, name)
    assert frame.protobuf == jpeg_message


def test_camera_and_ar_share_color_image_contract(jpeg_message):
    payload = jpeg_message.SerializeToString()
    camera = CameraDataSubscriber.decode(payload)
    ar = ARDataSubscriber.decode(payload)
    assert camera.has_color_image == ar.has_color_image
    assert camera.color_bytes == ar.color_bytes == jpeg_message.color_img
    assert (camera.rgb_width, camera.rgb_height) == (ar.rgb_width, ar.rgb_height)
    np.testing.assert_array_equal(camera.color_array, ar.color_array)
    np.testing.assert_array_equal(camera.color_upright, ar.color_upright)
    assert camera.image is camera.color_array
    np.testing.assert_array_equal(camera.image_upright, camera.color_upright)
    for receiver in (CameraDataSubscriber, ARDataSubscriber):
        empty = receiver.decode(phone_msg_pb2.Phone().SerializeToString())
        assert not empty.has_color_image
        assert empty.color_array is None and empty.color_upright is None


def test_camera_defaults_empty_and_registry():
    frame = CameraFrame()
    assert frame.image is None and frame.image_upright is None and not frame.has_image
    assert not frame.show_images()
    assert CameraDataSubscriber.__init__.__defaults__ == (8105, 32, False, False)
    assert asmagic.STREAMS["camera"].subscriber is CameraDataSubscriber
    assert asmagic.STREAMS["camera"].port == 8105
    assert "CameraDataSubscriber" in asmagic.__all__ and "CameraFrame" in asmagic.__all__
    assert inspect.signature(CameraDataSubscriber.receive).parameters["timeout"].default is None


def test_camera_jpeg_over_tcp_and_finite_diagnostic(publisher, jpeg_message):
    socket, connect = publisher
    sub = connect(CameraDataSubscriber)
    socket.send(jpeg_message.SerializeToString())
    frame = sub.receive(timeout=2000)
    assert frame.image.shape == (12, 18, 3)
    assert sub.received_frames == 1 and sub.last_received_at is not None
    assert sub.receive(timeout=0) is None
    inspection = inspect_frame("camera", frame, decode_images=True)
    assert inspection.usable and not inspection.errors
    assert inspection.values["rgb_shape"] == [12, 18, 3]
    socket.send(jpeg_message.SerializeToString())
    result = run_stream_check("camera", sub, duration=1, count=1)
    assert result.status == "received" and result.frames == 1
    assert result.component_frames["rgb_decoded"] == 1


def test_camera_named_factory_uses_separate_port():
    with subscribe("camera", "127.0.0.1") as sub:
        assert isinstance(sub, CameraDataSubscriber)
        assert sub.port == 8105 and sub.address == "tcp://127.0.0.1:8105"
        assert sub.receive(timeout=0) is None


def test_camera_legacy_jpeg_codec(jpeg_message):
    jpeg_message.rgb_codec = 0
    frame = CameraDataSubscriber.decode(jpeg_message.SerializeToString())
    assert frame.rgb_codec_name == "jpeg" and frame.image.shape == (12, 18, 3)


def test_camera_saved_real_hevc_keyframe():
    pytest.importorskip("av")
    fixtures = Path(__file__).parent / "fixtures"
    config = json.loads((fixtures / "hevc_config.json").read_text())
    message = phone_msg_pb2.Phone(
        color_img=(fixtures / "hevc_frame.bin").read_bytes(), rgb_codec=2,
        rgb_width=64, rgb_height=64,
        rgb_codec_config=[bytes.fromhex(value) for value in config["parameter_sets"]],
        rgb_nal_unit_header_length=4)
    frame = CameraDataSubscriber.decode(message.SerializeToString())
    assert frame.image.shape == (64, 64, 3)
    assert frame.image[..., 0].mean() > 180 and frame.image[..., 1].mean() < 60


def test_camera_hevc_reference_continuity_and_decoded_conflation(publisher, hevc_sequence):
    socket, connect = publisher
    sub = connect(CameraDataSubscriber, conflate=True)
    messages, expected = hevc_sequence
    for message in messages:
        message.session_identifier = ""
        socket.send(message.SerializeToString())
    with sub._pump._condition:
        assert sub._pump._condition.wait_for(
            lambda: sub._pump._pending and sub._pump._pending[-1].frame_id == messages[7].frame_id,
            timeout=2)
        assert len(sub._pump._pending) == 1
    frame = sub.receive(timeout=2000)
    assert frame.frame_id == 8 and frame._decoded_video_frame is not None
    assert np.abs(frame.image.astype(float) - expected[7]).mean() < 10


def test_camera_hevc_resets_on_lens_restart_format_change_and_codec_change(publisher, hevc_sequence, jpeg_message):
    socket, connect = publisher
    sub = connect(CameraDataSubscriber)
    messages, expected = hevc_sequence

    def receive(index, **changes):
        message = phone_msg_pb2.Phone()
        message.CopyFrom(messages[index])
        message.session_identifier = ""
        for name, value in changes.items():
            setattr(message, name, value)
        socket.send(message.SerializeToString())
        return sub.receive(timeout=2000)

    assert receive(0).image is not None
    assert receive(1).image is not None
    # Fresh camera encoder restarts at frame 1, followed by its new reference chain.
    assert receive(0).image is not None
    assert receive(1).image is not None
    # A dimension change with a delta frame must wait for the next keyframe.
    assert receive(2, rgb_width=128).image is None
    assert receive(4).image is not None
    # JPEG interrupts any old HEVC reference chain.
    socket.send(jpeg_message.SerializeToString())
    assert sub.receive(timeout=2000).image is not None
    assert receive(5).image is None
    recovered = receive(0).image
    assert np.abs(recovered.astype(float) - expected[0]).mean() < 10


def test_camera_hevc_gap_and_saved_delta_wait_for_keyframe(publisher, hevc_sequence):
    socket, connect = publisher
    sub = connect(CameraDataSubscriber)
    messages, _ = hevc_sequence
    for index in (1, 4, 6, 0):
        messages[index].session_identifier = ""
        socket.send(messages[index].SerializeToString())
        frame = sub.receive(timeout=2000)
        assert (frame.image is None) == (index in (1, 6))
    with pytest.raises(ValueError, match="key frame"):
        _ = CameraDataSubscriber.decode(messages[1].SerializeToString()).image


def test_camera_decode_failure_and_recovery(publisher, jpeg_message):
    socket, connect = publisher
    sub = connect(CameraDataSubscriber)
    socket.send(b"\xff")
    with pytest.raises(RuntimeError, match="Failed to receive camera data"):
        sub.receive(timeout=2000)
    socket.send(jpeg_message.SerializeToString())
    assert sub.receive(timeout=2000).image is not None and sub.last_error is None


def test_camera_invalid_image_is_reported(publisher):
    socket, connect = publisher
    sub = connect(CameraDataSubscriber)
    socket.send(phone_msg_pb2.Phone(color_img=b"bad-image").SerializeToString())
    result = run_stream_check("camera", sub, duration=1, count=1)
    assert result.frames == 1 and result.status == "errors"
    assert any("rgb:" in error for error in result.errors)


def test_camera_close_wakes_receive_and_stops_decoder_thread(publisher):
    _, connect = publisher
    sub = connect(CameraDataSubscriber)
    result = []

    def receive():
        try:
            sub.receive()
        except StopIteration:
            result.append("closed")

    worker = threading.Thread(target=receive)
    worker.start()
    sub.close()
    worker.join(timeout=2)
    assert result == ["closed"] and not worker.is_alive()
    assert not sub._pump._thread.is_alive() and not sub.is_connected
    sub.close()
