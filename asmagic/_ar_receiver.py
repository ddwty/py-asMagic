"""Receive/decode AR packets independently of display and user processing."""
from collections import deque
import threading

from ._images import HEVCDecoder, has_hevc_random_access_picture, nal_units
from ._subscriber import Subscriber
from .decoders import ar_frame
from .proto import phone_msg_pb2


_PREVIEW_BACKLOG_SECONDS = 0.1
_PREVIEW_MAX_BATCH = 32


def _trim_preview_backlog(frames):
    """Skip the outdated prefix only when a new independent picture is ready."""
    start = frames[0].source_timestamp
    if not (start > 0 and frames[-1].source_timestamp - start >= _PREVIEW_BACKLOG_SECONDS):
        return False
    for index, frame in enumerate(reversed(frames)):
        prefix = len(frames) - index - 1
        if not prefix:
            break
        if not frame.has_color_image or frame.source_timestamp <= start:
            continue
        if frame.rgb_codec == 2:
            if not frame.rgb_is_key_frame or not frame.rgb_codec_config:
                continue
            try:
                units = list(nal_units(frame.color_img, frame.rgb_nal_unit_header_length or 4))
            except ValueError:
                continue
            if not has_hevc_random_access_picture(units):
                continue
        elif frame.rgb_codec not in (0, 1):
            continue
        for _ in range(prefix):
            frames.popleft()
        return True
    return False


class _ARWireSubscriber(Subscriber):
    _message_type = phone_msg_pb2.Phone
    _from_message = staticmethod(ar_frame)
    _raise_decode_errors = True


class ARReceiverPump:
    """One thread owns its socket and ordered video decoder."""

    def __init__(self, ip, port, hwm, conflate, verbose,
                 subscriber_type=_ARWireSubscriber, thread_name="asmagic-ar-receiver"):
        self._condition = threading.Condition()
        self._pending = deque(maxlen=1 if conflate else hwm)
        self._batch_size = min(hwm, _PREVIEW_MAX_BATCH) if conflate else 1
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
            # Encoded frames keep their order. Preview recovery can restart at
            # an independent image, without arbitrarily dropping reference packets.
            receiver = subscriber_type(ip, port, hwm, False, verbose)
            self.active = True
            self._ready.set()
            frames = deque()
            read_error = None
            transport = getattr(receiver, "_usb", None)
            usb_generation = getattr(transport, "generation", 0)
            while not self._stop.is_set():
                try:
                    while read_error is None and len(frames) < self._batch_size and not self._stop.is_set():
                        try:
                            frame = receiver.get_frame(timeout=0 if frames else 50)
                        except (RuntimeError, ValueError, ImportError, OSError) as error:
                            read_error = error
                            break
                        generation = getattr(transport, "generation", 0)
                        if generation != usb_generation:
                            frames.clear()
                            decoder.reset()
                            usb_generation = generation
                        if frame is None:
                            break
                        frames.append(frame)
                    if not frames:
                        if read_error is not None:
                            error, read_error = read_error, None
                            raise error
                        if transport is not None:
                            self.last_error = receiver.last_error
                        continue
                    self.received_frames = receiver.received_frames
                    self.last_received_at = receiver.last_received_at
                    if len(frames) > 1 and _trim_preview_backlog(frames):
                        decoder.reset()
                    frame = frames.popleft()
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
