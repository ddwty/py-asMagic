import io
from pathlib import Path
import runpy
from types import SimpleNamespace

import cv2
import numpy as np
from PIL import Image
import pytest

import asmagic
from asmagic import CameraDataSubscriber
from asmagic.proto import phone_msg_pb2


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "documentation" / "camera"


def test_preview_can_quit_when_stream_is_paused(monkeypatch):
    calls = []

    class Receiver:
        def __init__(self, ip, conflate):
            assert conflate

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

        def close(self):
            calls.append("closed")

        def receive(self, timeout):
            calls.append(timeout)
            return None

    monkeypatch.setattr(asmagic, "CameraDataSubscriber", Receiver)
    monkeypatch.setattr(cv2, "waitKey", lambda delay: ord("q"))
    monkeypatch.setattr(cv2, "destroyAllWindows", lambda: calls.append("windows closed"))
    runpy.run_path(str(EXAMPLES / "01_preview.py"), run_name="__main__")
    assert calls == [100, "closed", "windows closed"]


def test_save_image_converts_rgb_and_reports_write_failure(monkeypatch):
    rgb = np.full((2, 4, 3), (10, 20, 30), dtype=np.uint8)
    closed = []

    class Receiver:
        def __init__(self, ip, conflate):
            assert conflate

        def __enter__(self):
            return self

        def __exit__(self, *args):
            closed.append(True)

        def receive(self, timeout):
            return SimpleNamespace(has_color_image=True, color_upright=rgb)

    def fail_write(path, bgr):
        np.testing.assert_array_equal(bgr[0, 0], (30, 20, 10))
        return False

    monkeypatch.setattr(asmagic, "CameraDataSubscriber", Receiver)
    monkeypatch.setattr(cv2, "imwrite", fail_write)
    with pytest.raises(OSError, match="Could not save"):
        runpy.run_path(str(EXAMPLES / "03_save_image.py"), run_name="__main__")
    assert closed == [True]


@pytest.mark.parametrize("size", [(640, 360), (360, 640), (1280, 720), (720, 1280), (1920, 1080)])
def test_camera_receives_selected_resolution_over_tcp(publisher, size):
    socket, connect = publisher
    receiver = connect(CameraDataSubscriber)
    encoded = io.BytesIO()
    Image.new("RGB", size, (10, 20, 30)).save(encoded, format="JPEG")
    message = phone_msg_pb2.Phone(
        rgb_width=size[0], rgb_height=size[1], color_img=encoded.getvalue(), rgb_codec=1,
        frame_id=1, image_rotation_quarter_turns_clockwise=0)
    socket.send(message.SerializeToString())
    frame = receiver.receive(timeout=2000)
    assert (frame.width, frame.height) == size
    assert frame.image_upright.shape == (size[1], size[0], 3)


def test_legacy_camera_example_matches_documentation_source():
    assert (ROOT / "examples" / "camera_only.py").read_text() == (EXAMPLES / "01_preview.py").read_text()
