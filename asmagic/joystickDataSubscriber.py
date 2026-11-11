"""Receive joystick_msg.Joystick using the established asmagic subscriber API."""
from ._subscriber import Subscriber
from .data_types import JoystickFrame
from .proto import joystick_msg_pb2
from .decoders import joystick_frame

DEFAULT_PORT = 8020
DEFAULT_HWM = 1
DEFAULT_CONFLATE = True


class JoystickDataSubscriber(Subscriber[JoystickFrame]):
    _message_type = joystick_msg_pb2.Joystick
    _from_message = staticmethod(joystick_frame)

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        super().__init__(ip, port, hwm, conflate, verbose)
