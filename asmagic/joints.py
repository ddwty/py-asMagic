"""Typed joint names and stable array exports; wire dictionaries remain compatible.

Body order follows BodyRecordingManager.orderedJointNames in the app;
hand order follows HandPoseJointName.allCases. The order is an SDK contract,
independent of protobuf map iteration and missing observations.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Mapping, Optional, Tuple, TypeVar, overload

import numpy as np

from .geometry import pose_matrix


class BodyJointName(str, Enum):
    """Protocol joint names, in stable array row order."""
    ROOT = 'root'
    HIPS = 'hips_joint'
    LEFT_UP_LEG = 'left_upLeg_joint'
    LEFT_LEG = 'left_leg_joint'
    LEFT_FOOT = 'left_foot_joint'
    LEFT_TOES = 'left_toes_joint'
    LEFT_TOES_END = 'left_toesEnd_joint'
    RIGHT_UP_LEG = 'right_upLeg_joint'
    RIGHT_LEG = 'right_leg_joint'
    RIGHT_FOOT = 'right_foot_joint'
    RIGHT_TOES = 'right_toes_joint'
    RIGHT_TOES_END = 'right_toesEnd_joint'
    SPINE_1 = 'spine_1_joint'
    SPINE_2 = 'spine_2_joint'
    SPINE_3 = 'spine_3_joint'
    SPINE_4 = 'spine_4_joint'
    SPINE_5 = 'spine_5_joint'
    SPINE_6 = 'spine_6_joint'
    SPINE_7 = 'spine_7_joint'
    LEFT_SHOULDER_1 = 'left_shoulder_1_joint'
    LEFT_ARM = 'left_arm_joint'
    LEFT_FOREARM = 'left_forearm_joint'
    LEFT_HAND = 'left_hand_joint'
    LEFT_HAND_INDEX_START = 'left_handIndexStart_joint'
    LEFT_HAND_INDEX_1 = 'left_handIndex_1_joint'
    LEFT_HAND_INDEX_2 = 'left_handIndex_2_joint'
    LEFT_HAND_INDEX_3 = 'left_handIndex_3_joint'
    LEFT_HAND_INDEX_END = 'left_handIndexEnd_joint'
    LEFT_HAND_MID_START = 'left_handMidStart_joint'
    LEFT_HAND_MID_1 = 'left_handMid_1_joint'
    LEFT_HAND_MID_2 = 'left_handMid_2_joint'
    LEFT_HAND_MID_3 = 'left_handMid_3_joint'
    LEFT_HAND_MID_END = 'left_handMidEnd_joint'
    LEFT_HAND_PINKY_START = 'left_handPinkyStart_joint'
    LEFT_HAND_PINKY_1 = 'left_handPinky_1_joint'
    LEFT_HAND_PINKY_2 = 'left_handPinky_2_joint'
    LEFT_HAND_PINKY_3 = 'left_handPinky_3_joint'
    LEFT_HAND_PINKY_END = 'left_handPinkyEnd_joint'
    LEFT_HAND_RING_START = 'left_handRingStart_joint'
    LEFT_HAND_RING_1 = 'left_handRing_1_joint'
    LEFT_HAND_RING_2 = 'left_handRing_2_joint'
    LEFT_HAND_RING_3 = 'left_handRing_3_joint'
    LEFT_HAND_RING_END = 'left_handRingEnd_joint'
    LEFT_HAND_THUMB_START = 'left_handThumbStart_joint'
    LEFT_HAND_THUMB_1 = 'left_handThumb_1_joint'
    LEFT_HAND_THUMB_2 = 'left_handThumb_2_joint'
    LEFT_HAND_THUMB_END = 'left_handThumbEnd_joint'
    NECK_1 = 'neck_1_joint'
    NECK_2 = 'neck_2_joint'
    NECK_3 = 'neck_3_joint'
    NECK_4 = 'neck_4_joint'
    HEAD = 'head_joint'
    JAW = 'jaw_joint'
    CHIN = 'chin_joint'
    LEFT_EYE = 'left_eye_joint'
    LEFT_EYE_LOWER_LID = 'left_eyeLowerLid_joint'
    LEFT_EYE_UPPER_LID = 'left_eyeUpperLid_joint'
    LEFT_EYEBALL = 'left_eyeball_joint'
    NOSE = 'nose_joint'
    RIGHT_EYE = 'right_eye_joint'
    RIGHT_EYE_LOWER_LID = 'right_eyeLowerLid_joint'
    RIGHT_EYE_UPPER_LID = 'right_eyeUpperLid_joint'
    RIGHT_EYEBALL = 'right_eyeball_joint'
    RIGHT_SHOULDER_1 = 'right_shoulder_1_joint'
    RIGHT_ARM = 'right_arm_joint'
    RIGHT_FOREARM = 'right_forearm_joint'
    RIGHT_HAND = 'right_hand_joint'
    RIGHT_HAND_INDEX_START = 'right_handIndexStart_joint'
    RIGHT_HAND_INDEX_1 = 'right_handIndex_1_joint'
    RIGHT_HAND_INDEX_2 = 'right_handIndex_2_joint'
    RIGHT_HAND_INDEX_3 = 'right_handIndex_3_joint'
    RIGHT_HAND_INDEX_END = 'right_handIndexEnd_joint'
    RIGHT_HAND_MID_START = 'right_handMidStart_joint'
    RIGHT_HAND_MID_1 = 'right_handMid_1_joint'
    RIGHT_HAND_MID_2 = 'right_handMid_2_joint'
    RIGHT_HAND_MID_3 = 'right_handMid_3_joint'
    RIGHT_HAND_MID_END = 'right_handMidEnd_joint'
    RIGHT_HAND_PINKY_START = 'right_handPinkyStart_joint'
    RIGHT_HAND_PINKY_1 = 'right_handPinky_1_joint'
    RIGHT_HAND_PINKY_2 = 'right_handPinky_2_joint'
    RIGHT_HAND_PINKY_3 = 'right_handPinky_3_joint'
    RIGHT_HAND_PINKY_END = 'right_handPinkyEnd_joint'
    RIGHT_HAND_RING_START = 'right_handRingStart_joint'
    RIGHT_HAND_RING_1 = 'right_handRing_1_joint'
    RIGHT_HAND_RING_2 = 'right_handRing_2_joint'
    RIGHT_HAND_RING_3 = 'right_handRing_3_joint'
    RIGHT_HAND_RING_END = 'right_handRingEnd_joint'
    RIGHT_HAND_THUMB_START = 'right_handThumbStart_joint'
    RIGHT_HAND_THUMB_1 = 'right_handThumb_1_joint'
    RIGHT_HAND_THUMB_2 = 'right_handThumb_2_joint'
    RIGHT_HAND_THUMB_END = 'right_handThumbEnd_joint'

    @property
    def row(self) -> int:
        """Row index in the default bulk array export."""
        return BODY_JOINT_NAMES.index(self.value)


class HandSide(str, Enum):
    """The tracked person's anatomical side, independent of screen position."""
    LEFT = "left"
    RIGHT = "right"
    UNKNOWN = "unknown"


class HandJointName(str, Enum):
    """Protocol joint names, in stable array row order."""
    WRIST = 'wrist'
    THUMB_CMC = 'thumb_cmc'
    THUMB_MP = 'thumb_mp'
    THUMB_IP = 'thumb_ip'
    THUMB_TIP = 'thumb_tip'
    INDEX_MCP = 'index_mcp'
    INDEX_PIP = 'index_pip'
    INDEX_DIP = 'index_dip'
    INDEX_TIP = 'index_tip'
    MIDDLE_MCP = 'middle_mcp'
    MIDDLE_PIP = 'middle_pip'
    MIDDLE_DIP = 'middle_dip'
    MIDDLE_TIP = 'middle_tip'
    RING_MCP = 'ring_mcp'
    RING_PIP = 'ring_pip'
    RING_DIP = 'ring_dip'
    RING_TIP = 'ring_tip'
    LITTLE_MCP = 'little_mcp'
    LITTLE_PIP = 'little_pip'
    LITTLE_DIP = 'little_dip'
    LITTLE_TIP = 'little_tip'

    @property
    def row(self) -> int:
        """Row index in the default bulk array export."""
        return HAND_JOINT_NAMES.index(self.value)


BODY_JOINT_NAMES = tuple(joint.value for joint in BodyJointName)
HAND_JOINT_NAMES = tuple(joint.value for joint in HandJointName)


class BodyCoordinateSpace(str, Enum):
    BODY = "body"
    PARENT = "parent"
    WORLD = "world"


_JointT = TypeVar("_JointT")


class _JointAccessor(Generic[_JointT]):
    """Statically declared descriptor, so IDEs see the optional joint type."""
    def __init__(self, name: str) -> None:
        self.name = name

    @overload
    def __get__(self, instance: None, owner: Optional[type] = None) -> "_JointAccessor[_JointT]": ...

    @overload
    def __get__(self, instance: Mapping[str, _JointT], owner: Optional[type] = None) -> Optional[_JointT]: ...

    def __get__(self, instance, owner=None):
        return self if instance is None else instance.get(self.name)

    def __set__(self, instance, value) -> None:
        raise AttributeError("Joint attributes are read-only; update the dictionary instead")


@dataclass
class BodyJointArrays:
    """All joints: stable rows, NaN for missing transforms, masks for presence/tracking."""
    names: Tuple[str, ...]
    positions: np.ndarray           # N x 3, float32, meters
    rotations: np.ndarray           # N x 4, float32, x/y/z/w
    valid: np.ndarray               # N, bool, a transform is present in this space
    tracked: np.ndarray             # N, bool, directly tracked according to the sender
    tracking_known: np.ndarray      # N, bool, sender supplied a tracking flag
    parent_indices: np.ndarray      # N, int32, -1 for absent/unknown parents
    space: BodyCoordinateSpace

    @property
    def matrices(self) -> np.ndarray:
        result = np.full((len(self.names), 4, 4), np.nan, dtype=np.float32)
        for index in np.flatnonzero(self.valid):
            result[index] = pose_matrix(np.concatenate((self.positions[index], self.rotations[index])))
        return result


@dataclass
class HandJointArrays:
    """All hand joints: raw normalized points, stable rows, NaN for missing joints."""
    names: Tuple[str, ...]
    points: np.ndarray              # N x 2, float32
    confidences: np.ndarray         # N, float32
    valid: np.ndarray               # N, bool, joint was present
