"""AR/IMU field values stay intact with receive() and attribute access."""
import numpy as np
import pytest

from asmagic import ARDataSubscriber, ARFrame, IMUDataSubscriber, IMUFrame
from asmagic.diagnostics import inspect_frame
from asmagic.proto import imu_msg_pb2, phone_msg_pb2


@pytest.mark.parametrize("receiver", [ARDataSubscriber, IMUDataSubscriber])
def test_ar_imu_expose_receive_and_frame_properties_without_getters(publisher, receiver):
    socket, connect = publisher
    sub = connect(receiver)
    message = sub._message_type(timestamp=42)
    socket.send(message.SerializeToString())
    frame = sub.receive(timeout=2000)
    assert frame.timestamp == 42
    assert not any(name == "get" or name.startswith("get_") for name in dir(sub))
    assert not any(name == "get" or name.startswith("get_") for name in dir(frame))
    assert sub.receive(timeout=0) is None


def test_original_ar_arrays_keep_their_values():
    message = phone_msg_pb2.Phone(timestamp=42, color_img=b"encoded", depth_img=b"\x01\x00\x02\x00",
                                  depth_width=2, depth_height=1, local_pose=[1, 2, 3, 0, 0, 0, 1],
                                  global_pose=list(range(16)), velocity=[4, 5, 6],
                                  camersIntrinsics=[100, 0, 0, 0, 200, 0, 20, 30, 1])
    frame = ARDataSubscriber.decode(message.SerializeToString())
    assert frame.timestamp == 42 and frame.color_bytes == frame.color_img == b"encoded"
    assert frame.depth_img == message.depth_img and (frame.depth_width, frame.depth_height) == (2, 1)
    for name, expected in [("local_pose", message.local_pose), ("global_pose", message.global_pose),
                           ("velocity", message.velocity), ("camera_intrinsics", message.camersIntrinsics)]:
        np.testing.assert_array_equal(getattr(frame, name), expected)
    np.testing.assert_array_equal(frame.depth_array, [[1, 2]])
    np.testing.assert_array_equal(frame.depth, [[1, 2]])
    assert ARFrame().depth_array is None


@pytest.mark.parametrize("pose", [[1, 2, 3, 0, 0, 0, 1], list(range(16)), []])
def test_matrix_properties_preserve_raw_arrays(pose):
    raw = np.array(pose, dtype=np.float32)
    intrinsics = np.array([100, 0, 0, 0, 200, 0, 20, 30, 1], dtype=np.float32)
    frame = ARFrame(local_pose=raw.copy(), global_pose=raw.copy(), camera_intrinsics=intrinsics.copy())
    for name in ("local_pose", "global_pose"):
        matrix = getattr(frame, name + "_matrix")
        if pose:
            if len(pose) == 16:
                expected = raw.reshape(4, 4)
            else:
                expected = np.eye(4, dtype=np.float32)
                expected[:3, 3] = raw[:3]
            np.testing.assert_array_equal(matrix, expected)
            assert matrix.shape == (4, 4)
        else:
            assert matrix is None
        np.testing.assert_array_equal(getattr(frame, name), raw)
    np.testing.assert_array_equal(frame.camera_intrinsics_matrix, [[100, 0, 20], [0, 200, 30], [0, 0, 1]])
    np.testing.assert_array_equal(frame.camera_intrinsics, intrinsics)
    assert ARFrame().camera_intrinsics_matrix is None


@pytest.mark.parametrize("name,size", [("accelerometer", 3), ("gyroscope", 3), ("magnetometer", 3),
                                       ("gravity", 3), ("user_acceleration", 3), ("attitude", 4)])
def test_imu_keeps_original_shapes_without_reporting_missing_sensors_as_measurements(name, size):
    message = imu_msg_pb2.Imu(timestamp=9)
    missing = IMUDataSubscriber.decode(message.SerializeToString())
    values = getattr(missing, name)
    assert values.shape == (size,) and values.dtype == np.float32
    np.testing.assert_array_equal(values, np.zeros(size))
    assert not getattr(missing, "has_" + name)
    assert not inspect_frame("imu", missing).usable

    sensor = getattr(message, name)
    sensor.SetInParent()  # A received all-zero reading is still present.
    present_zero = IMUDataSubscriber.decode(message.SerializeToString())
    assert getattr(present_zero, "has_" + name)
    assert inspect_frame("imu", present_zero).components[name]

    expected = list(range(1, size + 1))
    for axis, value in zip(("x", "y", "z", "w"), expected):
        setattr(sensor, axis, value)
    present = IMUDataSubscriber.decode(message.SerializeToString())
    assert present.timestamp == 9
    np.testing.assert_array_equal(getattr(present, name), expected)
    assert getattr(present, "has_" + name)

    # Manually constructed frames retain their original length-based flags.
    manual = IMUFrame(**{name: np.array(expected)})
    assert getattr(manual, "has_" + name)
    assert not getattr(IMUFrame(), "has_" + name)
