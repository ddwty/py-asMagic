"""Receive armpose_msg.Armpose using the established asmagic subscriber API."""
from typing import Optional, List
import numpy as np
from ._subscriber import Subscriber, DEFAULT_TIMEOUT
from .tracking_types import ARBodyFrame
from .proto import armpose_msg_pb2
from .decoders import ar_body_frame

DEFAULT_PORT = 8100
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class ARBodyDataSubscriber(Subscriber[ARBodyFrame]):
    _message_type = armpose_msg_pb2.Armpose
    _from_message = staticmethod(ar_body_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
