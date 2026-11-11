"""Receive Phone.HandPoseFrame on 8101 from Stream or Face and Hand Tracking."""
from typing import Optional, List
import numpy as np
from ._subscriber import Subscriber, DEFAULT_TIMEOUT
from .tracking_types import HandPoseFrame
from .proto import hand_pose_pb2
from .decoders import hand_frame

DEFAULT_PORT = 8101
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class HandPoseDataSubscriber(Subscriber[HandPoseFrame]):
    _message_type = hand_pose_pb2.HandPoseFrame
    _from_message = staticmethod(hand_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
