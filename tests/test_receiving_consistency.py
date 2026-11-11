"""Shared consumer contract and runnable documentation lifetime checks."""
import importlib.util
import runpy
from pathlib import Path

import pytest
import asmagic
from asmagic import WatchIMUReceiver
from asmagic.proto import watch_batch_msg_pb2

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", list(asmagic.STREAMS))
def test_all_channels_consume_one_message_per_read_method(publisher, name):
    socket, connect = publisher
    sub = connect(asmagic.STREAMS[name].subscriber)
    message = sub._message_type()
    timestamp_message = message.upper_body if name == "body_pose" else message
    timestamp_field = "timestamp" if "timestamp" in timestamp_message.DESCRIPTOR.fields_by_name else "source_timestamp"
    called = []
    try:
        assert sub.receive(timeout=0) is None
        assert sub.receive(timeout=10) is None
        methods = ("stream", "receive", "receive_timed")
        if name not in ("ar", "imu", "camera"):
            methods = ("get", "get_frame") + methods
        for timestamp, method in enumerate(methods, 1):
            setattr(timestamp_message, timestamp_field, timestamp)
            socket.send(message.SerializeToString())
            if method == "stream":
                frames = sub.stream(timeout=2000, on_frame=called.append, plot=False)
                try:
                    frame = next(frames)
                    assert called == [frame] and frame.timestamp == timestamp
                finally:
                    frames.close()
            elif method == "receive":
                assert sub.receive().timestamp == timestamp
            elif method == "receive_timed":
                assert sub.receive(timeout=2000).timestamp == timestamp
            else:
                assert getattr(sub, method)(timeout=2000).timestamp == timestamp
            assert sub.receive(timeout=0) is None  # Each method consumed its own message.
    finally:
        sub.close()
    if name not in ("ar", "imu", "camera"):
        assert sub.get() is None
    with pytest.raises(StopIteration):
        sub.receive()
    for timeout in (0, 50, -1):
        with pytest.raises(StopIteration):
            sub.receive(timeout=timeout)


def test_watch_has_same_read_methods_and_stream_options():
    receiver = WatchIMUReceiver(port=0)
    called = []
    try:
        assert receiver.receive(timeout=0) is None
        assert receiver.receive(timeout=10) is None
        for timestamp, method in enumerate(("get", "get_frame", "stream", "receive", "receive_timed"), 1):
            message = watch_batch_msg_pb2.WatchBatch(batch_timestamp=timestamp, frame_count=1)
            message.frames.add(timestamp=timestamp, gravity=[0, 0, -1])
            receiver._enqueue(receiver.decode(message.SerializeToString()))
            if method == "stream":
                batches = receiver.stream(timeout=0, on_frame=called.append, plot=False, plot_options={})
                try:
                    batch = next(batches)
                    assert called == [batch] and batch.timestamp == timestamp
                finally:
                    batches.close()
            elif method == "receive":
                assert receiver.receive().timestamp == timestamp
            elif method == "receive_timed":
                assert receiver.receive(timeout=0).timestamp == timestamp
            else:
                assert getattr(receiver, method)(timeout=0).timestamp == timestamp
            assert receiver.get(timeout=0) is None
        with pytest.raises(ValueError, match="plot=True"):
            next(receiver.stream(plot=True))
    finally:
        receiver.close()
    with pytest.raises(StopIteration):
        receiver.receive()
    for timeout in (0, 50, -1):
        with pytest.raises(StopIteration):
            receiver.receive(timeout=timeout)


@pytest.mark.parametrize("cls", [asmagic.ARDataSubscriber, asmagic.IMUDataSubscriber, WatchIMUReceiver])
@pytest.mark.parametrize("timeout", [True, -2, 1.5])
def test_invalid_timeout_is_rejected_even_after_close(cls, timeout):
    receiver = cls(port=0) if cls is WatchIMUReceiver else cls("127.0.0.1")
    receiver.close()
    if cls is WatchIMUReceiver:
        with pytest.raises(ValueError, match="milliseconds"):
            receiver.get(timeout)
    with pytest.raises(ValueError, match="milliseconds"):
        receiver.receive(timeout=timeout)
    with pytest.raises(ValueError, match="milliseconds"):
        next(receiver.stream(timeout))


PRIMARY_EXAMPLES = {
    "ar/01_continuous.py": "ARDataSubscriber",
    "imu/01_all_sensors.py": "IMUDataSubscriber",
    "joystick/01_sticks_and_buttons.py": "JoystickDataSubscriber",
    "joystick/02_full_controller.py": "JoystickDataSubscriber",
    "joystick/03_named_controls.py": "JoystickDataSubscriber",
    "airpods/01_rotation.py": "AirPodsDataSubscriber",
    "body/01_all_joints.py": "BodyTrackingDataSubscriber",
    "upper_body/01_relative_joints.py": "BodyPoseDataSubscriber",
    "hand/01_both_hands.py": "HandPoseDataSubscriber",
    "face/01_face.py": "FaceDataSubscriber",
    "claw/01_first_gripper.py": "ClawDataSubscriber",
    "claw/02_second_gripper.py": "ClawDataSubscriber",
    "body/04_optional_skeleton.py": "BodyTrackingDataSubscriber",
    "body/02_named_joints.py": "BodyTrackingDataSubscriber",
    "body/03_coordinate_spaces.py": "BodyTrackingDataSubscriber",
    "body/05_person_id.py": "BodyTrackingDataSubscriber",
    "body/06_image_landmarks.py": "BodyTrackingDataSubscriber",
    "upper_body/02_optional_skeleton.py": "BodyPoseDataSubscriber",
    "hand/03_optional_skeleton.py": "HandPoseDataSubscriber",
    "face/05_optional_plot.py": "FaceDataSubscriber",
    "watch/01_batches.py": "WatchIMUReceiver",
    "watch/02_individual_samples.py": "WatchIMUReceiver",
}


@pytest.mark.parametrize("file,cls_name", PRIMARY_EXAMPLES.items())
@pytest.mark.parametrize("failure", [KeyboardInterrupt, RuntimeError])
def test_public_examples_skip_timeout_and_close_on_interrupt_or_failure(monkeypatch, file, cls_name, failure):
    cls = getattr(asmagic, cls_name)
    if cls is WatchIMUReceiver:
        message = watch_batch_msg_pb2.WatchBatch(frame_count=1)
        message.frames.add(timestamp=1, gravity=[0, 0, -1])
        from asmagic.decoders import watch_batch
        frame = watch_batch(message)
    elif cls is asmagic.BodyTrackingDataSubscriber:
        frame = asmagic.BodyTrackingFrame.from_bytes((ROOT / "tests/fixtures/swift_body_people.bin").read_bytes(), model="mediapipe")
    else:
        frame = cls.decode(cls._message_type().SerializeToString())
    instances = []

    class Receiver:
        address = "test://receiver"
        host = ip = "127.0.0.1"
        port = 8002
        payload_format = "batch"
        received_frames = 1
        dropped_batches = 0
        last_received_at = 1
        last_error = None
        is_connected = has_received_data = True
        _connected = True

        def __init__(self, *args, **kwargs):
            self.calls = self.closed = 0
            instances.append(self)

        def _read_frame(self, timeout=1000):
            self.calls += 1
            if self.calls == 1:
                return None
            if self.calls == 2:
                return frame
            raise failure("stop")

        def receive(self, timeout=None):
            from asmagic._subscriber import Receiver as BaseReceiver
            return BaseReceiver.receive(self, timeout=timeout)

        def stream(self, **options):
            from asmagic._subscriber import Receiver as BaseReceiver
            return BaseReceiver.stream(self, **options)

        def close(self):
            self.closed += 1

    monkeypatch.setattr(asmagic, cls_name, Receiver)

    def run_example():
        namespace = runpy.run_path(str(ROOT / "examples/documentation" / file))
        if "main" in namespace:
            namespace["main"].__globals__["SHOW_SKELETON"] = False
            namespace["main"]()

    if failure is RuntimeError:
        with pytest.raises(RuntimeError, match="stop"):
            run_example()
    else:
        run_example()
    assert len(instances) == 1 and instances[0].calls == 3 and instances[0].closed == 1


def test_documentation_matches_executable_sources():
    path = ROOT / "tools/sync_documentation_examples.py"
    spec = importlib.util.spec_from_file_location("sync_examples", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for path, expected in module.documents():
        assert path.read_text(encoding="utf-8") == expected, str(path)


def test_ar_example_prints_decoded_user_data_and_matches_cli(monkeypatch):
    import io
    import numpy as np
    from PIL import Image

    image = io.BytesIO()
    Image.new("RGB", (2, 1), (230, 20, 10)).save(image, format="JPEG")
    depth = np.array([[10000, 20000]], dtype="<u2")
    frame = asmagic.ARFrame(
        timestamp=123, frame_id=8, source_timestamp=42,
        color_img=image.getvalue(), rgb_width=2, rgb_height=1,
        depth_img=depth.tobytes(), depth_width=2, depth_height=1,
        depth_meters_per_unit=0.0001, depth_confidence=bytes([1, 2]),
        local_pose=np.array([1, 2, 3, 0, 0, 0, 1]),
        global_pose=np.array([4, 5, 6, 0, 0, 0, 1]),
        velocity=np.array([0.1, 0.2, 0.3]),
        camera_intrinsics=np.array([100, 0, 0, 0, 200, 0, 20, 30, 1]),
        session_identifier="camera-session", shared_world_identifier="shared-world",
        global_pose_is_shared=True,
    )
    calls, printed = [], []

    class Receiver:
        def __init__(self, ip):
            calls.append(("connect", ip))

        def receive(self):
            calls.append("receive")
            if calls.count("receive") == 2:
                raise KeyboardInterrupt
            return frame

        def close(self):
            calls.append("close")

    monkeypatch.setattr(asmagic, "ARDataSubscriber", Receiver)
    monkeypatch.setattr("builtins.print", lambda *args: printed.append(args))
    module = runpy.run_path(str(ROOT / "examples/documentation/ar/01_continuous.py"))
    module["main"]()
    assert calls == [("connect", module["IPHONE_IP"]), "receive", "receive", "close"]
    values = {args[0]: args[1:] for args in printed}
    assert values["Frame ID:"] == (8,)
    assert values["RGB size:"] == values["Depth size:"] == (2, 1)
    assert values["RGB:"][0].shape == (1, 2, 3)
    np.testing.assert_equal(values["Depth (raw):"][0], depth)
    np.testing.assert_equal(values["Depth confidence:"][0], [[1, 2]])
    np.testing.assert_equal(values["Local transform:"][0][:3, 3], [1, 2, 3])
    np.testing.assert_equal(values["Global transform:"][0][:3, 3], [4, 5, 6])
    np.testing.assert_equal(values["Intrinsics matrix:"][0], [[100, 0, 20], [0, 200, 30], [0, 0, 1]])
    assert values["Session:"] == ("camera-session",)
    assert values["Shared world:"] == ("shared-world",)
    assert values["Has RGB / depth / pose:"] == (True, True, True)

    documentation_output = printed.copy()
    printed.clear()
    monkeypatch.syspath_prepend(str(ROOT / "examples"))
    cli = runpy.run_path(str(ROOT / "examples/read_ar_data.py"))
    cli["describe"](frame)
    assert len(printed) == len(documentation_output)
    for actual, expected in zip(printed, documentation_output):
        assert len(actual) == len(expected)
        for actual_value, expected_value in zip(actual, expected):
            np.testing.assert_equal(actual_value, expected_value)


@pytest.mark.parametrize("interrupt", [False, True])
def test_camera_example_displays_received_frame_and_closes_resources(monkeypatch, interrupt):
    import cv2
    calls = []

    class Frame:
        def show_images(self, **options):
            calls.append(("images", options))

    class Receiver:
        def __init__(self, ip, **options):
            assert ip == "192.0.2.1"

        def receive(self):
            calls.append("receive")
            if interrupt:
                raise KeyboardInterrupt
            return Frame()

        def close(self):
            calls.append("close")

    monkeypatch.setattr(asmagic, "ARDataSubscriber", Receiver)
    monkeypatch.setattr(cv2, "waitKey", lambda delay: calls.append("events") or 27)
    monkeypatch.setattr(cv2, "destroyAllWindows", lambda: calls.append("windows closed"))
    module = runpy.run_path(str(ROOT / "examples/documentation/ar/03_display_images.py"))
    module["main"]("192.0.2.1")
    expected = ["receive"]
    if not interrupt:
        expected += [("images", {}), "events"]
    assert calls == expected + ["close", "windows closed"]


def test_camera_test_entrypoint_reuses_documentation_main():
    examples = ROOT / "examples"
    import sys
    sys.path.insert(0, str(examples))
    try:
        test_entry = runpy.run_path(str(examples / "test_camera.py"))
        display_entry = runpy.run_path(str(examples / "simple_with_images.py"))
        assert test_entry["main"] is display_entry["main"]
        assert test_entry["main"].__code__.co_filename == str(examples / "documentation/ar/03_display_images.py")
    finally:
        sys.path.remove(str(examples))


def test_cli_example_skips_timeout_and_closes_when_processing_raises(monkeypatch):
    import sys
    spec = importlib.util.spec_from_file_location("cli_example", ROOT / "examples/_common.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []

    class Receiver:
        _connected = True

        def __init__(self, ip, **options):
            self.receives = 0

        def _read_frame(self, timeout=1000):
            self.receives += 1
            return None if self.receives == 1 else object()

        def receive(self):
            from asmagic._subscriber import Receiver as BaseReceiver
            return BaseReceiver.receive(self)

        def close(self):
            calls.append("closed")

    def process(frame):
        raise RuntimeError("processing failed")

    monkeypatch.setattr(sys, "argv", ["example", "192.0.2.1"])
    with pytest.raises(RuntimeError, match="processing failed"):
        module.run(Receiver, process, "test")
    assert calls == ["closed"]


def test_cli_plot_remains_responsive_when_sender_stops(monkeypatch):
    import sys
    spec = importlib.util.spec_from_file_location("cli_plot_example", ROOT / "examples/_common.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls = []
    frame = object()

    class Receiver:
        def __init__(self, ip, **options):
            self.frames = iter((frame, None))

        def receive(self, timeout=None):
            assert timeout == 50
            return next(self.frames)

        def close(self):
            calls.append("receiver closed")

    class Viewer:
        is_open = True

        def __init__(self, **options):
            pass

        def update(self, received):
            assert received is frame
            calls.append("draw")

        def idle(self):
            calls.append("events")
            self.is_open = False

        def close(self):
            calls.append("viewer closed")

    monkeypatch.setattr(asmagic, "TrackingPlotter", Viewer)
    monkeypatch.setattr(sys, "argv", ["example", "192.0.2.1", "--plot"])
    module.run(Receiver, lambda received: calls.append("process"), "test", plotting=True)
    assert calls == ["draw", "process", "events", "viewer closed", "receiver closed"]


@pytest.mark.parametrize("timeout", [None, 2000])
def test_receive_skips_invalid_sensor_message_and_returns_next_valid_frame(publisher, timeout):
    from asmagic.proto import imu_msg_pb2
    socket, connect = publisher
    sub = connect(asmagic.IMUDataSubscriber, conflate=False, hwm=4)
    try:
        socket.send(b"\xff")
        socket.send(imu_msg_pb2.Imu(timestamp=10).SerializeToString())
        assert sub.receive(timeout=timeout).timestamp == 10
        assert sub.received_frames == 1 and sub.last_error is None
    finally:
        sub.close()


def test_watch_close_ends_pending_receive():
    import threading
    receiver = WatchIMUReceiver(port=0)
    stopped = threading.Event()

    def read():
        try:
            receiver.receive()
        except StopIteration:
            stopped.set()

    thread = threading.Thread(target=read)
    try:
        thread.start()
    finally:
        receiver.close()
        thread.join(timeout=2)
    assert not thread.is_alive() and stopped.is_set()


def test_recoverable_reads_share_one_receive_timeout_budget(monkeypatch):
    from asmagic import _subscriber
    clock = [0.0]
    waits = []

    def read(timeout):
        waits.append(timeout)
        clock[0] += 0.01  # A stream of undecodable packets must not restart the timeout.
        return None

    monkeypatch.setattr(_subscriber.time, "monotonic", lambda: clock[0])
    assert _subscriber._receive_frame(read, lambda: True, timeout=25) is None
    assert waits == pytest.approx([25, 15, 5], abs=1)


def test_hand_window_example_handles_timeouts_until_window_closes(monkeypatch):
    calls = []

    class Receiver:
        def __init__(self, ip):
            pass

        def receive(self, timeout=None):
            assert timeout == 50
            calls.append("timeout")
            return None

        def close(self):
            calls.append("receiver closed")

    class Window:
        is_open = True

        def __init__(self, **options):
            pass

        def update(self, frame):
            assert frame is None
            calls.append("events")
            self.is_open = False

        def close(self):
            calls.append("window closed")

    monkeypatch.setattr(asmagic, "HandPoseDataSubscriber", Receiver)
    monkeypatch.setattr(asmagic, "HandTrackingWindow", Window)
    module = runpy.run_path(str(ROOT / "examples/documentation/hand/03_optional_skeleton.py"))
    module["main"]()
    assert calls == ["timeout", "events", "timeout", "window closed", "receiver closed"]
