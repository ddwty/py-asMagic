"""Every public stream decoder receives over the same framed USB session."""
import io

import numpy as np
from PIL import Image
import pytest

import asmagic
from asmagic.proto import (armpose_msg_pb2, multi_person_pose_pb2,
                           phone_msg_pb2, watch_batch_msg_pb2)
from test_usb import mux


@pytest.mark.parametrize("name", list(asmagic.STREAMS) + ["face_hand", "body-arkit", "body-mediapipe", "claw2"])
def test_all_typed_streams_receive_and_preserve_data_over_usb(mux, name):
    _, received = mux
    if name.startswith("body-"):
        sub = asmagic.subscribe("body", transport="usb", model=name[5:])
    else:
        sub = asmagic.subscribe("claw" if name == "claw2" else name, transport="usb",
                               **({"port": 5401} if name == "claw2" else {}))
    with sub:
        message_type = sub._message_type
        message = message_type()
        fields = message.DESCRIPTOR.fields_by_name
        if "timestamp" in fields:
            message.timestamp = 47.25
        elif "source_timestamp" in fields:
            message.source_timestamp = 47.25
        else:
            message.frame_id = 91
        if name == "body-arkit":
            message.tracking_state = "searching"
        elif name == "body-mediapipe":
            message.schema_version, message.model = 1, "mediapipe.pose"
            message.session_id, message.world_frame_id = "session", "world"
            message.camera_tracking = "normal"
            message.camera_world_transform.extend(np.eye(4).flatten())
            message.camera_intrinsics.extend(np.eye(3).flatten())
            message.image_width, message.image_height = 640, 480
        if name in ("camera", "ar"):
            pixels = np.full((8, 12, 3), [210, 40, 25], dtype=np.uint8)
            image = io.BytesIO()
            Image.fromarray(pixels).save(image, format="JPEG")
            message.color_img = image.getvalue()
            message.rgb_width, message.rgb_height, message.rgb_codec = 12, 8, 1
            if name == "ar":
                message.depth_img = np.arange(6, dtype=np.uint16).tobytes()
                message.depth_width, message.depth_height = 3, 2
                message.depth_meters_per_unit = .0001
                message.local_pose.extend(np.eye(4).flatten())
        received.stream_payloads = {"iphone.stream.{}".format(sub.port): message.SerializeToString()}
        frame = sub.receive(timeout=3000)
        assert frame is not None and frame.protobuf == message
        if name in ("camera", "ar"):
            assert frame.color_array.shape == (8, 12, 3)
            assert frame.color_array[0, 0, 0] > 190
        if name == "ar":
            assert frame.depth.shape == (2, 3)
            np.testing.assert_array_equal(frame.depth.flat, np.arange(6))


def test_watch_usb_batch_is_distinct_from_iphone_imu_on_same_logical_port(mux):
    _, received = mux
    message = watch_batch_msg_pb2.WatchBatch(batch_timestamp=61, frame_count=2)
    for stamp in (60.5, 60.75):
        message.frames.add(timestamp=stamp, attitude=[0, 0, 0, 1], gravity=[0, 0, -1])
    received.stream_payloads["iphone.watch.8002"] = message.SerializeToString()
    with asmagic.WatchIMUReceiver("usb") as watch, asmagic.IMUDataSubscriber("usb") as imu:
        batch = watch.receive(timeout=3000)
        assert batch.frame_count == 2
        assert [frame.timestamp for frame in batch.frames] == [60.5, 60.75]
        assert imu.receive(timeout=3000).timestamp == 33
        assert watch.address == "usb://auto/watch/8002"


def test_raw_protobuf_subscriber_uses_usb_for_explicit_extra_ports(mux):
    _, received = mux
    message = phone_msg_pb2.Phone(timestamp=81, frame_id=91)
    received.stream_payloads = {"iphone.stream.8107": message.SerializeToString()}
    with asmagic.ProtobufSubscriber("usb", 8107, phone_msg_pb2.Phone) as sub:
        assert sub.receive(timeout=3000) == message
