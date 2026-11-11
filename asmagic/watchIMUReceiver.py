"""HTTP receiver for the Watch companion's POST /imu protobuf batches."""
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import time
from typing import Optional, overload

from google.protobuf.message import DecodeError
from .proto import watch_batch_msg_pb2, watch_msg_pb2
from .decoders import watch_batch, watch_frame
from .tracking_types import WatchBatch
from ._subscriber import DEFAULT_TIMEOUT, _receive_frame, validate_timeout


class WatchIMUReceiver:
    """Listen locally and expose the same receive/iteration/context-manager pattern.

    host is this computer's bind address. Set the Watch's server address to this
    computer, not to the Watch IP. conflate drops old batches, never samples inside
    a batch. payload_format explicitly selects batch, single, or legacy.
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8002, conflate: bool = True,
                 max_batches: int = 32, payload_format: str = "batch", verbose: bool = False):
        if payload_format not in ("batch", "single", "legacy"):
            raise ValueError("payload_format must be batch, single or legacy")
        if isinstance(port, bool) or not isinstance(port, int) or not 0 <= port <= 65535:
            raise ValueError("port must be an integer from 0 to 65535")
        if isinstance(max_batches, bool) or not isinstance(max_batches, int) or max_batches < 1:
            raise ValueError("max_batches must be a positive integer")
        self.payload_format = payload_format
        self._condition = threading.Condition()
        self._batches = deque(maxlen=1 if conflate else max_batches)
        self._closed = False
        self._verbose = verbose
        self.received_frames = 0  # batches, not individual motion samples
        self.dropped_batches = 0
        self.last_error = None
        self.last_received_at = None
        receiver = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def setup(self):
                super().setup()
                self.connection.settimeout(5)

            def response(self, status, body=b""):
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if self.command != "HEAD" and body:
                    self.wfile.write(body)

            def do_HEAD(self):
                self.response(200 if self.path in ("/", "/imu") else 404)

            def do_GET(self):
                self.response(200, b'{"status":"ready"}') if self.path in ("/", "/imu") else self.response(404)

            def do_POST(self):
                if self.path != "/imu":
                    self.close_connection = True
                    self.response(404)
                    return
                if self.headers.get("Transfer-Encoding"):
                    self.close_connection = True
                    self.response(400, b'{"error":"Content-Length required"}')
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 1024 * 1024:
                    self.close_connection = True
                    self.response(413 if length > 1024 * 1024 else 400)
                    return
                try:
                    payload = self.rfile.read(length)
                    if len(payload) != length:
                        raise ValueError("Incomplete request body")
                    batch = receiver.decode(payload)
                except (DecodeError, ValueError, OSError) as error:
                    receiver.last_error = str(error)
                    self.close_connection = True
                    self.response(400, b'{"error":"Invalid Watch protobuf payload"}')
                    return
                receiver._enqueue(batch)
                self.response(200, b'{"status":"success"}')

            def log_message(self, format, *args):
                if receiver._verbose:
                    super().log_message(format, *args)

        self._server = ThreadingHTTPServer((host, port), Handler)
        self._server.daemon_threads = True
        self._server.block_on_close = False
        self.host, self.port = host, self._server.server_address[1]
        self.address = "http://{}:{}/imu".format(host, self.port)
        self._thread = threading.Thread(target=lambda: self._server.serve_forever(poll_interval=0.1),
                                        name="asmagic-watch-http", daemon=True)
        self._thread.start()

    @property
    def is_connected(self) -> bool:
        return not self._closed

    @property
    def has_received_data(self) -> bool:
        return self.received_frames > 0

    def decode(self, payload: bytes) -> WatchBatch:
        if self.payload_format == "batch":
            message = watch_batch_msg_pb2.WatchBatch.FromString(payload)
            if not message.frames or message.frame_count != len(message.frames):
                raise ValueError("Watch batch frame_count must match non-empty frames")
            return watch_batch(message)
        message_type = watch_batch_msg_pb2.Watch if self.payload_format == "single" else watch_msg_pb2.Watch
        message = message_type.FromString(payload)
        if not any((message.attitude, message.rotation_rate, message.gravity, message.acceleration)):
            raise ValueError("Watch sample has no motion data")
        frame = watch_frame(message)
        return WatchBatch((frame,), frame.timestamp, 1, message)

    def _enqueue(self, batch: WatchBatch) -> None:
        with self._condition:
            if self._closed:
                return
            if len(self._batches) == self._batches.maxlen:
                self.dropped_batches += 1
            self._batches.append(batch)
            self.received_frames += 1
            self.last_received_at = time.monotonic()
            self.last_error = None
            self._condition.notify_all()

    def get_frame(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[WatchBatch]:
        validate_timeout(timeout)
        deadline = None if timeout == -1 else time.monotonic() + timeout / 1000.0
        with self._condition:
            while not self._batches and not self._closed:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return None
                self._condition.wait(remaining)
            return self._batches.popleft() if self._batches and not self._closed else None

    def get(self, timeout: int = DEFAULT_TIMEOUT) -> Optional[WatchBatch]:
        """Compatibility read; prefer receive(timeout=...) in new code."""
        return self.get_frame(timeout)

    @overload
    def receive(self, timeout: None = None) -> WatchBatch: ...

    @overload
    def receive(self, timeout: int) -> Optional[WatchBatch]: ...

    def receive(self, timeout: Optional[int] = None) -> Optional[WatchBatch]:
        """Receive a batch; same timeout and closure behavior as TCP subscribers.

        No argument (or None/-1) waits for data. A nonnegative timeout is in
        milliseconds and returns None on timeout; 0 polls immediately.
        A closed receiver raises StopIteration in either mode.
        """
        return _receive_frame(self.get_frame, lambda: not self._closed, timeout)

    def stream(self, timeout: int = DEFAULT_TIMEOUT, on_frame=None,
               *, plot: bool = False, plot_options: Optional[dict] = None):
        validate_timeout(timeout)
        if plot:
            raise ValueError("此通道没有人体/手部绘图；plot=True 仅用于跟踪数据")
        while not self._closed:
            try:
                batch = self.receive(timeout=timeout)
            except StopIteration:
                return
            if batch is not None:
                if on_frame is not None:
                    on_frame(batch)
                yield batch

    def iter_samples(self, timeout: int = DEFAULT_TIMEOUT):
        for batch in self.stream(timeout):
            yield from batch.frames

    def __iter__(self):
        return self

    def __next__(self) -> WatchBatch:
        return self.receive()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self) -> None:
        with self._condition:
            if self._closed:
                return
            self._closed = True
            self._batches.clear()
            self._condition.notify_all()
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2)
