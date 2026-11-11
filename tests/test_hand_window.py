"""Hand window checks with a headless backend; no live sender or GUI is required."""
import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg", force=True)

from asmagic import HandPoseDataSubscriber, HandTrackingWindow, TrackingPlotter
from asmagic.proto import hand_pose_pb2


def test_hand_window_opens_before_data_and_uses_distinct_anatomical_panels(tmp_path):
    with HandTrackingWindow() as window:
        assert window.is_open and len(window.axes) == 2
        assert "Left hand (L)" in window.axes[0].get_title()
        assert "Right hand (R)" in window.axes[1].get_title()
        window.update(None)
        assert window.figure._suptitle.get_text() == "Waiting for hand data"
        message = hand_pose_pb2.HandPoseFrame(source_timestamp=4, unknown_hand_count=1)
        message.left_hand.joints.add(name="index_tip", x=.9, y=.2, confidence=.8)
        message.right_hand.joints.add(name="index_tip", x=.1, y=.3, confidence=.8)
        frame = HandPoseDataSubscriber.decode(message.SerializeToString())
        assert window.update(frame, force=True) is window
        np.testing.assert_allclose(window._artists[0][0].get_offsets(), [[.9, .2]])
        np.testing.assert_allclose(window._artists[1][0].get_offsets(), [[.1, .3]])
        assert window._artists[0][0].get_cmap().name == "Blues"
        assert window._artists[1][0].get_cmap().name == "Oranges"
        assert all(text.get_text() == "8: index_tip" for text in window._texts)
        assert "unassigned=1" in window.figure._suptitle.get_text()
        path = tmp_path / "hands.png"
        window.save(path)
        assert path.stat().st_size > 1000
    assert not window.is_open


def test_hand_window_filters_drawing_only_and_never_bridges_missing_nodes():
    message = hand_pose_pb2.HandPoseFrame()
    for name, confidence in (("wrist", .9), ("thumb_cmc", .1), ("thumb_mp", .8)):
        message.left_hand.joints.add(name=name, x=.2, y=.8, confidence=confidence)
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    before = frame.left.as_arrays().points.copy()
    with HandTrackingWindow(min_confidence=.5) as window:
        window.update(frame, force=True)
        assert len(window._artists[0][0].get_offsets()) == 2
        assert not len(window._artists[0][1].get_segments())
        np.testing.assert_equal(frame.left.as_arrays().points, before)
        assert frame.left.thumb.cmc is not None
        window.update(HandPoseDataSubscriber.decode(hand_pose_pb2.HandPoseFrame().SerializeToString()))
        assert all(not len(artists[0].get_offsets()) for artists in window._artists)
        assert not window._texts


def test_timeout_erases_stale_data_and_single_hand_plot_keeps_side(monkeypatch):
    message = hand_pose_pb2.HandPoseFrame()
    message.right_hand.joints.add(name="wrist", x=.4, y=.6, confidence=.9)
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    with HandTrackingWindow(stale_after=1) as window:
        window.update(frame)
        now = window._last_frame + 2
        monkeypatch.setattr("asmagic.plotting.time.monotonic", lambda: now)
        window.update(None)
        assert all(not len(artists[0].get_offsets()) for artists in window._artists)
        assert "waiting" in window.figure._suptitle.get_text()
        assert "waiting" in window.axes[1].get_title()
    with TrackingPlotter() as window:
        window.update(frame.right)
        assert "Right hand (R)" in window.axes[0].get_title()


def test_hand_window_rejects_wrong_frames_and_invalid_confidence():
    for confidence in (-.1, 1.1, np.nan):
        with pytest.raises(ValueError, match="min_confidence"):
            HandTrackingWindow(min_confidence=confidence)
    with HandTrackingWindow() as window:
        with pytest.raises(TypeError, match="HandPoseFrame or None"):
            window.update(object())
        window.close()
        window.update(None)
        assert not window.is_open


def test_hand_window_respects_drawing_rate_without_refreshing_old_frame_labels(monkeypatch):
    message = hand_pose_pb2.HandPoseFrame(source_timestamp=4)
    message.right_hand.joints.add(name="wrist", x=.4, y=.6, confidence=.9)
    with HandTrackingWindow(max_fps=1) as window:
        monkeypatch.setattr("asmagic.plotting.time.monotonic", lambda: 10)
        window.update(HandPoseDataSubscriber.decode(message.SerializeToString()))
        draws = []
        monkeypatch.setattr(window.figure.canvas, "draw_idle", lambda: draws.append(True))
        monkeypatch.setattr("asmagic.plotting.time.monotonic", lambda: 10.1)
        message.source_timestamp = 5
        message.right_hand.joints[0].x = .8
        window.update(HandPoseDataSubscriber.decode(message.SerializeToString()))
        assert not draws and window._last_draw == 10
        assert "t=4.000s" in window.figure._suptitle.get_text()
        np.testing.assert_allclose(window._artists[1][0].get_offsets(), [[.4, .6]])
