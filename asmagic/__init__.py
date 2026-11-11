"""Receive asMagic protobuf streams with receive(), iteration and context managers."""
__version__ = "1.0.2"
__author__ = "ASMagic Team"

from .arDataSubscriber import ARDataSubscriber, connect
from .cameraDataSubscriber import CameraDataSubscriber
from .camera_types import CameraFrame
from .imuDataSubscriber import IMUDataSubscriber
from .joystickDataSubscriber import JoystickDataSubscriber
from .airPodsDataSubscriber import AirPodsDataSubscriber
from .bodyPoseDataSubscriber import BodyPoseDataSubscriber
from .arBodyDataSubscriber import ARBodyDataSubscriber
from .bodyTrackingDataSubscriber import BodyTrackingDataSubscriber
from .body_tracking import (BodyTrackingModel, BodyTrackingSpace, BodyTrackingFrame,
                            BodyTrackingPerson, BodyTrackingJoint, BodyTrackingJoints,
                            BodyTrackingSkeleton, CommonBodyJointName, COMMON_BODY_JOINT_NAMES,
                            ARKIT_JOINT_NAMES, MEDIAPIPE_JOINT_NAMES)
from .handPoseDataSubscriber import HandPoseDataSubscriber
from .faceDataSubscriber import FaceDataSubscriber
from .faceAndHandTrackingDataSubscriber import FaceAndHandTrackingDataSubscriber
from .clawDataSubscriber import ClawDataSubscriber
from .protobufSubscriber import ProtobufSubscriber, MagiClawDataSubscriber, LegacyWatchDataSubscriber
from .watchIMUReceiver import WatchIMUReceiver
from .data_types import ARFrame, IMUFrame, JoystickFrame
from .joystick_controls import JoystickButtons
from .tracking_types import (AirPodsFrame, ARBodyFrame, BodyPoseFrame, ClawFrame,
                             FaceFrame, FaceAndHandTrackingFrame, FaceLandmark, FaceImageLocation,
                             HandPoseFrame, Hand, HandJoint, HandFinger, HandThumb, HandJoints, BodyJoints, JointTransform,
                             WatchFrame, WatchBatch)
from .joints import (BodyJointName, HandJointName, HandSide, BodyCoordinateSpace,
                     BodyJointArrays, HandJointArrays, BODY_JOINT_NAMES, HAND_JOINT_NAMES)
from .streams import STREAMS, StreamInfo, subscribe
from .plotting import TrackingPlotter, HandTrackingWindow, plot_tracking

__all__ = [
    "CameraDataSubscriber", "CameraFrame", "ARDataSubscriber", "IMUDataSubscriber", "JoystickDataSubscriber", "connect",
    "AirPodsDataSubscriber", "BodyPoseDataSubscriber", "ARBodyDataSubscriber",
    "BodyTrackingDataSubscriber", "BodyTrackingModel", "BodyTrackingSpace", "BodyTrackingFrame",
    "BodyTrackingPerson", "BodyTrackingJoint", "BodyTrackingJoints", "BodyTrackingSkeleton",
    "CommonBodyJointName", "COMMON_BODY_JOINT_NAMES", "ARKIT_JOINT_NAMES", "MEDIAPIPE_JOINT_NAMES",
    "HandPoseDataSubscriber", "FaceDataSubscriber", "FaceAndHandTrackingDataSubscriber", "ClawDataSubscriber",
    "ProtobufSubscriber", "MagiClawDataSubscriber", "LegacyWatchDataSubscriber", "WatchIMUReceiver",
    "ARFrame", "IMUFrame", "JoystickFrame", "JoystickButtons", "AirPodsFrame", "ARBodyFrame", "BodyPoseFrame",
    "ClawFrame", "FaceFrame", "FaceAndHandTrackingFrame", "FaceLandmark", "FaceImageLocation",
    "HandPoseFrame", "Hand", "HandJoint", "HandFinger", "HandThumb", "HandSide", "JointTransform", "WatchFrame", "WatchBatch",
    "HandJoints", "BodyJoints", "BodyJointName", "HandJointName", "BodyCoordinateSpace",
    "BodyJointArrays", "HandJointArrays", "BODY_JOINT_NAMES", "HAND_JOINT_NAMES",
    "STREAMS", "StreamInfo", "subscribe", "__version__",
    "TrackingPlotter", "HandTrackingWindow", "plot_tracking",
]
