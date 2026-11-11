"""JPEG decoding and per-stream HEVC reference-frame continuity."""
import io
from typing import Optional
import numpy as np


def nal_units(data: bytes, header_length: int):
    if header_length not in (1, 2, 4):
        raise ValueError("HEVC NAL length-prefix size must be 1, 2 or 4")
    offset = 0
    while offset < len(data):
        if len(data) - offset < header_length:
            raise ValueError("Truncated HEVC NAL length prefix")
        size = int.from_bytes(data[offset:offset + header_length], "big")
        offset += header_length
        if size == 0 or size > len(data) - offset:
            raise ValueError("Invalid HEVC NAL length")
        yield data[offset:offset + size]
        offset += size


class HEVCDecoder:
    """Feed every received packet in order, even when its image is not displayed."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._decoder = None
        self._configuration = None
        self._frame_id = 0

    def decode(self, frame):
        image = self.decode_frame(frame)
        return None if image is None else image.to_ndarray(format="rgb24")

    def decode_frame(self, frame):
        """Retain the decoded picture; RGB conversion can run on the consumer thread."""
        if frame.rgb_codec != 2 or not frame.has_color_image:
            self.reset()
            return None
        try:
            import av
        except ImportError as error:
            raise ImportError("HEVC decoding requires PyAV; install the complete SDK: python -m pip install --upgrade asmagic") from error
        if not frame.rgb_codec_config:
            self.reset()
            raise ValueError("HEVC frame has no VPS/SPS/PPS configuration")
        header_length = frame.rgb_nal_unit_header_length or 4
        try:
            units = list(nal_units(frame.color_img, header_length))
        except ValueError:
            self.reset()
            raise
        configuration = (tuple(frame.rgb_codec_config), header_length,
                         frame.rgb_width, frame.rgb_height, getattr(frame, "session_identifier", ""))
        # Current senders number admitted stream packets, not all camera frames.
        gap = self._frame_id and frame.frame_id and frame.frame_id != self._frame_id + 1
        if configuration != self._configuration or gap:
            self.reset()
        self._configuration = configuration
        self._frame_id = frame.frame_id
        # Inspect IRAP NAL types too, for saved frames without key-frame metadata.
        is_key_frame = any(unit and 16 <= ((unit[0] >> 1) & 0x3f) <= 21 for unit in units)
        if self._decoder is None:
            if not is_key_frame:
                return None  # Join/recover at a key frame instead of showing grey concealment.
            self._decoder = av.CodecContext.create("hevc", "r")
            self._decoder.thread_count = 1
            self._decoder.flags |= av.codec.context.Flags.low_delay
            self._decoder.options = {"err_detect": "explode"}
        annex_b = b"".join(b"\x00\x00\x00\x01" + unit
                           for unit in list(frame.rgb_codec_config) + units)
        try:
            decoded = self._decoder.decode(av.Packet(annex_b))
        except av.error.FFmpegError:
            self.reset()
            return None
        if not decoded:
            return None
        if decoded[-1].is_corrupt:
            self.reset()
            return None
        return decoded[-1]


def color_array(frame):
    if not frame.has_color_image:
        return None
    if frame.rgb_codec in (0, 1):
        from PIL import Image
        with Image.open(io.BytesIO(frame.color_img)) as image:
            return np.array(image.convert("RGB"))
    if frame.rgb_codec != 2:
        raise ValueError("Unsupported RGB codec: {}".format(frame.rgb_codec))
    image = HEVCDecoder().decode(frame)
    if image is None:
        raise ValueError("An isolated HEVC frame needs a decodable key frame; receive inter-frame video with ARDataSubscriber or CameraDataSubscriber")
    return image


class ColorImage:
    """Shared image access for AR and ordinary camera frames."""

    @property
    def has_color_image(self) -> bool:
        return bool(self.color_img)

    @property
    def color_bytes(self) -> bytes:
        """Raw JPEG or length-prefixed HEVC bytes; inspect rgb_codec before saving."""
        return self.color_img

    @property
    def color_array(self) -> Optional[np.ndarray]:
        key = self._color_cache_key()
        if self._decoded_color_key != key:
            self._decoded_video_frame = None
            self._decoded_color = color_array(self)
            self._decoded_color_key = key
        elif self._decoded_color is None and self._decoded_video_frame is not None:
            self._decoded_color = self._decoded_video_frame.to_ndarray(format="rgb24")
            self._decoded_video_frame = None
        return self._decoded_color

    def _color_cache_key(self):
        return (self.color_img, self.rgb_codec, self.rgb_codec_config, self.rgb_nal_unit_header_length)

    @property
    def color(self) -> Optional[np.ndarray]:
        return self.color_array

    @property
    def rgb_codec_name(self) -> str:
        return {0: "jpeg", 1: "jpeg", 2: "hevc"}.get(self.rgb_codec, "unknown")

    @property
    def image_rotation_quarter_turns_clockwise(self) -> int:
        return self.protobuf.image_rotation_quarter_turns_clockwise if self.protobuf is not None else 0

    @property
    def color_upright(self) -> Optional[np.ndarray]:
        image = self.color_array
        return None if image is None else np.rot90(image, -(self.image_rotation_quarter_turns_clockwise % 4))

    def show_color(self, window_name: str = "Color Image") -> bool:
        image = self.color_array
        if image is None:
            return False
        import cv2
        cv2.imshow(window_name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        return True
