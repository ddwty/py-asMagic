"""Hand, face and full-body observations with explicit message presence."""
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import numpy as np
from google.protobuf.message import Message

from .geometry import pose_matrix
from .joints import (BODY_JOINT_NAMES, HAND_JOINT_NAMES, BodyCoordinateSpace,
                     BodyJointArrays, BodyJointName, HandJointArrays, HandJointName, HandSide,
                     _JointAccessor)


class _Plottable:
    def plot(self, enabled: bool = True, plotter=None, **options):
        """Optionally draw this frame; reuse the returned plotter for subsequent frames."""
        if not enabled:
            return None
        from .plotting import plot_tracking
        return plot_tracking(self, enabled=enabled, plotter=plotter, **options)


@dataclass
class HandJoint:
    """One named 2D camera-image point, with Python float coordinates and quality.

    x/y are normalized in the raw, unrotated and unmirrored image: origin at
    top-left, X right, Y down. confidence is node-level, normally 0–1.
    A missing node is represented by None on the hand, not by a zero point.
    """
    name: str
    x: float
    y: float
    confidence: float

    @property
    def xy(self) -> Tuple[float, float]:
        """Raw normalized (x, y), top-left origin, X right and Y down."""
        return self.x, self.y

    def to_pixels(self, image_width: int, image_height: int) -> Tuple[float, float]:
        """Continuous raw image coordinates; no rounding, clipping or rotation."""
        if (not np.isfinite(image_width) or not np.isfinite(image_height)
                or image_width <= 0 or image_height <= 0):
            raise ValueError("image_width and image_height must be positive finite dimensions")
        return self.x * image_width, self.y * image_height


@dataclass(frozen=True)
class HandFinger:
    """One non-thumb finger, from knuckle (MCP) to fingertip; missing joints are None."""
    mcp: Optional[HandJoint]
    pip: Optional[HandJoint]
    dip: Optional[HandJoint]
    tip: Optional[HandJoint]


@dataclass(frozen=True)
class HandThumb:
    """Thumb joints from the palm base (CMC) to tip; missing joints are None."""
    cmc: Optional[HandJoint]
    mp: Optional[HandJoint]
    ip: Optional[HandJoint]
    tip: Optional[HandJoint]


class HandJoints(Dict[str, HandJoint]):
    """Dictionary-compatible joints with typed, optional attribute access."""
    wrist = _JointAccessor[HandJoint](HandJointName.WRIST)
    thumb_cmc = _JointAccessor[HandJoint](HandJointName.THUMB_CMC)
    thumb_mp = _JointAccessor[HandJoint](HandJointName.THUMB_MP)
    thumb_ip = _JointAccessor[HandJoint](HandJointName.THUMB_IP)
    thumb_tip = _JointAccessor[HandJoint](HandJointName.THUMB_TIP)
    index_mcp = _JointAccessor[HandJoint](HandJointName.INDEX_MCP)
    index_pip = _JointAccessor[HandJoint](HandJointName.INDEX_PIP)
    index_dip = _JointAccessor[HandJoint](HandJointName.INDEX_DIP)
    index_tip = _JointAccessor[HandJoint](HandJointName.INDEX_TIP)
    middle_mcp = _JointAccessor[HandJoint](HandJointName.MIDDLE_MCP)
    middle_pip = _JointAccessor[HandJoint](HandJointName.MIDDLE_PIP)
    middle_dip = _JointAccessor[HandJoint](HandJointName.MIDDLE_DIP)
    middle_tip = _JointAccessor[HandJoint](HandJointName.MIDDLE_TIP)
    ring_mcp = _JointAccessor[HandJoint](HandJointName.RING_MCP)
    ring_pip = _JointAccessor[HandJoint](HandJointName.RING_PIP)
    ring_dip = _JointAccessor[HandJoint](HandJointName.RING_DIP)
    ring_tip = _JointAccessor[HandJoint](HandJointName.RING_TIP)
    little_mcp = _JointAccessor[HandJoint](HandJointName.LITTLE_MCP)
    little_pip = _JointAccessor[HandJoint](HandJointName.LITTLE_PIP)
    little_dip = _JointAccessor[HandJoint](HandJointName.LITTLE_DIP)
    little_tip = _JointAccessor[HandJoint](HandJointName.LITTLE_TIP)


@dataclass
class Hand(_Plottable):
    confidence: float
    joints: "HandJoints"
    side: HandSide = HandSide.UNKNOWN

    def __post_init__(self) -> None:
        if not isinstance(self.joints, HandJoints):
            self.joints = HandJoints(self.joints)
        self.side = HandSide(self.side)

    @property
    def wrist(self) -> Optional[HandJoint]:
        return self.joints.wrist

    @property
    def thumb(self) -> HandThumb:
        return HandThumb(self.joints.thumb_cmc, self.joints.thumb_mp,
                         self.joints.thumb_ip, self.joints.thumb_tip)

    def _finger(self, name: str) -> HandFinger:
        return HandFinger(*(self.joints.get(name + "_" + joint)
                            for joint in ("mcp", "pip", "dip", "tip")))

    @property
    def index(self) -> HandFinger:
        return self._finger("index")

    @property
    def middle(self) -> HandFinger:
        return self._finger("middle")

    @property
    def ring(self) -> HandFinger:
        return self._finger("ring")

    @property
    def little(self) -> HandFinger:
        return self._finger("little")

    @property
    def points(self) -> np.ndarray:
        return np.array([(joint.x, joint.y) for joint in self.joints.values()], dtype=np.float32).reshape(-1, 2)

    def as_arrays(self) -> HandJointArrays:
        """Export every joint in fixed order; absent rows are NaN with valid=False.

        The first 21 rows follow HandJointName. Unknown extension names are
        appended alphabetically, so future wire joints are not discarded.
        """
        names = HAND_JOINT_NAMES + tuple(sorted(set(self.joints).difference(HAND_JOINT_NAMES)))
        points = np.full((len(names), 2), np.nan, dtype=np.float32)
        confidences = np.full(len(names), np.nan, dtype=np.float32)
        valid = np.zeros(len(names), dtype=bool)
        for index, name in enumerate(names):
            joint = self.joints.get(name)
            if joint is not None:
                points[index] = (joint.x, joint.y)
                confidences[index] = joint.confidence
                valid[index] = True
        return HandJointArrays(names, points, confidences, valid)


@dataclass
class HandPoseFrame(_Plottable):
    """One hand observation; anatomical sides are Optional[Hand] objects.

    source_timestamp is the source camera time in seconds; image dimensions
    are raw pixels. An empty observation is still a frame with no hands.
    receive() returns this object; timed receive returns None only on timeout.
    """
    source_timestamp: float = 0.0
    image_width: int = 0
    image_height: int = 0
    unknown_hand_count: int = 0
    left_hand: Optional[Hand] = None
    right_hand: Optional[Hand] = None
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    @property
    def timestamp(self) -> float:
        return self.source_timestamp

    @property
    def left(self) -> Optional[Hand]:
        """The person's left hand; not the hand on the left of the image."""
        return self.left_hand

    @property
    def right(self) -> Optional[Hand]:
        return self.right_hand

    @property
    def hands(self) -> Tuple[Hand, ...]:
        """Assigned hands in left-then-right order, omitting absent hands."""
        return tuple(hand for hand in (self.left, self.right) if hand is not None)

    @property
    def has_left_hand(self) -> bool:
        return self.left_hand is not None

    @property
    def has_right_hand(self) -> bool:
        return self.right_hand is not None

    @property
    def hand_count(self) -> int:
        return int(self.has_left_hand) + int(self.has_right_hand)


@dataclass
class FaceImageLocation:
    center_x: float
    center_y: float
    width: float
    height: float


@dataclass
class FaceLandmark:
    index: int
    region: str
    image_x: float
    image_y: float
    position_face_meters: Optional[np.ndarray] = None


@dataclass
class FaceFrame(_Plottable):
    source_timestamp: float = 0.0
    has_face: bool = False
    image_width: int = 0
    image_height: int = 0
    image_location: Optional[FaceImageLocation] = None
    camera_position_meters: Optional[np.ndarray] = None
    camera_orientation: Optional[np.ndarray] = None
    blendshapes: Dict[str, float] = field(default_factory=dict)
    landmarks: Tuple[FaceLandmark, ...] = ()
    triangle_indices: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.uint32))
    tracking_mode: str = "unspecified"
    sequence_number: int = 0
    session_id: str = ""
    schema_version: int = 0
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    @property
    def timestamp(self) -> float:
        return self.source_timestamp

    @property
    def blendshape_coefficients(self) -> Dict[str, float]:
        return self.blendshapes

    @property
    def points(self) -> np.ndarray:
        return np.array([(p.image_x, p.image_y) for p in self.landmarks], dtype=np.float32).reshape(-1, 2)

    @property
    def triangles(self) -> np.ndarray:
        if self.triangle_indices.size % 3:
            raise ValueError("triangle_indices must contain groups of three")
        return self.triangle_indices.reshape(-1, 3)

    @property
    def face_vertices(self) -> Optional[np.ndarray]:
        if not self.landmarks or any(p.position_face_meters is None for p in self.landmarks):
            return None
        return np.stack([p.position_face_meters for p in self.landmarks])


@dataclass
class FaceAndHandTrackingFrame(FaceFrame):
    """Legacy combined frames from older App builds; current streams are separate."""
    hands: Optional[HandPoseFrame] = None

    @property
    def hand_pose(self) -> Optional[HandPoseFrame]:
        return self.hands

    @property
    def left_hand(self) -> Optional[Hand]:
        return self.hands.left_hand if self.hands is not None else None

    @property
    def right_hand(self) -> Optional[Hand]:
        return self.hands.right_hand if self.hands is not None else None

    @property
    def left(self) -> Optional[Hand]:
        return self.left_hand

    @property
    def right(self) -> Optional[Hand]:
        return self.right_hand

@dataclass
class JointTransform:
    position: np.ndarray
    rotation: np.ndarray

    @property
    def matrix(self) -> np.ndarray:
        return pose_matrix(np.concatenate((self.position, self.rotation)))


class BodyJoints(Dict[str, JointTransform]):
    """Dictionary-compatible joints with typed, optional attribute access."""
    root = _JointAccessor[JointTransform](BodyJointName.ROOT)
    hips = _JointAccessor[JointTransform](BodyJointName.HIPS)
    left_up_leg = _JointAccessor[JointTransform](BodyJointName.LEFT_UP_LEG)
    left_leg = _JointAccessor[JointTransform](BodyJointName.LEFT_LEG)
    left_foot = _JointAccessor[JointTransform](BodyJointName.LEFT_FOOT)
    left_toes = _JointAccessor[JointTransform](BodyJointName.LEFT_TOES)
    left_toes_end = _JointAccessor[JointTransform](BodyJointName.LEFT_TOES_END)
    right_up_leg = _JointAccessor[JointTransform](BodyJointName.RIGHT_UP_LEG)
    right_leg = _JointAccessor[JointTransform](BodyJointName.RIGHT_LEG)
    right_foot = _JointAccessor[JointTransform](BodyJointName.RIGHT_FOOT)
    right_toes = _JointAccessor[JointTransform](BodyJointName.RIGHT_TOES)
    right_toes_end = _JointAccessor[JointTransform](BodyJointName.RIGHT_TOES_END)
    spine_1 = _JointAccessor[JointTransform](BodyJointName.SPINE_1)
    spine_2 = _JointAccessor[JointTransform](BodyJointName.SPINE_2)
    spine_3 = _JointAccessor[JointTransform](BodyJointName.SPINE_3)
    spine_4 = _JointAccessor[JointTransform](BodyJointName.SPINE_4)
    spine_5 = _JointAccessor[JointTransform](BodyJointName.SPINE_5)
    spine_6 = _JointAccessor[JointTransform](BodyJointName.SPINE_6)
    spine_7 = _JointAccessor[JointTransform](BodyJointName.SPINE_7)
    left_shoulder_1 = _JointAccessor[JointTransform](BodyJointName.LEFT_SHOULDER_1)
    left_arm = _JointAccessor[JointTransform](BodyJointName.LEFT_ARM)
    left_forearm = _JointAccessor[JointTransform](BodyJointName.LEFT_FOREARM)
    left_hand = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND)
    left_hand_index_start = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_INDEX_START)
    left_hand_index_1 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_INDEX_1)
    left_hand_index_2 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_INDEX_2)
    left_hand_index_3 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_INDEX_3)
    left_hand_index_end = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_INDEX_END)
    left_hand_mid_start = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_MID_START)
    left_hand_mid_1 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_MID_1)
    left_hand_mid_2 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_MID_2)
    left_hand_mid_3 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_MID_3)
    left_hand_mid_end = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_MID_END)
    left_hand_pinky_start = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_PINKY_START)
    left_hand_pinky_1 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_PINKY_1)
    left_hand_pinky_2 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_PINKY_2)
    left_hand_pinky_3 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_PINKY_3)
    left_hand_pinky_end = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_PINKY_END)
    left_hand_ring_start = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_RING_START)
    left_hand_ring_1 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_RING_1)
    left_hand_ring_2 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_RING_2)
    left_hand_ring_3 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_RING_3)
    left_hand_ring_end = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_RING_END)
    left_hand_thumb_start = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_THUMB_START)
    left_hand_thumb_1 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_THUMB_1)
    left_hand_thumb_2 = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_THUMB_2)
    left_hand_thumb_end = _JointAccessor[JointTransform](BodyJointName.LEFT_HAND_THUMB_END)
    neck_1 = _JointAccessor[JointTransform](BodyJointName.NECK_1)
    neck_2 = _JointAccessor[JointTransform](BodyJointName.NECK_2)
    neck_3 = _JointAccessor[JointTransform](BodyJointName.NECK_3)
    neck_4 = _JointAccessor[JointTransform](BodyJointName.NECK_4)
    head = _JointAccessor[JointTransform](BodyJointName.HEAD)
    jaw = _JointAccessor[JointTransform](BodyJointName.JAW)
    chin = _JointAccessor[JointTransform](BodyJointName.CHIN)
    left_eye = _JointAccessor[JointTransform](BodyJointName.LEFT_EYE)
    left_eye_lower_lid = _JointAccessor[JointTransform](BodyJointName.LEFT_EYE_LOWER_LID)
    left_eye_upper_lid = _JointAccessor[JointTransform](BodyJointName.LEFT_EYE_UPPER_LID)
    left_eyeball = _JointAccessor[JointTransform](BodyJointName.LEFT_EYEBALL)
    nose = _JointAccessor[JointTransform](BodyJointName.NOSE)
    right_eye = _JointAccessor[JointTransform](BodyJointName.RIGHT_EYE)
    right_eye_lower_lid = _JointAccessor[JointTransform](BodyJointName.RIGHT_EYE_LOWER_LID)
    right_eye_upper_lid = _JointAccessor[JointTransform](BodyJointName.RIGHT_EYE_UPPER_LID)
    right_eyeball = _JointAccessor[JointTransform](BodyJointName.RIGHT_EYEBALL)
    right_shoulder_1 = _JointAccessor[JointTransform](BodyJointName.RIGHT_SHOULDER_1)
    right_arm = _JointAccessor[JointTransform](BodyJointName.RIGHT_ARM)
    right_forearm = _JointAccessor[JointTransform](BodyJointName.RIGHT_FOREARM)
    right_hand = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND)
    right_hand_index_start = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_INDEX_START)
    right_hand_index_1 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_INDEX_1)
    right_hand_index_2 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_INDEX_2)
    right_hand_index_3 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_INDEX_3)
    right_hand_index_end = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_INDEX_END)
    right_hand_mid_start = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_MID_START)
    right_hand_mid_1 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_MID_1)
    right_hand_mid_2 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_MID_2)
    right_hand_mid_3 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_MID_3)
    right_hand_mid_end = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_MID_END)
    right_hand_pinky_start = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_PINKY_START)
    right_hand_pinky_1 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_PINKY_1)
    right_hand_pinky_2 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_PINKY_2)
    right_hand_pinky_3 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_PINKY_3)
    right_hand_pinky_end = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_PINKY_END)
    right_hand_ring_start = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_RING_START)
    right_hand_ring_1 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_RING_1)
    right_hand_ring_2 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_RING_2)
    right_hand_ring_3 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_RING_3)
    right_hand_ring_end = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_RING_END)
    right_hand_thumb_start = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_THUMB_START)
    right_hand_thumb_1 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_THUMB_1)
    right_hand_thumb_2 = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_THUMB_2)
    right_hand_thumb_end = _JointAccessor[JointTransform](BodyJointName.RIGHT_HAND_THUMB_END)


@dataclass
class ARBodyFrame(_Plottable):
    timestamp: float = 0.0
    left_arm_rotation: float = 0.0
    left_arm_angle: float = 0.0
    left_forearm_rotation: float = 0.0
    left_forearm_angle: float = 0.0
    right_arm_rotation: float = 0.0
    right_arm_angle: float = 0.0
    right_forearm_rotation: float = 0.0
    right_forearm_angle: float = 0.0
    right_shoulder_1_pos: Optional[np.ndarray] = None
    right_arm_pos: Optional[np.ndarray] = None
    right_forearm_pos: Optional[np.ndarray] = None
    left_shoulder_1_pos: Optional[np.ndarray] = None
    left_arm_pos: Optional[np.ndarray] = None
    left_forearm_pos: Optional[np.ndarray] = None
    joints: "BodyJoints" = field(default_factory=BodyJoints)
    local_joints: "BodyJoints" = field(default_factory=BodyJoints)
    joint_parents: Dict[str, str] = field(default_factory=dict)
    body_transform: Optional[JointTransform] = None
    tracked_joints: Dict[str, bool] = field(default_factory=dict)
    tracking_state: str = ""
    source_timestamp: float = 0.0
    session_id: str = ""
    estimated_scale: float = 0.0
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.joints, BodyJoints):
            self.joints = BodyJoints(self.joints)
        if not isinstance(self.local_joints, BodyJoints):
            self.local_joints = BodyJoints(self.local_joints)

    @property
    def is_tracking(self) -> bool:
        return self.tracking_state == "tracking" or (not self.tracking_state and bool(self.joints))

    def joint_world_matrix(self, name: str) -> Optional[np.ndarray]:
        if self.body_transform is None or name not in self.joints:
            return None
        return self.body_transform.matrix @ self.joints[name].matrix

    def skeleton(self, space: BodyCoordinateSpace = BodyCoordinateSpace.BODY) -> BodyJointArrays:
        """Export all body transforms and metadata in one coherent array snapshot.

        The first 91 rows follow BodyJointName. Unknown wire joints are appended
        alphabetically. Missing transforms remain NaN; no coordinate fallback
        or synthetic identity transform is used when a space is unavailable.
        """
        space = BodyCoordinateSpace(space)
        names = BODY_JOINT_NAMES + tuple(sorted(
            (set(self.joints) | set(self.local_joints)).difference(BODY_JOINT_NAMES)))
        source = self.local_joints if space == BodyCoordinateSpace.PARENT else self.joints
        positions = np.full((len(names), 3), np.nan, dtype=np.float32)
        rotations = np.full((len(names), 4), np.nan, dtype=np.float32)
        valid = np.zeros(len(names), dtype=bool)
        tracked = np.array([self.tracked_joints.get(name, False) for name in names], dtype=bool)
        tracking_known = np.array([name in self.tracked_joints for name in names], dtype=bool)
        index_by_name = {name: index for index, name in enumerate(names)}
        parents = np.array([index_by_name.get(self.joint_parents.get(name, ""), -1)
                            for name in names], dtype=np.int32)
        anchor_matrix = None
        if space == BodyCoordinateSpace.WORLD and self.body_transform is not None and source:
            anchor_matrix = self.body_transform.matrix
            anchor_q = self.body_transform.rotation / np.linalg.norm(self.body_transform.rotation)
        for index, name in enumerate(names):
            joint = source.get(name)
            if joint is None or (space == BodyCoordinateSpace.WORLD and anchor_matrix is None):
                continue
            if space == BodyCoordinateSpace.WORLD:
                positions[index] = (anchor_matrix @ joint.matrix)[:3, 3]
                q = joint.rotation / np.linalg.norm(joint.rotation)
                rotations[index, :3] = anchor_q[3] * q[:3] + q[3] * anchor_q[:3] + np.cross(anchor_q[:3], q[:3])
                rotations[index, 3] = anchor_q[3] * q[3] - np.dot(anchor_q[:3], q[:3])
            else:
                positions[index] = joint.position
                rotations[index] = joint.rotation
            valid[index] = True
        return BodyJointArrays(names, positions, rotations, valid, tracked,
                               tracking_known, parents, space)


@dataclass
class BodyPoseFrame(_Plottable):
    upper_body: Optional[Message] = None
    json_data: str = ""
    detection_fps: float = 0.0
    frame_id: int = 0
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    @property
    def timestamp(self) -> int:
        return self.upper_body.timestamp if self.upper_body is not None else 0


@dataclass
class AirPodsFrame:
    """Head orientation as an x/y/z/w quaternion in ``rotation``."""
    timestamp: float = 0.0
    rotation: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)


@dataclass
class ClawFrame:
    timestamp: float = 0.0
    angle: float = 0.0
    motor: Optional[Message] = None
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)


@dataclass
class WatchFrame:
    timestamp: float = 0.0
    attitude: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    rotation_rate: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    gravity: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    acceleration: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float32))
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)


@dataclass
class WatchBatch:
    frames: Tuple[WatchFrame, ...] = ()
    batch_timestamp: float = 0.0
    frame_count: int = 0
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    @property
    def timestamp(self) -> float:
        return self.batch_timestamp
