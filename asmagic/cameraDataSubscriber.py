"""Receive camera-only RGB images on the ordinary-camera stream."""
from typing import Optional

from ._ar_receiver import ARReceiverPump
from ._subscriber import Receiver, Subscriber, DEFAULT_TIMEOUT, tcp_address
from .camera_types import CameraFrame
from .decoders import camera_frame
from .proto import phone_msg_pb2

DEFAULT_PORT = 8105
DEFAULT_HWM = 32
DEFAULT_CONFLATE = False


class _CameraWireSubscriber(Subscriber):
    _message_type = phone_msg_pb2.Phone
    _from_message = staticmethod(camera_frame)
    _raise_decode_errors = True
    _decode_error_label = "camera data"


class CameraDataSubscriber(Receiver[CameraFrame]):
    """Receive CameraFrame objects with ARDataSubscriber-compatible RGB fields."""

    _message_type = phone_msg_pb2.Phone
    _from_message = staticmethod(camera_frame)
    _raise_decode_errors = True

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        self._pump = None
        self._ip, self._port = ip, port
        self._address = tcp_address(ip, port)
        if isinstance(hwm, bool) or not isinstance(hwm, int) or hwm < 1:
            raise ValueError("hwm must be a positive integer")
        self._pump = ARReceiverPump(
            ip, port, hwm, conflate, verbose,
            subscriber_type=_CameraWireSubscriber, thread_name="asmagic-camera-receiver")

    @property
    def _connected(self):
        return self._pump is not None and self._pump.active

    @property
    def received_frames(self):
        return self._pump.received_frames if self._pump is not None else 0

    @property
    def last_received_at(self):
        return self._pump.last_received_at if self._pump is not None else None

    @property
    def last_error(self):
        return self._pump.last_error if self._pump is not None else None

    def _read_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[CameraFrame]:
        if self._pump is None:
            return None
        return self._pump.get(timeout)

    def close(self) -> None:
        pump = getattr(self, "_pump", None)
        if pump is not None:
            pump.close()
