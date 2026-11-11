import inspect
import importlib
from pathlib import Path

import numpy as np
import pytest
from google.protobuf.message import DecodeError

import asmagic
from asmagic import (ARDataSubscriber, AirPodsDataSubscriber, IMUDataSubscriber, JoystickDataSubscriber,
                     HandPoseDataSubscriber, FaceAndHandTrackingDataSubscriber,
                     ARBodyDataSubscriber, ProtobufSubscriber, subscribe)
from asmagic.proto import (phone_msg_pb2, joystick_msg_pb2, imu_msg_pb2, hand_pose_pb2,
                           face_tracking_pb2, armpose_msg_pb2, airpods_msg_pb2,
                           body_pose_msg_pb2, claw_msg_pb2)


@pytest.mark.parametrize("name", list(asmagic.STREAMS))
def test_each_app_stream_over_real_tcp(publisher, name):
    socket, connect = publisher
    info = asmagic.STREAMS[name]
    sub = connect(info.subscriber)
    message = sub._message_type()
    if "timestamp" in message.DESCRIPTOR.fields_by_name:
        message.timestamp = 12.5
    elif "source_timestamp" in message.DESCRIPTOR.fields_by_name:
        message.source_timestamp = 12.5
    socket.send(message.SerializeToString())
    frame = sub.receive(timeout=2000)
    assert frame is not None
    assert frame.protobuf.SerializeToString() == message.SerializeToString()
    assert sub.has_received_data and sub.received_frames == 1
    assert sub.last_received_at is not None
    assert sub.receive(timeout=0) is None
    sub.close()
    sub.close()
    assert not sub.is_connected
    with pytest.raises(StopIteration):
        sub.receive(timeout=0)
    with pytest.raises(StopIteration):
        next(sub)


def test_original_methods_and_module_imports_still_exist():
    for module, name in [("arDataSubscriber", "ARDataSubscriber"),
                         ("imuDataSubscriber", "IMUDataSubscriber"),
                         ("joystickDataSubscriber", "JoystickDataSubscriber")]:
        cls = getattr(importlib.import_module("asmagic." + module), name)
        assert cls is getattr(asmagic, name)
        # Python 3.8 may prefer Generic.__new__ when inspecting the class itself.
        params = dict(inspect.signature(cls.__init__).parameters)
        params.pop("self")
        assert list(params) == ["ip", "port", "hwm", "conflate", "verbose"]
        assert params["hwm"].default == (32 if cls is ARDataSubscriber else 1)
        assert params["conflate"].default is (False if cls is ARDataSubscriber else True)
        assert inspect.signature(cls.receive).parameters["timeout"].default is None
        if cls is JoystickDataSubscriber:
            assert inspect.signature(cls.get).parameters["timeout"].default == 1000
    from asmagic.subscriber import ARDataSubscriber as original_ar, connect as original_connect
    assert original_ar is ARDataSubscriber and original_connect is asmagic.connect


def test_ar_received_fields_and_frame_independence(publisher):
    socket, connect = publisher
    sub = connect(ARDataSubscriber)
    message = phone_msg_pb2.Phone(timestamp=42, local_pose=[1, 2, 3, 0, 0, 0, 1])
    socket.send(message.SerializeToString())
    frame = sub.receive(timeout=2000)
    assert frame.timestamp == 42
    np.testing.assert_equal(frame.local_pose, [1, 2, 3, 0, 0, 0, 1])
    socket.send(message.SerializeToString())
    first = next(sub)
    socket.send(phone_msg_pb2.Phone(timestamp=43).SerializeToString())
    second = sub.receive(timeout=2000)
    assert first.local_pose.size == 7 and second.local_pose.size == 0
    assert first.protobuf.timestamp == 42


def test_stream_callback_and_frame_protobuf(publisher):
    socket, connect = publisher
    sub = connect(IMUDataSubscriber)
    message = imu_msg_pb2.Imu(timestamp=33)
    message.gyroscope.z = 1.5
    socket.send(message.SerializeToString())
    called = []
    frame = next(sub.stream(timeout=2000, on_frame=called.append))
    assert called == [frame]
    socket.send(message.SerializeToString())
    assert sub.receive(timeout=2000).protobuf.gyroscope.z == 1.5


def test_decode_error_and_recovery(publisher):
    socket, connect = publisher
    sub = connect(IMUDataSubscriber)
    socket.send(b"\xff")
    assert sub.receive(timeout=50) is None
    assert sub.last_error and sub.received_frames == 0
    socket.send(imu_msg_pb2.Imu(timestamp=10).SerializeToString())
    assert sub.receive(timeout=2000).timestamp == 10 and sub.last_error is None


def test_ar_preserves_legacy_decode_error(publisher):
    socket, connect = publisher
    sub = connect(ARDataSubscriber)
    socket.send(b"\xff")
    with pytest.raises(RuntimeError, match="Failed to receive AR data"):
        sub.receive(timeout=2000)


@pytest.mark.parametrize("rotation", [[], [.1, .2, .3, .9]])
def test_airpods_rotation_without_alias(rotation):
    message = airpods_msg_pb2.Airpods(timestamp=12.5, rotation=rotation)
    frame = AirPodsDataSubscriber.decode(message.SerializeToString())
    assert frame.timestamp == 12.5
    assert frame.rotation.dtype == np.float32
    np.testing.assert_array_equal(frame.rotation, np.array(rotation, dtype=np.float32))
    assert frame.protobuf.SerializeToString() == message.SerializeToString()
    with pytest.raises(AttributeError):
        _ = frame.attitude


def test_presence_and_legacy_imu_attitude():
    message = imu_msg_pb2.Imu(timestamp=9)
    message.accelerometer.SetInParent()  # measured zero is different from missing
    frame = IMUDataSubscriber.decode(message.SerializeToString())
    assert frame.has_accelerometer
    np.testing.assert_array_equal(frame.accelerometer, [0, 0, 0])
    assert not frame.has_gyroscope and not frame.has_attitude
    message.attitude.w = 1
    assert IMUDataSubscriber.decode(message.SerializeToString()).has_attitude


def test_full_controller_and_legacy_axes():
    message = joystick_msg_pb2.Joystick(timestamp=4, controller_name="DualSense", is_connected=True,
                                        l_joystick_position=[-.7, .2], r_joystick_position=[0, -1],
                                        button_pressed=[True, False, False, True])
    message.triggers.l2.value = .75
    message.triggers.r2.pressed = True
    message.dpad.axis.x = -1
    message.motion.sensors_active = True
    message.motion.attitude.w = 1
    frame = JoystickDataSubscriber.decode(message.SerializeToString())
    assert frame.left_x == pytest.approx(-.7)
    assert frame.right_y == -1 and frame.button1 and frame.button4
    assert frame.triggers.l2.value == .75 and frame.triggers.r2.pressed
    assert frame.dpad.axis.x == -1 and frame.motion.attitude.w == 1
    assert frame.controller_name == "DualSense" and frame.is_connected
    old = joystick_msg_pb2.Joystick(l_joystick_position=[.5, .8])
    frame = JoystickDataSubscriber.decode(old.SerializeToString())
    assert frame.left_x == .5 and frame.triggers is None
    new_only = joystick_msg_pb2.Joystick()
    new_only.left_stick.x = -.25
    new_only.face_buttons.cross = True
    frame = JoystickDataSubscriber.decode(new_only.SerializeToString())
    assert frame.left_x == -.25 and frame.button3


def test_face_mesh_blendshapes_presence_and_async_hands():
    message = face_tracking_pb2.FaceAndHandTrackingFrame(
        source_timestamp=20, has_face=True, image_width=640, image_height=480,
        tracking_mode=face_tracking_pb2.FACE_TRACKING_MODE_TRUE_DEPTH,
        sequence_number=7, session_id="session-a", schema_version=1, image_rotation=6)
    names = __import__("json").loads((Path(__file__).parent / "fixtures/blendshape_names.json").read_text())
    for index, name in enumerate(names):
        message.blendshape_coefficients.add(name=name, value=index/51)
    for index in range(3):
        point = message.landmarks.add(index=index, region="mesh", image_x=.2*index, image_y=.4)
        point.position_face_meters.x = index*.01
    message.triangle_indices.extend([0, 1, 2])
    message.hand_pose.source_timestamp = 19.95
    message.hand_pose.left_hand.confidence = .9
    message.hand_pose.left_hand.joints.add(name="wrist", x=.2, y=.8, confidence=.95)
    frame = FaceAndHandTrackingDataSubscriber.decode(message.SerializeToString())
    assert len(frame.blendshapes) == 52 and frame.blendshapes["tongueOut"] == 1
    assert frame.points.shape == (3, 2) and frame.face_vertices.shape == (3, 3)
    np.testing.assert_equal(frame.triangles, [[0, 1, 2]])
    assert frame.hands.timestamp == 19.95 and frame.timestamp == 20
    assert frame.left_hand.joints["wrist"].x == pytest.approx(.2)
    assert frame.right_hand is None and frame.camera_position_meters is None
    assert frame.tracking_mode == "true_depth"
    absent = FaceAndHandTrackingDataSubscriber.decode(face_tracking_pb2.FaceAndHandTrackingFrame().SerializeToString())
    assert absent.hands is None and absent.points.shape == (0, 2) and not absent.blendshapes
    assert absent.face_vertices is None


def test_standalone_hand_presence_and_unknown_count():
    message = hand_pose_pb2.HandPoseFrame(source_timestamp=3, unknown_hand_count=1)
    message.right_hand.SetInParent()
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    assert frame.has_right_hand and not frame.has_left_hand
    assert frame.hand_count == 1 and frame.unknown_hand_count == 1


def test_body_model_local_and_world_transforms():
    message = armpose_msg_pb2.Armpose(timestamp=100, source_timestamp=2, session_id="origin-1", tracking_state="tracking")
    message.body_transform.rotation.w = 1
    message.body_transform.position.x = 10
    message.joints["left_hand_joint"].position.x = 2
    message.joints["left_hand_joint"].rotation.w = 1
    message.local_joints["left_hand_joint"].rotation.w = 1
    message.tracked_joints["left_hand_joint"] = False
    message.joint_parents["left_hand_joint"] = "left_forearm_joint"
    frame = ARBodyDataSubscriber.decode(message.SerializeToString())
    assert frame.joints["left_hand_joint"].position[0] == 2
    assert frame.joint_world_matrix("left_hand_joint")[0, 3] == 12
    assert not frame.tracked_joints["left_hand_joint"]
    assert frame.joint_parents["left_hand_joint"] == "left_forearm_joint"
    assert frame.is_tracking and frame.session_id == "origin-1"
    lost = ARBodyDataSubscriber.decode(armpose_msg_pb2.Armpose(tracking_state="searching").SerializeToString())
    assert not lost.is_tracking and not lost.joints and lost.body_transform is None


def test_custom_proto_subscriber(publisher):
    socket, connect = publisher
    sub = connect(ProtobufSubscriber, message_type=claw_msg_pb2.Claw)
    socket.send(claw_msg_pb2.Claw(angle=45).SerializeToString())
    assert sub.get(2000).angle == 45


def test_address_and_invalid_configuration():
    from asmagic._subscriber import tcp_address
    assert tcp_address("fe80::1%en0", 8102) == "tcp://[fe80::1%en0]:8102"
    assert tcp_address("[::1]", 8102) == "tcp://[::1]:8102"
    with pytest.raises(ValueError):
        ARDataSubscriber("", port=8000)
    with pytest.raises(ValueError):
        ARDataSubscriber("127.0.0.1", hwm=0)
    with pytest.raises(ValueError):
        tcp_address("127.0.0.1", 70000)
    with pytest.raises(ValueError):
        subscribe("missing", "127.0.0.1")
