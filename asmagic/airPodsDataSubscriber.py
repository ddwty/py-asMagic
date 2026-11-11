"""Receive airpods_msg.Airpods using the established asmagic subscriber API."""
from typing import Optional, List
import numpy as np
from ._subscriber import Subscriber, DEFAULT_TIMEOUT
from .tracking_types import AirPodsFrame
from .proto import airpods_msg_pb2
from .decoders import airpods_frame

DEFAULT_PORT = 8001
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class AirPodsDataSubscriber(Subscriber[AirPodsFrame]):
    _message_type = airpods_msg_pb2.Airpods
    _from_message = staticmethod(airpods_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
