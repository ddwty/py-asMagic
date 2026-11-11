"""Human-readable body data shared by ARKit and MediaPipe.

Native skeletons retain every node. The common layout names twelve major joints
without synthesizing missing landmarks or joint rotations.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple, Union

import numpy as np
from google.protobuf.message import Message

from .joints import BodyJointName, _JointAccessor
from .tracking_types import JointTransform


class BodyTrackingModel(str, Enum):
    ARKIT = "arkit"
    MEDIAPIPE = "mediapipe"


class BodyTrackingSpace(str, Enum):
    BODY = "body"
    WORLD = "world"
    CAMERA = "camera"
    MODEL = "model"
    IMAGE = "image"
    PARENT = "parent"


class CommonBodyJointName(str, Enum):
    LEFT_SHOULDER = "left_shoulder"
    RIGHT_SHOULDER = "right_shoulder"
    LEFT_ELBOW = "left_elbow"
    RIGHT_ELBOW = "right_elbow"
    LEFT_WRIST = "left_wrist"
    RIGHT_WRIST = "right_wrist"
    LEFT_HIP = "left_hip"
    RIGHT_HIP = "right_hip"
    LEFT_KNEE = "left_knee"
    RIGHT_KNEE = "right_knee"
    LEFT_ANKLE = "left_ankle"
    RIGHT_ANKLE = "right_ankle"

    @property
    def row(self) -> int:
        return COMMON_BODY_JOINT_NAMES.index(self.value)


COMMON_BODY_JOINT_NAMES = tuple(j.value for j in CommonBodyJointName)
MEDIAPIPE_JOINT_NAMES = (
    "nose", "left_eye_inner", "left_eye", "left_eye_outer", "right_eye_inner",
    "right_eye", "right_eye_outer", "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "left_pinky", "right_pinky", "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee", "left_ankle", "right_ankle",
    "left_heel", "right_heel", "left_foot_index", "right_foot_index",
)
MEDIAPIPE_BONES = (
    (0, 1), (1, 2), (2, 3), (3, 7), (0, 4), (4, 5), (5, 6), (6, 8), (9, 10),
    (11, 12), (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
    (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
    (11, 23), (12, 24), (23, 24), (23, 25), (24, 26), (25, 27), (26, 28),
    (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32),
)
COMMON_BODY_BONES = (
    (0, 1), (0, 2), (2, 4), (1, 3), (3, 5), (0, 6), (1, 7), (6, 7),
    (6, 8), (8, 10), (7, 9), (9, 11),
)

# ARKit's arm node is the shoulder, forearm is the elbow, and hand is the wrist.
_ARKIT_ALIASES = {
    side + native + "_joint": side + semantic
    for side in ("left_", "right_")
    for native, semantic in (("arm", "shoulder"), ("forearm", "elbow"), ("hand", "wrist"),
                             ("upLeg", "hip"), ("leg", "knee"), ("foot", "ankle"))
}
ARKIT_JOINT_NAMES_BY_WIRE = {j.value: _ARKIT_ALIASES.get(j.value, j.name.lower()) for j in BodyJointName}
ARKIT_JOINT_NAMES = tuple(ARKIT_JOINT_NAMES_BY_WIRE.values())


@dataclass
class BodyTrackingJoint:
    name: str
    native_name: str
    native_index: Optional[int] = None
    position: Optional[np.ndarray] = None  # body-origin meters
    rotation: Optional[np.ndarray] = None  # x/y/z/w; MediaPipe has none
    world_position: Optional[np.ndarray] = None
    world_rotation: Optional[np.ndarray] = None
    camera_position: Optional[np.ndarray] = None
    model_position: Optional[np.ndarray] = None
    image_position: Optional[np.ndarray] = None
    parent_position: Optional[np.ndarray] = None
    parent_rotation: Optional[np.ndarray] = None
    tracked: Optional[bool] = None
    visibility: Optional[float] = None
    presence: Optional[float] = None
    measured_depth: Optional[float] = None

    def position_in(self, space: Union[BodyTrackingSpace, str] = BodyTrackingSpace.BODY) -> Optional[np.ndarray]:
        space = BodyTrackingSpace(space)
        return getattr(self, "position" if space == BodyTrackingSpace.BODY else space.value + "_position")

    def rotation_in(self, space: Union[BodyTrackingSpace, str] = BodyTrackingSpace.BODY) -> Optional[np.ndarray]:
        space = BodyTrackingSpace(space)
        return getattr(self, "rotation" if space == BodyTrackingSpace.BODY else space.value + "_rotation", None)

    @property
    def usable(self) -> bool:
        """Sender's quality criterion; availability is independent of quality."""
        if self.position is None or not np.isfinite(self.position).all():
            return False
        if self.visibility is not None and self.presence is not None:
            return min(self.visibility, self.presence) >= 0.5
        return self.tracked is True


class BodyTrackingJoints(Dict[str, BodyTrackingJoint]):
    """Named optional attributes and a dictionary containing all received nodes."""
    nose = _JointAccessor[BodyTrackingJoint]("nose")
    left_eye_inner = _JointAccessor[BodyTrackingJoint]("left_eye_inner")
    left_eye = _JointAccessor[BodyTrackingJoint]("left_eye")
    left_eye_outer = _JointAccessor[BodyTrackingJoint]("left_eye_outer")
    right_eye_inner = _JointAccessor[BodyTrackingJoint]("right_eye_inner")
    right_eye = _JointAccessor[BodyTrackingJoint]("right_eye")
    right_eye_outer = _JointAccessor[BodyTrackingJoint]("right_eye_outer")
    left_ear = _JointAccessor[BodyTrackingJoint]("left_ear")
    right_ear = _JointAccessor[BodyTrackingJoint]("right_ear")
    mouth_left = _JointAccessor[BodyTrackingJoint]("mouth_left")
    mouth_right = _JointAccessor[BodyTrackingJoint]("mouth_right")
    left_shoulder = _JointAccessor[BodyTrackingJoint]("left_shoulder")
    right_shoulder = _JointAccessor[BodyTrackingJoint]("right_shoulder")
    left_elbow = _JointAccessor[BodyTrackingJoint]("left_elbow")
    right_elbow = _JointAccessor[BodyTrackingJoint]("right_elbow")
    left_wrist = _JointAccessor[BodyTrackingJoint]("left_wrist")
    right_wrist = _JointAccessor[BodyTrackingJoint]("right_wrist")
    left_pinky = _JointAccessor[BodyTrackingJoint]("left_pinky")
    right_pinky = _JointAccessor[BodyTrackingJoint]("right_pinky")
    left_index = _JointAccessor[BodyTrackingJoint]("left_index")
    right_index = _JointAccessor[BodyTrackingJoint]("right_index")
    left_thumb = _JointAccessor[BodyTrackingJoint]("left_thumb")
    right_thumb = _JointAccessor[BodyTrackingJoint]("right_thumb")
    left_hip = _JointAccessor[BodyTrackingJoint]("left_hip")
    right_hip = _JointAccessor[BodyTrackingJoint]("right_hip")
    left_knee = _JointAccessor[BodyTrackingJoint]("left_knee")
    right_knee = _JointAccessor[BodyTrackingJoint]("right_knee")
    left_ankle = _JointAccessor[BodyTrackingJoint]("left_ankle")
    right_ankle = _JointAccessor[BodyTrackingJoint]("right_ankle")
    left_heel = _JointAccessor[BodyTrackingJoint]("left_heel")
    right_heel = _JointAccessor[BodyTrackingJoint]("right_heel")
    left_foot_index = _JointAccessor[BodyTrackingJoint]("left_foot_index")
    right_foot_index = _JointAccessor[BodyTrackingJoint]("right_foot_index")
    root = _JointAccessor[BodyTrackingJoint]("root")
    hips = _JointAccessor[BodyTrackingJoint]("hips")
    head = _JointAccessor[BodyTrackingJoint]("head")

    left_toes = _JointAccessor[BodyTrackingJoint]("left_toes")
    left_toes_end = _JointAccessor[BodyTrackingJoint]("left_toes_end")
    right_toes = _JointAccessor[BodyTrackingJoint]("right_toes")
    right_toes_end = _JointAccessor[BodyTrackingJoint]("right_toes_end")
    spine_1 = _JointAccessor[BodyTrackingJoint]("spine_1")
    spine_2 = _JointAccessor[BodyTrackingJoint]("spine_2")
    spine_3 = _JointAccessor[BodyTrackingJoint]("spine_3")
    spine_4 = _JointAccessor[BodyTrackingJoint]("spine_4")
    spine_5 = _JointAccessor[BodyTrackingJoint]("spine_5")
    spine_6 = _JointAccessor[BodyTrackingJoint]("spine_6")
    spine_7 = _JointAccessor[BodyTrackingJoint]("spine_7")
    left_shoulder_1 = _JointAccessor[BodyTrackingJoint]("left_shoulder_1")
    left_hand_index_start = _JointAccessor[BodyTrackingJoint]("left_hand_index_start")
    left_hand_index_1 = _JointAccessor[BodyTrackingJoint]("left_hand_index_1")
    left_hand_index_2 = _JointAccessor[BodyTrackingJoint]("left_hand_index_2")
    left_hand_index_3 = _JointAccessor[BodyTrackingJoint]("left_hand_index_3")
    left_hand_index_end = _JointAccessor[BodyTrackingJoint]("left_hand_index_end")
    left_hand_mid_start = _JointAccessor[BodyTrackingJoint]("left_hand_mid_start")
    left_hand_mid_1 = _JointAccessor[BodyTrackingJoint]("left_hand_mid_1")
    left_hand_mid_2 = _JointAccessor[BodyTrackingJoint]("left_hand_mid_2")
    left_hand_mid_3 = _JointAccessor[BodyTrackingJoint]("left_hand_mid_3")
    left_hand_mid_end = _JointAccessor[BodyTrackingJoint]("left_hand_mid_end")
    left_hand_pinky_start = _JointAccessor[BodyTrackingJoint]("left_hand_pinky_start")
    left_hand_pinky_1 = _JointAccessor[BodyTrackingJoint]("left_hand_pinky_1")
    left_hand_pinky_2 = _JointAccessor[BodyTrackingJoint]("left_hand_pinky_2")
    left_hand_pinky_3 = _JointAccessor[BodyTrackingJoint]("left_hand_pinky_3")
    left_hand_pinky_end = _JointAccessor[BodyTrackingJoint]("left_hand_pinky_end")
    left_hand_ring_start = _JointAccessor[BodyTrackingJoint]("left_hand_ring_start")
    left_hand_ring_1 = _JointAccessor[BodyTrackingJoint]("left_hand_ring_1")
    left_hand_ring_2 = _JointAccessor[BodyTrackingJoint]("left_hand_ring_2")
    left_hand_ring_3 = _JointAccessor[BodyTrackingJoint]("left_hand_ring_3")
    left_hand_ring_end = _JointAccessor[BodyTrackingJoint]("left_hand_ring_end")
    left_hand_thumb_start = _JointAccessor[BodyTrackingJoint]("left_hand_thumb_start")
    left_hand_thumb_1 = _JointAccessor[BodyTrackingJoint]("left_hand_thumb_1")
    left_hand_thumb_2 = _JointAccessor[BodyTrackingJoint]("left_hand_thumb_2")
    left_hand_thumb_end = _JointAccessor[BodyTrackingJoint]("left_hand_thumb_end")
    neck_1 = _JointAccessor[BodyTrackingJoint]("neck_1")
    neck_2 = _JointAccessor[BodyTrackingJoint]("neck_2")
    neck_3 = _JointAccessor[BodyTrackingJoint]("neck_3")
    neck_4 = _JointAccessor[BodyTrackingJoint]("neck_4")
    jaw = _JointAccessor[BodyTrackingJoint]("jaw")
    chin = _JointAccessor[BodyTrackingJoint]("chin")
    left_eye_lower_lid = _JointAccessor[BodyTrackingJoint]("left_eye_lower_lid")
    left_eye_upper_lid = _JointAccessor[BodyTrackingJoint]("left_eye_upper_lid")
    left_eyeball = _JointAccessor[BodyTrackingJoint]("left_eyeball")
    right_eye_lower_lid = _JointAccessor[BodyTrackingJoint]("right_eye_lower_lid")
    right_eye_upper_lid = _JointAccessor[BodyTrackingJoint]("right_eye_upper_lid")
    right_eyeball = _JointAccessor[BodyTrackingJoint]("right_eyeball")
    right_shoulder_1 = _JointAccessor[BodyTrackingJoint]("right_shoulder_1")
    right_hand_index_start = _JointAccessor[BodyTrackingJoint]("right_hand_index_start")
    right_hand_index_1 = _JointAccessor[BodyTrackingJoint]("right_hand_index_1")
    right_hand_index_2 = _JointAccessor[BodyTrackingJoint]("right_hand_index_2")
    right_hand_index_3 = _JointAccessor[BodyTrackingJoint]("right_hand_index_3")
    right_hand_index_end = _JointAccessor[BodyTrackingJoint]("right_hand_index_end")
    right_hand_mid_start = _JointAccessor[BodyTrackingJoint]("right_hand_mid_start")
    right_hand_mid_1 = _JointAccessor[BodyTrackingJoint]("right_hand_mid_1")
    right_hand_mid_2 = _JointAccessor[BodyTrackingJoint]("right_hand_mid_2")
    right_hand_mid_3 = _JointAccessor[BodyTrackingJoint]("right_hand_mid_3")
    right_hand_mid_end = _JointAccessor[BodyTrackingJoint]("right_hand_mid_end")
    right_hand_pinky_start = _JointAccessor[BodyTrackingJoint]("right_hand_pinky_start")
    right_hand_pinky_1 = _JointAccessor[BodyTrackingJoint]("right_hand_pinky_1")
    right_hand_pinky_2 = _JointAccessor[BodyTrackingJoint]("right_hand_pinky_2")
    right_hand_pinky_3 = _JointAccessor[BodyTrackingJoint]("right_hand_pinky_3")
    right_hand_pinky_end = _JointAccessor[BodyTrackingJoint]("right_hand_pinky_end")
    right_hand_ring_start = _JointAccessor[BodyTrackingJoint]("right_hand_ring_start")
    right_hand_ring_1 = _JointAccessor[BodyTrackingJoint]("right_hand_ring_1")
    right_hand_ring_2 = _JointAccessor[BodyTrackingJoint]("right_hand_ring_2")
    right_hand_ring_3 = _JointAccessor[BodyTrackingJoint]("right_hand_ring_3")
    right_hand_ring_end = _JointAccessor[BodyTrackingJoint]("right_hand_ring_end")
    right_hand_thumb_start = _JointAccessor[BodyTrackingJoint]("right_hand_thumb_start")
    right_hand_thumb_1 = _JointAccessor[BodyTrackingJoint]("right_hand_thumb_1")
    right_hand_thumb_2 = _JointAccessor[BodyTrackingJoint]("right_hand_thumb_2")
    right_hand_thumb_end = _JointAccessor[BodyTrackingJoint]("right_hand_thumb_end")


@dataclass
class BodyTrackingSkeleton:
    names: Tuple[str, ...]
    positions: np.ndarray  # N x 3 meters, or N x 2 normalized image coordinates
    rotations: np.ndarray  # N x 4, x/y/z/w; NaN when unavailable
    valid: np.ndarray  # finite position present in the requested space
    rotation_valid: np.ndarray
    usable: np.ndarray  # valid and sender quality criterion met
    tracked: np.ndarray
    tracking_known: np.ndarray
    visibility: np.ndarray
    presence: np.ndarray
    native_indices: np.ndarray  # MediaPipe index; -1 when not supplied on wire
    parent_indices: np.ndarray  # -1 without an actual parent transform relationship
    bones: np.ndarray  # M x 2 row pairs; use valid/usable before drawing
    space: BodyTrackingSpace
    layout: str
    skeleton_id: str


@dataclass
class BodyTrackingPerson:
    id: str
    label: int
    model: BodyTrackingModel
    skeleton_id: str
    identity_kind: str  # session_track (MediaPipe) or body_slot (ARKit)
    joints: BodyTrackingJoints
    joint_names: Tuple[str, ...]
    bone_names: Tuple[Tuple[str, str], ...] = ()
    joint_parents: Dict[str, str] = field(default_factory=dict)
    body_transform: Optional[JointTransform] = None
    body_camera_transform: Optional[JointTransform] = None
    identity_ambiguous: Optional[bool] = None
    metric_scale: Optional[float] = None
    fit_rms: Optional[float] = None
    depth_joint_count: Optional[int] = None
    robot_eligible: Optional[bool] = None
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.model = BodyTrackingModel(self.model)
        self.joint_names = tuple(self.joint_names)
        if not isinstance(self.joints, BodyTrackingJoints):
            self.joints = BodyTrackingJoints(self.joints)

    @property
    def has_world_coordinates(self) -> bool:
        return any(j.world_position is not None for j in self.joints.values())

    def skeleton(self, space: Union[BodyTrackingSpace, str] = BodyTrackingSpace.BODY,
                 *, layout: str = "native") -> BodyTrackingSkeleton:
        """Export a fresh snapshot; never filter rows or fall back to another space."""
        space = BodyTrackingSpace(space)
        if layout not in ("native", "common"):
            raise ValueError("layout must be 'native' or 'common'")
        names = self.joint_names if layout == "native" else COMMON_BODY_JOINT_NAMES
        n = len(names)
        positions = np.full((n, 2 if space == BodyTrackingSpace.IMAGE else 3), np.nan, dtype=np.float32)
        rotations = np.full((n, 4), np.nan, dtype=np.float32)
        valid = np.zeros(n, dtype=bool)
        rotation_valid = np.zeros(n, dtype=bool)
        usable = np.zeros(n, dtype=bool)
        tracked = np.zeros(n, dtype=bool)
        tracking_known = np.zeros(n, dtype=bool)
        visibility = np.full(n, np.nan, dtype=np.float32)
        presence = np.full(n, np.nan, dtype=np.float32)
        native_indices = np.full(n, -1, dtype=np.int32)
        index = {name: row for row, name in enumerate(names)}
        parents = np.array([index.get(self.joint_parents.get(name, ""), -1) for name in names], dtype=np.int32)
        edges = (tuple((names[a], names[b]) for a, b in COMMON_BODY_BONES)
                 if layout == "common" else self.bone_names)
        bones = np.array([(index[a], index[b]) for a, b in edges if a in index and b in index],
                         dtype=np.int32).reshape(-1, 2)
        for row, name in enumerate(names):
            joint = self.joints.get(name)
            if joint is None:
                continue
            p, q = joint.position_in(space), joint.rotation_in(space)
            if p is not None and np.isfinite(p).all():
                positions[row], valid[row] = p, True
                usable[row] = joint.usable
            if q is not None and np.isfinite(q).all() and np.linalg.norm(q) > 0:
                rotations[row], rotation_valid[row] = q, True
            if joint.tracked is not None:
                tracked[row], tracking_known[row] = joint.tracked, True
            if joint.visibility is not None:
                visibility[row] = joint.visibility
            if joint.presence is not None:
                presence[row] = joint.presence
            if joint.native_index is not None:
                native_indices[row] = joint.native_index
        return BodyTrackingSkeleton(names, positions, rotations, valid, rotation_valid, usable,
                                    tracked, tracking_known, visibility, presence, native_indices,
                                    parents, bones, space, layout, self.skeleton_id)


@dataclass
class BodyTrackingFrame:
    model: BodyTrackingModel
    timestamp: float
    source_timestamp: float
    session_id: str
    world_frame_id: str
    tracking_state: str
    people: Tuple[BodyTrackingPerson, ...] = ()
    selected_person_id: Optional[str] = None
    model_name: str = ""
    schema_version: Optional[int] = None
    sequence: Optional[int] = None
    camera_world_transform: Optional[np.ndarray] = None
    camera_intrinsics: Optional[np.ndarray] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    camera_tracking: Optional[str] = None
    has_scene_depth: Optional[bool] = None
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.model = BodyTrackingModel(self.model)
        self.people = tuple(self.people)

    @property
    def person_count(self) -> int:
        return len(self.people)

    @property
    def is_tracking(self) -> bool:
        return bool(self.people)

    def person(self, person_id: str) -> Optional[BodyTrackingPerson]:
        """Look up an ID in this frame only; a lost person returns None."""
        return next((person for person in self.people if person.id == person_id), None)

    @property
    def selected_person(self) -> Optional[BodyTrackingPerson]:
        return self.person(self.selected_person_id) if self.selected_person_id is not None else None

    @classmethod
    def from_bytes(cls, payload: bytes, *, model: Union[BodyTrackingModel, str]) -> "BodyTrackingFrame":
        """Decode a saved native frame without opening a socket."""
        from ._body_tracking_decoder import decode_body_tracking
        return decode_body_tracking(payload, BodyTrackingModel(model))

    def plot(self, enabled: bool = True, plotter=None, **options):
        from .plotting import plot_tracking
        return plot_tracking(self, enabled=enabled, plotter=plotter, **options)
