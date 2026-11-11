"""Receive claw_msg.Claw using the established asmagic subscriber API."""
from typing import Optional, List
import numpy as np
from ._subscriber import Subscriber, DEFAULT_TIMEOUT
from .tracking_types import ClawFrame
from .proto import claw_msg_pb2
from .decoders import claw_frame

DEFAULT_PORT = 5301
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class ClawDataSubscriber(Subscriber[ClawFrame]):
    _message_type = claw_msg_pb2.Claw
    _from_message = staticmethod(claw_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
