"""User-controlled live Matplotlib tracking plots; pyplot is imported on demand."""
import json
import time
from typing import Optional, TYPE_CHECKING

import numpy as np

from .joints import BodyCoordinateSpace, HandJointName, HandSide, HAND_JOINT_NAMES

if TYPE_CHECKING:
    from .tracking_types import HandPoseFrame


# Same topology as HandPoseJointName.bones in the sending app.
HAND_BONES = tuple((HandJointName[a].row, HandJointName[b].row) for a, b in (
    ("WRIST", "THUMB_CMC"), ("THUMB_CMC", "THUMB_MP"), ("THUMB_MP", "THUMB_IP"), ("THUMB_IP", "THUMB_TIP"),
    ("WRIST", "INDEX_MCP"), ("INDEX_MCP", "INDEX_PIP"), ("INDEX_PIP", "INDEX_DIP"), ("INDEX_DIP", "INDEX_TIP"),
    ("WRIST", "MIDDLE_MCP"), ("MIDDLE_MCP", "MIDDLE_PIP"), ("MIDDLE_PIP", "MIDDLE_DIP"), ("MIDDLE_DIP", "MIDDLE_TIP"),
    ("WRIST", "RING_MCP"), ("RING_MCP", "RING_PIP"), ("RING_PIP", "RING_DIP"), ("RING_DIP", "RING_TIP"),
    ("WRIST", "LITTLE_MCP"), ("LITTLE_MCP", "LITTLE_PIP"), ("LITTLE_PIP", "LITTLE_DIP"), ("LITTLE_DIP", "LITTLE_TIP"),
    ("INDEX_MCP", "MIDDLE_MCP"), ("MIDDLE_MCP", "RING_MCP"), ("RING_MCP", "LITTLE_MCP")))


def _pyplot():
    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise ImportError("绘图依赖 Matplotlib，请完整安装 SDK：python -m pip install --upgrade asmagic") from error
    return plt


def supports_plot(frame) -> bool:
    from .body_tracking import BodyTrackingFrame
    from .tracking_types import ARBodyFrame, BodyPoseFrame, Hand, HandPoseFrame, FaceFrame, FaceAndHandTrackingFrame
    return isinstance(frame, (BodyTrackingFrame, ARBodyFrame, BodyPoseFrame, Hand, HandPoseFrame, FaceFrame, FaceAndHandTrackingFrame))


def upper_body_points(frame):
    """Reconstruct a common neck coordinate space; respect sender detection metadata."""
    names = ("neck", "leftShoulder", "leftElbow", "leftWrist", "rightShoulder", "rightElbow", "rightWrist")
    points = np.full((7, 2), np.nan, dtype=np.float32)
    present = np.zeros(7, dtype=bool)
    detected = None
    try:
        metadata = json.loads(frame.json_data) if frame.json_data else {}
        values = metadata.get("detected_joints") if isinstance(metadata, dict) else None
        if isinstance(values, list) and all(isinstance(name, str) for name in values):
            detected = set(values)
    except (ValueError, TypeError):
        pass
    pose = frame.upper_body
    if pose is not None:
        origin = np.array([pose.neck.x, pose.neck.y], dtype=np.float32)
        if pose.HasField("neck"):
            points[0], present[0] = origin, True
        for side, start in (("left_arm", 1), ("right_arm", 4)):
            if not pose.HasField(side):
                continue
            arm = getattr(pose, side)
            position = origin.copy()
            for index, name in enumerate(("shoulder", "elbow", "wrist"), start):
                if not arm.HasField(name):
                    break  # downstream relative vectors require every previous vector
                value = getattr(arm, name)
                position = position + [value.x, value.y]
                points[index], present[index] = position, True
    if detected is not None:
        present &= np.array([name in detected for name in names])
    present &= np.isfinite(points).all(axis=1)
    edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6)]
    segments = [points[[a, b]] for a, b in edges if present[a] and present[b]]
    return names, points, present, segments, detected is not None


class TrackingPlotter:
    """Reusable tracking window; update() never receives or mutates a sensor frame.

    Use on the main thread with a GUI Matplotlib backend. max_fps limits drawing
    only. BODY and WORLD share a spatial origin; PARENT does not, so it is rejected.
    """
    def __init__(self, space: BodyCoordinateSpace = BodyCoordinateSpace.BODY,
                 labels: bool = False, max_fps: float = 30, stale_after: float = 2.0,
                 min_confidence: float = 0.0):
        self.space = BodyCoordinateSpace(space)
        if self.space == BodyCoordinateSpace.PARENT:
            raise ValueError("父关节坐标各有原点，不能直接放在同一图中；绘图请选择 BODY 或 WORLD")
        if not np.isfinite(max_fps) or max_fps <= 0 or not np.isfinite(stale_after) or stale_after <= 0:
            raise ValueError("max_fps and stale_after must be positive finite numbers")
        if not np.isfinite(min_confidence) or not 0 <= min_confidence <= 1:
            raise ValueError("min_confidence must be between 0 and 1")
        self.labels, self.max_fps, self.stale_after = labels, max_fps, stale_after
        self.min_confidence = min_confidence
        self.figure = None
        self.axes = []
        self._artists = []
        self._texts = []
        self._kind = None
        self._plt = None
        self._closed = False
        self._last_draw = None
        self._last_frame = None
        self._stale = False

    @property
    def is_open(self) -> bool:
        return not self._closed and (self.figure is None or self._plt.fignum_exists(self.figure.number))

    def _create(self, kind):
        self._plt = _pyplot()
        self._kind = kind
        if kind == "people":
            self.figure = self._plt.figure(figsize=(7, 6))
        elif kind == "body":
            from mpl_toolkits.mplot3d.art3d import Line3DCollection
            self.figure = self._plt.figure(figsize=(8, 7))
            ax = self.figure.add_subplot(111, projection="3d")
            ax.set(xlabel="X (m)", ylabel="Y (m)", zlabel="Z (m)")
            ax.set_box_aspect((1, 1, 1))
            ax.view_init(elev=12, azim=-15, vertical_axis="y")
            tracked = ax.scatter([], [], [], color="#1769aa", s=25, label="Directly tracked")
            other = ax.scatter([], [], [], color="#8b9299", s=20, label="Estimated / flag unavailable")
            bones = Line3DCollection([], colors="#476477", linewidths=1.5)
            # It is already a 3D collection; avoid autoscaling an empty collection
            # (new Matplotlib versions concatenate its empty segment list).
            ax.add_collection(bones, autolim=False)
            ax.legend(loc="upper right", fontsize=8)
            self.axes, self._artists = [ax], [(tracked, other, bones)]
        else:
            from matplotlib.collections import LineCollection
            count = {"hand": 1, "hands": 2, "face_hand": 3, "face": 1, "upper_body": 1}[kind]
            self.figure, axes = self._plt.subplots(1, count, figsize=(5 * count, 5), squeeze=False)
            self.axes = list(axes[0])
            for ax in self.axes:
                points = ax.scatter([], [], c=[], cmap="Blues", vmin=0, vmax=1, s=32,
                                    edgecolors="#476477", linewidths=.5)
                bones = LineCollection([], colors="#567684", linewidths=1.5)
                ax.add_collection(bones)
                ax.set_aspect("equal", adjustable="box")
                if kind == "upper_body":
                    ax.set(xlabel="Relative X", ylabel="Relative Y", xlim=(-.7, .7), ylim=(-.7, .7))
                else:
                    ax.set(xlabel="Raw image X", ylabel="Raw image Y", xlim=(0, 1), ylim=(1, 0))
                ax.grid(alpha=.2)
                self._artists.append((points, bones))
        self.figure.tight_layout(rect=(0, 0, 1, .9))
        if getattr(self.figure.canvas, "required_interactive_framework", None):
            self._plt.show(block=False)

    def _annotations(self, ax, names, points):
        if self.labels:
            for name, point in zip(names, points):
                self._texts.append(ax.text(*point, name, fontsize=7))

    def _hand(self, axis, hand, title, side=HandSide.UNKNOWN):
        ax = self.axes[axis]
        scatter, bones = self._artists[axis]
        if side == HandSide.UNKNOWN and hand is not None:
            side = hand.side
        color = {HandSide.LEFT: "#1769aa", HandSide.RIGHT: "#cf691c"}.get(side, "#567684")
        scatter.set_cmap("Oranges" if side == HandSide.RIGHT else "Blues")
        scatter.set_edgecolor(color)
        bones.set_color(color)
        points = np.empty((0, 2), dtype=np.float32)
        confidences = np.array([])
        segments = []
        if hand is not None:
            bulk = hand.as_arrays()
            valid = (bulk.valid & np.isfinite(bulk.points).all(axis=1)
                     & np.isfinite(bulk.confidences) & (bulk.confidences >= self.min_confidence))
            points, confidences = bulk.points[valid], bulk.confidences[valid]
            segments = [bulk.points[[a, b]] for a, b in HAND_BONES if valid[a] and valid[b]]
            names = ["{}: {}".format(HandJointName(name).row, name) if name in HAND_JOINT_NAMES
                     else name for name, ok in zip(bulk.names, valid) if ok]
            self._annotations(ax, names, points)
        scatter.set_offsets(points)
        scatter.set_array(confidences)
        bones.set_segments(segments)
        ax.set_title("{} — {} points".format(title, len(points)))

    def update(self, frame, force: bool = False):
        from .body_tracking import BodyTrackingFrame
        from .tracking_types import ARBodyFrame, BodyPoseFrame, Hand, HandPoseFrame, FaceFrame, FaceAndHandTrackingFrame
        if not self.is_open:
            return self
        if not supports_plot(frame):
            raise TypeError("绘图支持 ARBodyFrame、BodyPoseFrame、Hand、HandPoseFrame 、FaceFrame 和旧 FaceAndHandTrackingFrame")
        kind = ("people" if isinstance(frame, BodyTrackingFrame) else "body" if isinstance(frame, ARBodyFrame) else "upper_body" if isinstance(frame, BodyPoseFrame)
                else "hand" if isinstance(frame, Hand) else "hands" if isinstance(frame, HandPoseFrame)
                else "face_hand" if isinstance(frame, FaceAndHandTrackingFrame) else "face")
        if self._kind is not None and kind != self._kind:
            raise TypeError("同一个 TrackingPlotter 只处理同一种帧类型")
        now = time.monotonic()
        self._last_frame = now
        # Tracking loss must clear visible data even inside the drawing interval.
        loss = ((kind in ("body", "people") and not frame.is_tracking) or
                (kind == "hands" and not frame.hand_count) or
                (kind == "face" and not frame.has_face) or
                (kind == "face_hand" and not frame.has_face and frame.left_hand is None and frame.right_hand is None))
        if not force and not loss and self._last_draw is not None and now - self._last_draw < 1 / self.max_fps:
            self.idle()
            return self
        if self.figure is None:
            self._create(kind)
        for artist in self._texts:
            artist.remove()
        self._texts.clear()
        if kind == "people":
            self._people(frame)
        elif kind == "body":
            body = frame.skeleton(self.space)
            valid = body.valid & np.isfinite(body.positions).all(axis=1) & frame.is_tracking
            points = body.positions
            tracked, other, bones = self._artists[0]
            for artist, mask in ((tracked, valid & body.tracked), (other, valid & ~body.tracked)):
                subset = points[mask]
                artist._offsets3d = (subset[:, 0], subset[:, 1], subset[:, 2])
            segments = [points[[parent, child]] for child, parent in enumerate(body.parent_indices)
                        if 0 <= parent < len(points) and parent != child and valid[parent] and valid[child]]
            bones.set_segments(segments)
            ax = self.axes[0]
            ax.set_title("Body / {} — {} — {} joints".format(self.space.value, frame.tracking_state, int(valid.sum())))
            if valid.any():
                shown = points[valid]
                center = (shown.max(axis=0) + shown.min(axis=0)) / 2
                radius = max(.5, float(np.ptp(shown, axis=0).max()) * .6)
                ax.set_xlim(center[0] - radius, center[0] + radius)
                ax.set_ylim(center[1] - radius, center[1] + radius)
                ax.set_zlim(center[2] - radius, center[2] + radius)
                self._annotations(ax, [name for name, ok in zip(body.names, valid) if ok], shown)
        elif kind == "upper_body":
            names, points, valid, segments, flags = upper_body_points(frame)
            scatter, bones = self._artists[0]
            scatter.set_offsets(points[valid])
            scatter.set_array(np.ones(int(valid.sum())))
            bones.set_segments(segments)
            self.axes[0].set_title("Upper body — {} points{}".format(int(valid.sum()), "" if flags else " / detection flags unavailable"))
            self._annotations(self.axes[0], [name for name, ok in zip(names, valid) if ok], points[valid])
        elif kind == "hand":
            title = {HandSide.LEFT: "Left hand (L)", HandSide.RIGHT: "Right hand (R)"}.get(frame.side, "Hand (side unknown)")
            self._hand(0, frame, title)
        else:
            offset = 0
            if isinstance(frame, FaceFrame):
                points = frame.points if frame.has_face else np.empty((0, 2))
                points = points[np.isfinite(points).all(axis=1)]
                self._artists[0][0].set_offsets(points)
                self._artists[0][0].set_array(np.ones(len(points)))
                self.axes[0].set_title("Face / {} — {} points".format(frame.tracking_mode, len(points)))
                offset = 1
            if kind != "face":
                self._hand(offset, frame.left_hand, "Left hand (L)", HandSide.LEFT)
                self._hand(offset + 1, frame.right_hand, "Right hand (R)", HandSide.RIGHT)
        self._stale = False
        self._last_draw = now
        self.figure.suptitle("")
        self.figure.canvas.draw_idle()
        self.figure.canvas.flush_events()
        return self

    def _people(self, frame):
        """Each local body gets its own panel; unrelated body origins never overlap."""
        from mpl_toolkits.mplot3d.art3d import Line3DCollection
        count = max(1, frame.person_count)
        if len(self.axes) != count:
            for ax in self.axes:
                ax.remove()
            self.axes, self._artists = [], []
            columns = min(count, 2)
            rows = (count + columns - 1) // columns
            self.figure.set_size_inches(6 * columns, 5 * rows, forward=True)
            for panel in range(count):
                ax = self.figure.add_subplot(rows, columns, panel + 1, projection="3d")
                ax.set(xlabel="X (m)", ylabel="Y (m)", zlabel="Z (m)")
                ax.set_box_aspect((1, 1, 1))
                ax.view_init(elev=12, azim=-15, vertical_axis="y")
                points = ax.scatter([], [], [], color="#1769aa", s=24)
                bones = Line3DCollection([], colors="#567684", linewidths=1.5)
                ax.add_collection(bones, autolim=False)
                self.axes.append(ax)
                self._artists.append((points, bones))
            self.figure.tight_layout()
        for panel, ax in enumerate(self.axes):
            scatter, bones = self._artists[panel]
            if panel >= frame.person_count:
                scatter._offsets3d = ([], [], [])
                bones.set_segments([])
                ax.set_title("Waiting for body data")
                continue
            person = frame.people[panel]
            skeleton = person.skeleton(self.space)
            valid = skeleton.valid.copy()
            if frame.model.value == "mediapipe":
                valid &= (skeleton.visibility >= self.min_confidence) & (skeleton.presence >= self.min_confidence)
            shown = skeleton.positions[valid]
            scatter._offsets3d = (shown[:, 0], shown[:, 1], shown[:, 2])
            bones.set_segments([skeleton.positions[[a, b]] for a, b in skeleton.bones if valid[a] and valid[b]])
            ax.set_title("Person {} / {} / {}".format(person.label, person.id, self.space.value))
            if shown.size:
                center = (shown.max(axis=0) + shown.min(axis=0)) / 2
                radius = max(.5, float(np.ptp(shown, axis=0).max()) * .6)
                ax.set_xlim(center[0] - radius, center[0] + radius)
                ax.set_ylim(center[1] - radius, center[1] + radius)
                ax.set_zlim(center[2] - radius, center[2] + radius)
                self._annotations(ax, [n for n, ok in zip(skeleton.names, valid) if ok], shown)

    def idle(self):
        """Pump window events during receive timeouts; erase stale data once."""
        if self.figure is None or not self.is_open:
            return
        if self._last_frame is not None and time.monotonic() - self._last_frame > self.stale_after and not self._stale:
            for artists in self._artists:
                if self._kind == "people":
                    artists[0]._offsets3d = ([], [], [])
                    artists[1].set_segments([])
                elif self._kind == "body":
                    artists[0]._offsets3d = ([], [], [])
                    artists[1]._offsets3d = ([], [], [])
                    artists[2].set_segments([])
                else:
                    artists[0].set_offsets(np.empty((0, 2)))
                    artists[0].set_array(np.array([]))
                    artists[1].set_segments([])
            for artist in self._texts:
                artist.remove()
            self._texts.clear()
            self.figure.suptitle("No recent data — waiting for sender")
            self._stale = True
            self.figure.canvas.draw_idle()
        self.figure.canvas.flush_events()

    def save(self, path, **kwargs):
        if self.figure is None:
            raise RuntimeError("先调用 update(frame)，再保存绘图")
        self.figure.savefig(path, **kwargs)

    def close(self):
        self._closed = True
        if self.figure is not None:
            self._plt.close(self.figure)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class HandTrackingWindow(TrackingPlotter):
    """Two anatomical hand panels, ready before the first frame arrives.

    Call update(frame) with an already-received HandPoseFrame, or update(None)
    during a receive timeout. Labels show SDK array rows and joint names.
    Run on the main thread with a GUI Matplotlib backend. No socket is opened.
    """
    def __init__(self, labels: bool = True, max_fps: float = 30,
                 stale_after: float = 2.0, min_confidence: float = 0.0):
        super().__init__(labels=labels, max_fps=max_fps, stale_after=stale_after,
                         min_confidence=min_confidence)
        self._create("hands")
        self.figure.canvas.manager.set_window_title("asMagic Hand Tracking")
        self._hand(0, None, "Left hand (L)", HandSide.LEFT)
        self._hand(1, None, "Right hand (R)", HandSide.RIGHT)
        self.axes[0].set_title("Left hand (L) — waiting")
        self.axes[1].set_title("Right hand (R) — waiting")
        self.figure.suptitle("Waiting for hand data")
        self.figure.canvas.draw_idle()
        self.figure.canvas.flush_events()

    def update(self, frame: Optional["HandPoseFrame"], force: bool = False) -> "HandTrackingWindow":
        from .tracking_types import HandPoseFrame
        if frame is None:
            self.idle()
            return self
        if not isinstance(frame, HandPoseFrame):
            raise TypeError("HandTrackingWindow.update expects a HandPoseFrame or None")
        previous_draw = self._last_draw
        result = super().update(frame, force=force)
        if self.is_open and not self._stale and self._last_draw != previous_draw:
            self.figure.suptitle("t={:.3f}s | L={} R={} | unassigned={}".format(
                frame.timestamp, int(frame.has_left_hand), int(frame.has_right_hand), frame.unknown_hand_count))
            self.figure.canvas.draw_idle()
        return result

    def idle(self):
        was_stale = self._stale
        super().idle()
        if self.is_open and self._stale and not was_stale:
            self.axes[0].set_title("Left hand (L) — waiting")
            self.axes[1].set_title("Right hand (R) — waiting")
            self.figure.canvas.draw_idle()


def plot_tracking(frame, enabled: bool = True, plotter: Optional[TrackingPlotter] = None, **options):
    """Plot one already-received frame; disabled calls allocate no figure/import pyplot."""
    if not enabled:
        return None
    if plotter is not None and options:
        raise ValueError("已有 plotter 时，请在创建它时设置绘图选项")
    result = plotter if plotter is not None else TrackingPlotter(**options)
    try:
        return result.update(frame, force=True)
    except Exception:
        if plotter is None:
            result.close()
        raise
