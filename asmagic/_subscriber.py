"""Shared one-part ZeroMQ receive loop; socket use stays on the caller's thread."""
import logging
import math
import time
from typing import Callable, Generic, Optional, TypeVar, overload

import zmq
from google.protobuf.message import DecodeError, Message

T = TypeVar("T")
DEFAULT_TIMEOUT = 1000  # milliseconds, preserved from 0.1.4
LOGGER = logging.getLogger("asmagic")


def validate_timeout(timeout: int) -> None:
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < -1:
        raise ValueError("timeout must be an integer >= -1, in milliseconds")


def _receive_frame(get_frame: Callable[[int], Optional[T]], is_open: Callable[[], bool],
                   timeout: Optional[int]) -> Optional[T]:
    """Wait for valid data within one timeout budget, shared by TCP and Watch."""
    if timeout is not None:
        validate_timeout(timeout)
    deadline = None if timeout is None or timeout == -1 else time.monotonic() + timeout / 1000.0
    while is_open():
        wait = DEFAULT_TIMEOUT if deadline is None else min(
            DEFAULT_TIMEOUT, max(0, math.ceil((deadline - time.monotonic()) * 1000)))
        frame = get_frame(wait)
        if frame is not None:
            return frame
        if not is_open():
            break
        if deadline is not None and time.monotonic() >= deadline:
            return None
    raise StopIteration


def tcp_address(ip: str, port: int) -> str:
    if not isinstance(ip, str) or not ip.strip() or "://" in ip:
        raise ValueError("ip must be a host name or IP address, without a transport prefix")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("port must be an integer from 1 to 65535")
    host = ip.strip()
    if ":" in host and not host.startswith("["):
        host = "[" + host + "]"
    return "tcp://{}:{}".format(host, port)


class Receiver(Generic[T]):
    """Common receive, iteration, stream and deterministic cleanup."""
    _message_type = None
    _raise_decode_errors = False
    _decode_error_label = "AR data"

    def __init__(self, ip: str, port: int, hwm: int = 1,
                 conflate: bool = True, verbose: bool = False) -> None:
        self._connected = False
        self._context = None
        self._socket = None
        self._poller = None
        self._ip, self._port = ip, port
        self._address = tcp_address(ip, port)
        if isinstance(hwm, bool) or not isinstance(hwm, int) or hwm < 1:
            raise ValueError("hwm must be a positive integer")
        self.last_error = None  # type: Optional[str]
        self.received_frames = 0
        self.last_received_at = None  # type: Optional[float]
        self._verbose = verbose
        try:
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.SUB)
            self._subscriber = self._socket  # retained internal name used by old modules
            self._socket.setsockopt(zmq.LINGER, 0)
            self._socket.setsockopt(zmq.IPV6, 1)
            self._socket.set_hwm(hwm)
            self._socket.setsockopt(zmq.CONFLATE, int(conflate))
            self._socket.setsockopt(zmq.SUBSCRIBE, b"")
            self._socket.connect(self._address)
            self._poller = zmq.Poller()
            self._poller.register(self._socket, zmq.POLLIN)
            self._connected = True
        except Exception:
            self.close()
            raise
        if verbose:
            print("[{}] Subscribed to {}".format(type(self).__name__, self.address))

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    @property
    def address(self) -> str:
        return self._address

    @property
    def is_connected(self) -> bool:
        """True while the local subscription is open, not proof of device delivery."""
        return self._connected

    @property
    def has_received_data(self) -> bool:
        return self.received_frames > 0

    @classmethod
    def decode(cls, payload: bytes) -> T:
        """Decode a saved wire message without opening a socket."""
        message = cls._message_type()
        message.ParseFromString(payload)
        return cls._from_message(message)

    @staticmethod
    def _from_message(message):
        return message

    def _read_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[T]:
        """Receive one fresh frame; timeout is milliseconds, 0 polls, -1 waits."""
        validate_timeout(timeout)
        if not self._connected:
            return None
        events = dict(self._poller.poll(timeout))
        if not events.get(self._socket, 0) & zmq.POLLIN:
            return None
        try:
            payload = self._socket.recv(zmq.DONTWAIT)
            frame = self.decode(payload)
        except zmq.Again:
            return None
        except (DecodeError, ValueError) as error:
            self.last_error = str(error)
            if self._verbose:
                LOGGER.warning("Unable to decode %s: %s", self.address, error)
            if self._raise_decode_errors:
                raise RuntimeError("Failed to receive {}: {}".format(self._decode_error_label, error)) from error
            return None
        self.received_frames += 1
        self.last_received_at = time.monotonic()
        self.last_error = None
        return frame

    @overload
    def receive(self, timeout: None = None) -> T: ...

    @overload
    def receive(self, timeout: int) -> Optional[T]: ...

    def receive(self, timeout: Optional[int] = None) -> Optional[T]:
        """Receive one valid frame, optionally within a timeout in milliseconds.

        No argument (or None/-1) waits until valid data arrives. A nonnegative
        timeout returns None if no valid frame arrives; 0 polls immediately.
        Closure raises StopIteration in both modes. Decode errors that were
        recoverable are skipped within the same budget; AR errors still raise.
        """
        return _receive_frame(self._read_frame, lambda: self._connected, timeout)

    def stream(self, timeout: int = DEFAULT_TIMEOUT, on_frame: Optional[Callable] = None,
               *, plot: bool = False, plot_options: Optional[dict] = None):
        validate_timeout(timeout)
        plotter = None
        if plot:
            supported = ("Armpose.Armpose", "asmagic.body.v1.MultiPersonPoseFrame", "BodyPose.BodyPoseMessage", "Phone.HandPoseFrame", "Phone.FaceTrackingFrame", "Phone.FaceAndHandTrackingFrame")
            if self._message_type.DESCRIPTOR.full_name not in supported:
                raise ValueError("此通道没有人体/手部绘图；plot=True 仅用于跟踪数据")
            from .plotting import TrackingPlotter, _pyplot
            _pyplot()  # Report an incomplete installation before waiting for a device.
            plotter = TrackingPlotter(**(plot_options or {}))
        try:
            while self._connected and (plotter is None or plotter.is_open):
                # Frequent polling keeps a plot window responsive; receive timeout
                # does not cap source FPS or change socket queue behavior.
                wait = min(timeout, 50) if plot and timeout >= 0 else (50 if plot else timeout)
                try:
                    frame = self.receive(timeout=wait)
                except StopIteration:
                    return
                if frame is not None:
                    if plotter is not None:
                        plotter.update(frame)
                    if on_frame is not None:
                        on_frame(frame)
                    yield frame
                elif plotter is not None:
                    plotter.idle()
        finally:
            if plotter is not None:
                plotter.close()

    def __iter__(self):
        return self

    def __next__(self) -> T:
        return self.receive()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        self._connected = False
        socket = getattr(self, "_socket", None)
        context = getattr(self, "_context", None)
        if socket is not None:
            if self._poller is not None:
                self._poller.unregister(socket)
            socket.close(linger=0)
            self._socket = self._subscriber = None
        if context is not None:
            context.term()
            self._context = None

    def __del__(self):
        self.close()


class Subscriber(Receiver[T]):
    """Compatibility reads for subscribers that retain the legacy interface."""

    def get_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[T]:
        return super()._read_frame(timeout)

    def get(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[T]:
        return self.get_frame(timeout)

    def _read_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[T]:
        return self.get_frame(timeout)
