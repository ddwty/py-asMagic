import json
import subprocess
import sys

import numpy as np
import pytest

matplotlib = pytest.importorskip("matplotlib")
matplotlib.use("Agg", force=True)

from asmagic import (ARBodyDataSubscriber, ARBodyFrame, BodyCoordinateSpace, BodyPoseDataSubscriber,
                     FaceAndHandTrackingDataSubscriber, HandPoseDataSubscriber, TrackingPlotter)
from asmagic.plotting import upper_body_points
from asmagic.proto import armpose_msg_pb2, body_pose_msg_pb2, hand_pose_pb2, face_tracking_pb2


def body_frame():
    message = armpose_msg_pb2.Armpose(tracking_state="tracking")
    message.joints["hips_joint"].rotation.w = 1
    message.joints["left_hand_joint"].position.x = .5
    message.joints["left_hand_joint"].rotation.w = 1
    message.joint_parents["left_hand_joint"] = "hips_joint"
    message.tracked_joints["hips_joint"] = True
    message.body_transform.rotation.w = 1
    message.body_transform.position.x = 5
    return ARBodyDataSubscriber.decode(message.SerializeToString())


def test_disabled_plotting_does_not_import_matplotlib():
    code = """
import builtins, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.startswith('matplotlib'):
        raise AssertionError('disabled plotting imported Matplotlib')
    return original(name, *args, **kwargs)
builtins.__import__ = guarded
from asmagic import ARBodyFrame, HandPoseFrame, plot_tracking
assert ARBodyFrame().plot(enabled=False) is None
assert plot_tracking(HandPoseFrame(), enabled=False) is None
assert not any(name.startswith('matplotlib') for name in sys.modules)
"""
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


def test_body_plot_uses_world_transform_real_parents_and_clears_lost_tracking(tmp_path):
    frame = body_frame()
    with TrackingPlotter(space=BodyCoordinateSpace.WORLD, labels=True) as plot:
        plot.update(frame, force=True)
        tracked, other, bones = plot._artists[0]
        np.testing.assert_allclose(tracked._offsets3d[0], [5])
        np.testing.assert_allclose(other._offsets3d[0], [5.5])
        assert len(bones._segments3d) == 1
        before = frame.joints.left_hand.position.copy()
        path = tmp_path / "body.png"
        plot.save(path)
        assert path.stat().st_size > 1000
        np.testing.assert_equal(frame.joints.left_hand.position, before)
        plot.update(ARBodyFrame(tracking_state="searching"))
        assert not len(tracked._offsets3d[0]) and not len(bones._segments3d)
        assert not plot._texts


def test_hand_plot_connects_only_present_joints_and_preserves_raw_coordinates():
    message = hand_pose_pb2.HandPoseFrame()
    message.left_hand.joints.add(name="wrist", x=.2, y=.8, confidence=.9)
    message.left_hand.joints.add(name="thumb_cmc", x=.3, y=.7, confidence=.8)
    # No thumb_mp: do not connect cmc to tip across the missing nodes.
    message.left_hand.joints.add(name="thumb_tip", x=.4, y=.5, confidence=.7)
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    with TrackingPlotter() as plot:
        plot.update(frame, force=True)
        scatter, bones = plot._artists[0]
        np.testing.assert_allclose(scatter.get_offsets(), [[.2, .8], [.3, .7], [.4, .5]])
        assert len(bones.get_segments()) == 1
        assert plot.axes[0].get_ylim() == (1, 0)
        assert not len(plot._artists[1][0].get_offsets())
        plot.update(HandPoseDataSubscriber.decode(hand_pose_pb2.HandPoseFrame().SerializeToString()))
        assert not len(scatter.get_offsets()) and not len(bones.get_segments())


def test_upper_body_reconstructs_relative_chain_and_respects_detection_flags():
    message = body_pose_msg_pb2.BodyPoseMessage()
    message.upper_body.neck.SetInParent()
    message.upper_body.left_arm.shoulder.x = -.2
    message.upper_body.left_arm.elbow.y = -.3
    message.upper_body.left_arm.wrist.x = -.1
    message.json_data = json.dumps({"detected_joints": ["neck", "leftShoulder", "leftElbow"]})
    frame = BodyPoseDataSubscriber.decode(message.SerializeToString())
    names, points, valid, segments, known = upper_body_points(frame)
    np.testing.assert_allclose(points[3], [-.3, -.3])
    assert known and not valid[3] and len(segments) == 2
    with TrackingPlotter() as plot:
        plot.update(frame)
        assert len(plot._artists[0][0].get_offsets()) == 3


def test_face_hand_plot_and_stale_timeout_erase_points(monkeypatch):
    message = face_tracking_pb2.FaceAndHandTrackingFrame(has_face=True)
    message.landmarks.add(index=0, region="mesh", image_x=.4, image_y=.3)
    message.hand_pose.right_hand.joints.add(name="wrist", x=.7, y=.8, confidence=.9)
    frame = FaceAndHandTrackingDataSubscriber.decode(message.SerializeToString())
    with TrackingPlotter(stale_after=1) as plot:
        plot.update(frame)
        assert len(plot.axes) == 3
        assert len(plot._artists[0][0].get_offsets()) == 1
        assert len(plot._artists[2][0].get_offsets()) == 1
        monkeypatch.setattr("asmagic.plotting.time.monotonic", lambda: plot._last_frame + 2)
        plot.idle()
        assert all(not len(artists[0].get_offsets()) for artists in plot._artists)
        assert "waiting" in plot.figure._suptitle.get_text()
        plot.update(frame, force=True)
        assert plot.figure._suptitle.get_text() == ""


def test_plotter_reuse_and_invalid_coordinate_options():
    with pytest.raises(ValueError, match="父关节"):
        TrackingPlotter(space=BodyCoordinateSpace.PARENT)
    with pytest.raises(ValueError):
        TrackingPlotter(max_fps=0)
    frame = body_frame()
    plot = frame.plot()
    assert frame.plot(plotter=plot) is plot
    with pytest.raises(TypeError):
        plot.update(HandPoseDataSubscriber.decode(hand_pose_pb2.HandPoseFrame().SerializeToString()))
    plot.close()
    assert not plot.is_open


def test_stream_plot_reads_once_per_yield_and_closes_with_generator(publisher, monkeypatch):
    socket, connect = publisher
    sub = connect(HandPoseDataSubscriber)
    created = []
    original = TrackingPlotter.__init__

    def record(self, *args, **kwargs):
        original(self, *args, **kwargs)
        created.append(self)

    monkeypatch.setattr(TrackingPlotter, "__init__", record)
    stream = sub.stream(plot=True)
    socket.send(hand_pose_pb2.HandPoseFrame(source_timestamp=7).SerializeToString())
    assert next(stream).timestamp == 7
    assert sub.received_frames == 1 and len(created) == 1
    stream.close()
    assert not created[0].is_open


def test_face_only_plot_has_no_hand_panels_and_clears_on_loss():
    from asmagic import FaceDataSubscriber
    message = face_tracking_pb2.FaceTrackingFrame(has_face=True)
    message.landmarks.add(index=0, region="mesh", image_x=.2, image_y=.4)
    with TrackingPlotter(max_fps=30) as plot:
        plot.update(FaceDataSubscriber.decode(message.SerializeToString()))
        assert len(plot.axes) == 1
        assert plot._artists[0][0].get_offsets().shape == (1, 2)
        plot.update(FaceDataSubscriber.decode(face_tracking_pb2.FaceTrackingFrame().SerializeToString()))
        assert plot._artists[0][0].get_offsets().shape == (0, 2)


def test_face_receiver_stream_can_enable_plotting(publisher):
    from asmagic import FaceDataSubscriber
    from asmagic.diagnostics import run_stream_check
    socket, connect = publisher
    sub = connect(FaceDataSubscriber)
    message = face_tracking_pb2.FaceTrackingFrame(has_face=True)
    message.landmarks.add(index=0, region="mesh", image_x=.2, image_y=.4)
    socket.send(message.SerializeToString())
    frames = sub.stream(plot=True)
    try:
        assert next(frames).has_face
    finally:
        frames.close()
    socket.send(message.SerializeToString())
    result = run_stream_check("face", sub, duration=1, count=1, plot=True)
    assert result.status == "received" and result.component_frames["face"] == 1
