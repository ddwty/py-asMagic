import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from google.protobuf.message import DecodeError

from asmagic import ARDataSubscriber, FaceAndHandTrackingDataSubscriber, FaceDataSubscriber, FaceFrame, HandPoseDataSubscriber, JoystickDataSubscriber

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def test_schema_snapshot_hashes_match_sources():
    metadata = json.loads((ROOT / "asmagic/proto/schema_sources.json").read_text())
    for name, source in metadata["files"].items():
        assert hashlib.sha256((ROOT / "asmagic/proto/schemas" / name).read_bytes()).hexdigest() == source["sha256"]


def test_python_38_syntax_compatibility():
    for directory in ["asmagic", "tools", "examples"]:
        for file in (ROOT / directory).rglob("*.py"):
            ast.parse(file.read_text(), filename=str(file), feature_version=8)


def test_unknown_fields_preserved_and_no_reused_optional_fields():
    from asmagic.proto import phone_msg_pb2
    payload = phone_msg_pb2.Phone(timestamp=5).SerializeToString() + b"\xa2\x06\x03new"
    frame = ARDataSubscriber.decode(payload)
    assert b"\xa2\x06\x03new" in frame.protobuf.SerializeToString()
    next_frame = ARDataSubscriber.decode(phone_msg_pb2.Phone().SerializeToString())
    assert next_frame.timestamp == 0 and not next_frame.color_img


def test_legacy_014_golden_packets():
    frame = ARDataSubscriber.decode((FIXTURES / "v014_phone.bin").read_bytes())
    assert frame.timestamp == 123.5 and frame.color_bytes == b"legacy-jpeg"
    assert frame.depth_width == 2 and frame.depth_height == 1
    np.testing.assert_equal(frame.depth, [[10000, 20000]])
    assert frame.frame_id == 0 and frame.rgb_codec_name == "jpeg"
    controller = JoystickDataSubscriber.decode((FIXTURES / "v014_joystick.bin").read_bytes())
    assert controller.left_x == .5 and controller.button1
    assert controller.triggers is None and controller.controller_name == ""


def test_swift_sender_face_packet():
    frame = FaceAndHandTrackingDataSubscriber.decode((FIXTURES / "swift_face_hand.bin").read_bytes())
    assert frame.source_timestamp == 100.125 and frame.session_id == "swift-session"
    assert len(frame.blendshapes) == 52 and frame.blendshapes["jawOpen"] == pytest.approx(.75)
    assert frame.has_face and frame.protobuf.image_rotation == 6
    assert frame.points.shape == (3, 2) and frame.face_vertices.shape == (3, 3)
    assert frame.hands.timestamp == 100.1
    assert frame.left_hand.joints["wrist"].confidence == pytest.approx(.9)


def test_same_hand_receiver_across_app_entries_and_tracking_loss(publisher):
    socket, connect = publisher
    sub = connect(HandPoseDataSubscriber)
    # Actual Swift sender/encoder outputs: Stream, loss of both hands, then
    # Face and Hand Tracking. The receiver and decoder stay the same.
    frames = []
    for name in ("swift_stream_hand.bin", "swift_empty_hand.bin", "swift_face_hand_only.bin"):
        socket.send((FIXTURES / name).read_bytes())
        frame = sub.get(timeout=2000)
        assert frame is not None
        assert frame.protobuf.DESCRIPTOR.full_name == "Phone.HandPoseFrame"
        frames.append(frame)
    stream, empty, face_hands = frames
    assert stream.protobuf == face_hands.protobuf
    for frame in (stream, face_hands):
        assert frame.source_timestamp == 42.2 and frame.hand_count == 2
        assert (frame.image_width, frame.image_height) == (640, 480)
        assert frame.protobuf.image_orientation == "portrait"
        assert frame.unknown_hand_count == 1
        assert frame.left_hand.joints.wrist.confidence == pytest.approx(.9)
        assert frame.right_hand.joints.index_tip.x == pytest.approx(.7)
        np.testing.assert_equal(stream.left_hand.as_arrays().points, frame.left_hand.as_arrays().points)
        np.testing.assert_equal(stream.right_hand.as_arrays().valid, frame.right_hand.as_arrays().valid)
    assert empty.source_timestamp == 42.3 and empty.hand_count == 0
    assert empty.left_hand is None and empty.right_hand is None


def test_swift_sender_controller_packet():
    frame = JoystickDataSubscriber.decode((FIXTURES / "swift_joystick.bin").read_bytes())
    assert frame.left_x == pytest.approx(-.5) and frame.controller_name == "Swift controller"
    assert frame.triggers.r2.value == pytest.approx(.8) and frame.motion.attitude.w == 1


def test_swift_sender_camera_packet():
    frame = ARDataSubscriber.decode((FIXTURES / "swift_phone.bin").read_bytes())
    assert frame.frame_id == 8 and frame.session_identifier == "swift-camera"
    assert frame.global_pose_is_shared and frame.shared_world_identifier == "shared-world"
    assert frame.depth_meters_per_unit == pytest.approx(.0001)
    np.testing.assert_array_equal(frame.depth, [[10000, 20000]])


def test_swift_face_only_output_and_tracking_loss(publisher):
    from asmagic.proto import face_tracking_pb2
    socket, connect = publisher
    sub = connect(FaceDataSubscriber)
    assert "hand_pose" not in face_tracking_pb2.FaceTrackingFrame.DESCRIPTOR.fields_by_name
    socket.send((FIXTURES / "swift_face_only.bin").read_bytes())
    frame = sub.get(timeout=2000)
    assert isinstance(frame, FaceFrame) and not hasattr(frame, "hands")
    assert frame.protobuf.DESCRIPTOR.full_name == "Phone.FaceTrackingFrame"
    assert frame.schema_version == 2 and frame.session_id == "independent-test"
    assert frame.has_face and frame.tracking_mode == "true_depth"
    assert frame.source_timestamp == 42.25 and frame.protobuf.image_rotation == 6
    assert len(frame.blendshapes) == 52 and frame.blendshapes["jawOpen"] == pytest.approx(.75)
    assert frame.points.shape == (1, 2) and frame.face_vertices.shape == (1, 3)
    legacy = FaceAndHandTrackingDataSubscriber.decode((FIXTURES / "swift_face_only.bin").read_bytes())
    assert legacy.hands is None
    socket.send((FIXTURES / "swift_no_face.bin").read_bytes())
    lost = sub.get(timeout=2000)
    assert not lost.has_face and not lost.blendshapes and not lost.landmarks
    assert frame.has_face and len(frame.blendshapes) == 52


def test_face_and_hand_receivers_are_independent():
    import zmq
    with zmq.Context() as context:
        with context.socket(zmq.XPUB) as face_pub, context.socket(zmq.XPUB) as hand_pub:
            face_pub.setsockopt(zmq.LINGER, 0)
            hand_pub.setsockopt(zmq.LINGER, 0)
            face_port = face_pub.bind_to_random_port("tcp://127.0.0.1")
            hand_port = hand_pub.bind_to_random_port("tcp://127.0.0.1")
            with FaceDataSubscriber("127.0.0.1", port=face_port) as faces, \
                    HandPoseDataSubscriber("127.0.0.1", port=hand_port) as hands:
                assert face_pub.poll(2000) and face_pub.recv()[0] == 1
                assert hand_pub.poll(2000) and hand_pub.recv()[0] == 1
                hand_pub.send((FIXTURES / "swift_face_hand_only.bin").read_bytes())
                assert hands.get(timeout=2000).hand_count == 2
                assert faces.get(timeout=0) is None
                face_pub.send((FIXTURES / "swift_face_only.bin").read_bytes())
                assert faces.get(timeout=2000).has_face
                assert hands.get(timeout=0) is None
                faces.close()
                hand_pub.send((FIXTURES / "swift_empty_hand.bin").read_bytes())
                assert hands.get(timeout=2000).hand_count == 0
