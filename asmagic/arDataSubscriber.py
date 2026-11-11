"""Receive AR frames with receive(); inspect fields on the returned frame."""
from contextlib import contextmanager
from typing import Optional
from ._subscriber import Receiver, DEFAULT_TIMEOUT, tcp_address
from .data_types import ARFrame
from .proto import phone_msg_pb2
from .decoders import ar_frame
from ._ar_receiver import ARReceiverPump

DEFAULT_PORT = 8000
DEFAULT_HWM = 32
DEFAULT_CONFLATE = False


class ARDataSubscriber(Receiver[ARFrame]):
    _message_type = phone_msg_pb2.Phone
    _from_message = staticmethod(ar_frame)
    _raise_decode_errors = True

    def __init__(self, ip: str, port: int = DEFAULT_PORT, hwm: int = DEFAULT_HWM,
                 conflate: bool = DEFAULT_CONFLATE, verbose: bool = False) -> None:
        self._pump = None
        self._ip, self._port = ip, port
        self._address = tcp_address(ip, port)
        if isinstance(hwm, bool) or not isinstance(hwm, int) or hwm < 1:
            raise ValueError("hwm must be a positive integer")
        self._pump = ARReceiverPump(ip, port, hwm, conflate, verbose)

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

    def _read_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[ARFrame]:
        if self._pump is None:
            return None
        return self._pump.get(timeout)

    def close(self) -> None:
        pump = getattr(self, "_pump", None)
        if pump is not None:
            pump.close()


@contextmanager
def connect(ip: str, port: int = DEFAULT_PORT, **kwargs):
    with ARDataSubscriber(ip, port, **kwargs) as subscriber:
        yield subscriber
