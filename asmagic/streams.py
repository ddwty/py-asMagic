"""Named stream selection and source-backed default ports."""
from dataclasses import dataclass
from types import MappingProxyType

from .arDataSubscriber import ARDataSubscriber
from .cameraDataSubscriber import CameraDataSubscriber
from .imuDataSubscriber import IMUDataSubscriber
from .joystickDataSubscriber import JoystickDataSubscriber
from .airPodsDataSubscriber import AirPodsDataSubscriber
from .bodyPoseDataSubscriber import BodyPoseDataSubscriber
from .arBodyDataSubscriber import ARBodyDataSubscriber
from .bodyTrackingDataSubscriber import BodyTrackingDataSubscriber
from .handPoseDataSubscriber import HandPoseDataSubscriber
from .faceDataSubscriber import FaceDataSubscriber
from .faceAndHandTrackingDataSubscriber import FaceAndHandTrackingDataSubscriber
from .clawDataSubscriber import ClawDataSubscriber


@dataclass(frozen=True)
class StreamInfo:
    subscriber: type
    port: int
    message: str
    feature: str


STREAMS = MappingProxyType({
    "camera": StreamInfo(CameraDataSubscriber, 8105, "Phone.Phone", "Stream > Camera > Send camera"),
    "ar": StreamInfo(ARDataSubscriber, 8000, "Phone.Phone", "Stream or Robot control"),
    "airpods": StreamInfo(AirPodsDataSubscriber, 8001, "Airpods.Airpods", "AirPods motion"),
    "imu": StreamInfo(IMUDataSubscriber, 8002, "Imu.Imu", "IMU"),
    "body_pose": StreamInfo(BodyPoseDataSubscriber, 8010, "BodyPose.BodyPoseMessage", "2D upper-body tracking"),
    "joystick": StreamInfo(JoystickDataSubscriber, 8020, "Joystick.Joystick", "Controller"),
    "ar_body": StreamInfo(ARBodyDataSubscriber, 8100, "Armpose.Armpose", "Body tracking"),
    "hand": StreamInfo(HandPoseDataSubscriber, 8101, "Phone.HandPoseFrame", "Stream or Face and Hand Tracking hand output"),
    "face": StreamInfo(FaceDataSubscriber, 8102, "Phone.FaceTrackingFrame", "Face and Hand Tracking face output"),
    "claw": StreamInfo(ClawDataSubscriber, 5301, "Claw.Claw", "Robot gripper; second gripper uses 5401"),
})


def subscribe(stream: str, ip: str, **kwargs):
    """Optional factory; the existing explicit subscriber classes remain primary."""
    if stream == "body":
        return BodyTrackingDataSubscriber(ip, **kwargs)
    if stream == "face_hand":
        # Legacy factory name; excluded from the current output inventory.
        return FaceAndHandTrackingDataSubscriber(ip, **kwargs)
    try:
        info = STREAMS[stream]
    except KeyError as error:
        raise ValueError("Unknown stream '{}'; choose {}".format(stream, ", ".join(STREAMS) + ", body")) from error
    return info.subscriber(ip, **kwargs)
