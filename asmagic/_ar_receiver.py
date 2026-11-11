"""Receive/decode AR packets independently of display and user processing."""
from collections import deque
import threading

from ._images import HEVCDecoder
from ._subscriber import Subscriber
from .decoders import ar_frame
from .proto import phone_msg_pb2


class _ARWireSubscriber(Subscriber):
    _message_type = phone_msg_pb2.Phone
    _from_message = staticmethod(ar_frame)
    _raise_decode_errors = True


class ARReceiverPump:
    """One thread owns its socket and decoder; only decoded output may be replaced."""

    def __init__(self, ip, port, hwm, conflate, verbose,
                 subscriber_type=_ARWireSubscriber, thread_name="asmagic-ar-receiver"):
        self._condition = threading.Condition()
        self._pending = deque(maxlen=1 if conflate else hwm)
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._startup_error = None
        self.active = False
        self.last_error = None
        self.received_frames = 0
        self.last_received_at = None
        self._thread = threading.Thread(
            target=self._run, args=(ip, port, hwm, verbose, subscriber_type),
            name=thread_name, daemon=True)
        self._thread.start()
        self._ready.wait()
        if self._startup_error is not None:
            self.close()
            raise self._startup_error

    def _publish(self, item):
        with self._condition:
            self._pending.append(item)
            self._condition.notify_all()

    def _run(self, ip, port, hwm, verbose, subscriber_type):
        receiver = None
        decoder = HEVCDecoder()
        try:
            # Create, poll, receive and close the ZeroMQ socket on this thread.
            # Conflation belongs AFTER video decoding, never on encoded packets.
            receiver = subscriber_type(ip, port, hwm, False, verbose)
            self.active = True
            self._ready.set()
            while not self._stop.is_set():
                try:
                    frame = receiver.get_frame(timeout=50)
                    if frame is None:
                        continue
                    self.received_frames = receiver.received_frames
                    self.last_received_at = receiver.last_received_at
                    if frame.rgb_codec == 2 and frame.has_color_image:
                        frame._decoded_video_frame = decoder.decode_frame(frame)
                        frame._decoded_color_key = frame._color_cache_key()
                    else:
                        decoder.reset()
                    self.last_error = None
                    self._publish(frame)
                except (RuntimeError, ValueError, ImportError, OSError) as error:
                    decoder.reset()
                    self.last_error = str(error)
                    self._publish(error)
        except Exception as error:
            if not self._ready.is_set():
                self._startup_error = error
            else:
                self.last_error = str(error)
                self._publish(error)
        finally:
            if receiver is not None:
                receiver.close()
            decoder.reset()
            with self._condition:
                self.active = False
                self._condition.notify_all()
            self._ready.set()

    def get(self, timeout):
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < -1:
            raise ValueError("timeout must be an integer >= -1, in milliseconds")
        with self._condition:
            self._condition.wait_for(
                lambda: self._pending or not self.active or self._stop.is_set(),
                timeout=None if timeout == -1 else timeout / 1000)
            if self._stop.is_set() or not self._pending:
                return None
            item = self._pending.popleft()
        if isinstance(item, Exception):
            raise item
        return item

    def close(self):
        self._stop.set()
        with self._condition:
            self._pending.clear()
            self._condition.notify_all()
        if threading.current_thread() is not self._thread:
            self._thread.join()
        with self._condition:
            self._pending.clear()
