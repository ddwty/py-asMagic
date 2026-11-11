"""Legacy combined frames from older App builds. Use FaceDataSubscriber and
HandPoseDataSubscriber independently with current App builds.
"""
from typing import Optional, List
import numpy as np
from ._subscriber import Subscriber, DEFAULT_TIMEOUT
from .tracking_types import FaceAndHandTrackingFrame
from .proto import face_tracking_pb2
from .decoders import face_hand_frame

DEFAULT_PORT = 8102
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class FaceAndHandTrackingDataSubscriber(Subscriber[FaceAndHandTrackingFrame]):
    _message_type = face_tracking_pb2.FaceAndHandTrackingFrame
    _from_message = staticmethod(face_hand_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
