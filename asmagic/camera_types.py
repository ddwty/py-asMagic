"""Ordinary camera image frames, without spatial tracking fields."""
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple

import numpy as np
from google.protobuf.message import Message

from ._images import ColorImage


@dataclass
class CameraFrame(ColorImage):
    """One encoded camera image and its capture metadata.

    Like ARFrame, `has_color_image` and `color_bytes` expose the encoded image;
    `color_array` is RGB uint8 in received orientation and `color_upright`
    applies sender rotation metadata. Camera frames have no pose or depth.
    `image` and `image_upright` are aliases. `source_timestamp` is the
    camera capture clock in seconds.
    """
    timestamp: float = 0.0
    source_timestamp: float = 0.0
    frame_id: int = 0
    color_img: bytes = b""
    rgb_width: int = 0
    rgb_height: int = 0
    rgb_codec: int = 0
    rgb_codec_config: Tuple[bytes, ...] = ()
    rgb_is_key_frame: bool = False
    rgb_nal_unit_header_length: int = 0
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)
    _decoded_color: Optional[np.ndarray] = field(default=None, init=False, repr=False, compare=False)
    _decoded_color_key: Optional[tuple] = field(default=None, init=False, repr=False, compare=False)
    _decoded_video_frame: Optional[Any] = field(default=None, init=False, repr=False, compare=False)

    @property
    def width(self) -> int:
        return self.rgb_width

    @property
    def height(self) -> int:
        return self.rgb_height

    @property
    def has_image(self) -> bool:
        return self.has_color_image

    @property
    def image_bytes(self) -> bytes:
        return self.color_bytes

    @property
    def image(self) -> Optional[np.ndarray]:
        return self.color_array

    @property
    def image_upright(self) -> Optional[np.ndarray]:
        return self.color_upright

    def show_image(self, window_name: str = "Camera Image", upright: bool = True) -> bool:
        image = self.image_upright if upright else self.image
        if image is None:
            return False
        import cv2
        cv2.imshow(window_name, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        return True

    def show_images(self, window_name: str = "Camera Image", upright: bool = True) -> bool:
        """Display this camera image; call cv2.waitKey() to process window events."""
        return self.show_image(window_name, upright)
