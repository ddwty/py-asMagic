import io
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from asmagic import ARDataSubscriber, ARFrame
from asmagic._images import nal_units
from asmagic.proto import phone_msg_pb2


@pytest.mark.parametrize("rotation", [0, 1, 2, 3])
def test_jpeg_rgb_decode_and_legacy_codec(rotation):
    buffer = io.BytesIO()
    Image.new("RGB", (3, 2), (230, 20, 10)).save(buffer, format="JPEG", quality=100)
    frame = ARDataSubscriber.decode(phone_msg_pb2.Phone(
        color_img=buffer.getvalue(), image_rotation_quarter_turns_clockwise=rotation).SerializeToString())
    assert frame.rgb_codec_name == "jpeg"
    assert frame.color_array.shape == (2, 3, 3)
    assert frame.color is frame.color_array
    assert frame.protobuf.image_rotation_quarter_turns_clockwise == rotation
    assert frame.image_rotation_quarter_turns_clockwise == rotation
    np.testing.assert_equal(frame.color_upright, np.rot90(frame.color_array, -rotation))
    assert frame.color_bytes == buffer.getvalue()
    replacement = io.BytesIO()
    Image.new("RGB", (2, 4), (20, 230, 10)).save(replacement, format="JPEG")
    frame.color_img = replacement.getvalue()
    assert frame.color_array.shape == (4, 2, 3)


def test_depth_units_confidence_and_raw_image_layout():
    data = np.array([[0, 10000, 20000], [30000, 40000, 50000]], dtype="<u2")
    frame = ARDataSubscriber.decode(phone_msg_pb2.Phone(
        depth_img=data.tobytes(), depth_width=3, depth_height=2,
        depth_confidence=bytes([0, 1, 2, 2, 1, 0]),
        image_rotation_quarter_turns_clockwise=1).SerializeToString())
    np.testing.assert_equal(frame.depth, data)
    np.testing.assert_equal(frame.depth_upright, np.rot90(data, -1))
    np.testing.assert_equal(frame.depth_array, data)
    assert frame.depth.dtype == np.uint16
    np.testing.assert_equal(frame.depth_confidence_array, [[0, 1, 2], [2, 1, 0]])
    frame.depth_meters_per_unit = .001
    np.testing.assert_equal(frame.depth, data)
    frame.depth_img = b"short"
    with pytest.raises(ValueError, match="Depth byte count"):
        _ = frame.depth
    frame.depth_confidence = b"x"
    with pytest.raises(ValueError, match="confidence byte count"):
        _ = frame.depth_confidence_array


def test_quaternion_pose_and_intrinsics_layout():
    frame = ARFrame(local_pose=np.array([1, 2, 3, 0, 0, np.sqrt(.5), np.sqrt(.5)]),
                    camera_intrinsics=np.array([100, 0, 0, 0, 200, 0, 20, 30, 1]))
    np.testing.assert_allclose(frame.local_pose_matrix,
                               [[0, -1, 0, 1], [1, 0, 0, 2], [0, 0, 1, 3], [0, 0, 0, 1]], atol=1e-6)
    np.testing.assert_equal(frame.camera_intrinsics_matrix, [[100, 0, 20], [0, 200, 30], [0, 0, 1]])
    frame.local_pose = np.arange(16)
    np.testing.assert_equal(frame.local_pose_matrix, np.arange(16).reshape(4, 4))


def test_hevc_length_prefix_validation():
    assert list(nal_units(b"\x00\x00\x00\x02ab", 4)) == [b"ab"]
    for payload, length in [(b"\x00", 4), (b"\x00\x03ab", 2), (b"\x00", 3)]:
        with pytest.raises(ValueError):
            list(nal_units(payload, length))


@pytest.mark.parametrize("named_flags_available", [True, False])
def test_hevc_independent_frame_decode(monkeypatch, named_flags_available):
    av = pytest.importorskip("av")
    if not named_flags_available:
        monkeypatch.setattr(av.codec.context, "Flags", None)
    import json
    fixture = Path(__file__).parent / "fixtures"
    config = json.loads((fixture / "hevc_config.json").read_text())
    frame = ARFrame(color_img=(fixture / "hevc_frame.bin").read_bytes(), rgb_codec=2,
                    rgb_codec_config=tuple(bytes.fromhex(value) for value in config["parameter_sets"]),
                    rgb_nal_unit_header_length=4)
    image = frame.color_array
    assert image.shape == (64, 64, 3)
    assert image[..., 0].mean() > 180 and image[..., 1].mean() < 60
    assert frame.rgb_codec_name == "hevc"


def test_unsupported_codec_is_not_treated_as_jpeg():
    with pytest.raises(ValueError, match="Unsupported RGB codec"):
        _ = ARFrame(color_img=b"not-jpeg", rgb_codec=99).color_array


@pytest.fixture
def hevc_sequence():
    """Real I/P packets with moving pixels; the old per-frame decoder loses references."""
    av = pytest.importorskip("av")
    import re
    from asmagic.proto import phone_msg_pb2
    encoder = av.CodecContext.create("libx265", "w")
    encoder.width = encoder.height = 64
    encoder.pix_fmt = "yuv420p"
    from fractions import Fraction
    encoder.time_base = Fraction(1, 30)
    encoder.thread_count = 1
    encoder.options = {"preset": "ultrafast", "tune": "zerolatency",
                       "x265-params": "keyint=4:min-keyint=4:scenecut=0:bframes=0:repeat-headers=1:pools=none:frame-threads=1:log-level=error"}
    packets, expected = [], []
    y, x = np.indices((64, 64))
    for index in range(8):
        image = np.stack([180 + (x + index * 4) % 60, 20 + y % 30,
                          10 + (x + y + index * 2) % 30], axis=-1).astype(np.uint8)
        expected.append(image)
        video_frame = av.VideoFrame.from_ndarray(image, format="rgb24")
        video_frame.pts = index
        packets.extend(encoder.encode(video_frame))
    packets.extend(encoder.encode(None))
    assert len(packets) == 8
    messages, config = [], []
    for index, packet in enumerate(packets):
        units = [unit for unit in re.split(b"\x00\x00(?:\x00)?\x01", bytes(packet)) if unit]
        parameter_sets = [unit for unit in units if (unit[0] >> 1) & 0x3f in (32, 33, 34)]
        if parameter_sets:
            config = parameter_sets
        picture = [unit for unit in units if (unit[0] >> 1) & 0x3f not in (32, 33, 34)]
        messages.append(phone_msg_pb2.Phone(
            frame_id=index + 1, session_identifier="synthetic-video", rgb_width=64, rgb_height=64,
            rgb_codec=2, rgb_codec_config=config, rgb_is_key_frame=packet.is_keyframe,
            rgb_nal_unit_header_length=4,
            color_img=b"".join(len(unit).to_bytes(4, "big") + unit for unit in picture)))
    assert messages[0].rgb_is_key_frame and not messages[1].rgb_is_key_frame
    assert messages[4].rgb_is_key_frame
    return messages, expected


def test_received_hevc_keeps_references_without_displaying_each_frame(publisher, hevc_sequence):
    socket, connect = publisher
    sub = connect(ARDataSubscriber)
    messages, expected = hevc_sequence
    received = []
    for message in messages:
        socket.send(message.SerializeToString())
        received.append(sub.receive(timeout=2000))  # Deliberately don't access color yet.
    sub.close()  # Retained video pictures still belong to their individual ARFrame.
    for frame, image in zip(received, expected):
        assert frame.color_array is not None
        assert np.abs(frame.color_array.astype(float) - image).mean() < 10
        assert frame.color is frame.color_array


def test_received_hevc_waits_for_keyframe_after_join_gap_and_new_session(publisher, hevc_sequence):
    socket, connect = publisher
    sub = connect(ARDataSubscriber)
    messages, expected = hevc_sequence

    def receive(index, session=None):
        message = type(messages[index])()
        message.CopyFrom(messages[index])
        if session is not None:
            message.session_identifier = session
        socket.send(message.SerializeToString())
        return sub.receive(timeout=2000)

    joined = receive(1)
    assert joined.color_array is None  # Join mid-GOP.
    from asmagic.diagnostics import inspect_frame
    inspection = inspect_frame("ar", joined, decode_images=True)
    assert inspection.components["rgb_decoded"] is False
    assert inspection.values["rgb_waiting_for_key_frame"] is True
    assert not inspection.errors
    assert receive(4).color_array is not None
    assert receive(6).color_array is None  # Packet 5 was lost.
    assert receive(0).color_array is not None  # Restart at a key frame.
    assert receive(1, "new-session").color_array is None
    recovered = receive(4, "new-session").color_array
    assert np.abs(recovered.astype(float) - expected[4]).mean() < 10


def test_hevc_subscribers_do_not_share_decoder_state(publisher, hevc_sequence):
    socket, connect = publisher
    first = connect(ARDataSubscriber)
    messages, _ = hevc_sequence
    socket.send(messages[0].SerializeToString())
    assert first.receive(timeout=2000).color_array is not None
    second = connect(ARDataSubscriber)
    socket.send(messages[1].SerializeToString())
    assert first.receive(timeout=2000).color_array is not None
    assert second.receive(timeout=2000).color_array is None


def test_saved_hevc_delta_requires_stream_context(hevc_sequence):
    messages, _ = hevc_sequence
    frame = ARDataSubscriber.decode(messages[1].SerializeToString())
    with pytest.raises(ValueError, match="key frame"):
        _ = frame.color_array


def test_slow_display_only_replaces_decoded_hevc_frames(publisher, hevc_sequence):
    socket, connect = publisher
    sub = connect(ARDataSubscriber, conflate=True)
    messages, expected = hevc_sequence
    for index in range(4):
        socket.send(messages[index].SerializeToString())
    # Simulate a blocked GUI while the worker consumes I/P packets.
    with sub._pump._condition:
        assert sub._pump._condition.wait_for(
            lambda: sub._pump._pending and sub._pump._pending[-1].frame_id == messages[3].frame_id,
            timeout=2)
        assert len(sub._pump._pending) == 1
    frame = sub.receive(timeout=2000)
    assert frame.frame_id == messages[3].frame_id
    assert frame._decoded_color is None  # No RGB conversion on the receive thread.
    assert frame._decoded_video_frame is not None
    assert np.abs(frame.color_array.astype(float) - expected[3]).mean() < 10
    assert frame._decoded_video_frame is None
    for index in range(4, 8):
        socket.send(messages[index].SerializeToString())
    with sub._pump._condition:
        assert sub._pump._condition.wait_for(
            lambda: sub._pump._pending and sub._pump._pending[-1].frame_id == messages[7].frame_id,
            timeout=2)
    latest = sub.receive(timeout=2000)
    assert latest.frame_id == messages[7].frame_id
    assert np.abs(latest.color_array.astype(float) - expected[7]).mean() < 10


def test_ar_close_wakes_waiting_receive_and_stops_socket_thread(publisher):
    import threading
    _, connect = publisher
    sub = connect(ARDataSubscriber)
    returned = []
    def receive():
        try:
            returned.append(sub.receive())
        except StopIteration:
            returned.append("closed")

    waiting = threading.Thread(target=receive)
    waiting.start()
    sub.close()
    waiting.join(timeout=2)
    assert not waiting.is_alive() and returned == ["closed"]
    assert not sub._pump._thread.is_alive()
    assert not sub.is_connected
