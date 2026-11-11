"""Receive body_pose_msg.BodyPoseMessage using the established asmagic subscriber API."""
from typing import Optional, List
import numpy as np
from ._subscriber import Subscriber, DEFAULT_TIMEOUT
from .tracking_types import BodyPoseFrame
from .proto import body_pose_msg_pb2
from .decoders import body_pose_frame

DEFAULT_PORT = 8010
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class BodyPoseDataSubscriber(Subscriber[BodyPoseFrame]):
    _message_type = body_pose_msg_pb2.BodyPoseMessage
    _from_message = staticmethod(body_pose_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
