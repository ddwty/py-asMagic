"""Receive IMU frames with receive(); inspect fields on the returned frame."""
from ._subscriber import Receiver
from .data_types import IMUFrame
from .proto import imu_msg_pb2
from .decoders import imu_frame

DEFAULT_PORT = 8002
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class IMUDataSubscriber(Receiver[IMUFrame]):
    _message_type = imu_msg_pb2.Imu
    _from_message = staticmethod(imu_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
