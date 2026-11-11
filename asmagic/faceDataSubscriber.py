"""Receive face-only Phone.FaceTrackingFrame on TCP 8102."""
from ._subscriber import Subscriber
from .tracking_types import FaceFrame
from .proto import face_tracking_pb2
from .decoders import face_frame

DEFAULT_PORT = 8102
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class FaceDataSubscriber(Subscriber[FaceFrame]):
    _message_type = face_tracking_pb2.FaceTrackingFrame
    _from_message = staticmethod(face_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
