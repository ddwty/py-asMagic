"""Public data objects with field access and image display helpers."""
from dataclasses import dataclass, field
from typing import Any, Optional, Tuple
import numpy as np
from google.protobuf.message import Message

from ._images import ColorImage
from .geometry import pose_matrix
from .joystick_controls import JoystickControls


@dataclass
class ARFrame(ColorImage):
    """RGB-D frame; raw arrays and image bytes preserve their received values.

    Current poses use [tx, ty, tz, qx, qy, qz, qw]. Intrinsics are column-major.
    timestamp is the legacy sender wall clock; source_timestamp is monotonic.
    """
    timestamp: float = 0.0
    color_img: bytes = b""
    depth_img: bytes = b""
    depth_width: int = 0
    depth_height: int = 0
    local_pose: np.ndarray = field(default_factory=lambda: np.array([]))
    global_pose: np.ndarray = field(default_factory=lambda: np.array([]))
    velocity: np.ndarray = field(default_factory=lambda: np.array([]))
    camera_intrinsics: np.ndarray = field(default_factory=lambda: np.array([]))
    frame_id: int = 0
    source_timestamp: float = 0.0
    rgb_width: int = 0
    rgb_height: int = 0
    depth_confidence: bytes = b""
    depth_meters_per_unit: float = 0.0
    session_identifier: str = ""
    shared_world_identifier: str = ""
    global_pose_is_shared: bool = False
    rgb_codec: int = 0
    rgb_codec_config: Tuple[bytes, ...] = ()
    rgb_is_key_frame: bool = False
    rgb_nal_unit_header_length: int = 0
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)
    _decoded_color: Optional[np.ndarray] = field(default=None, init=False, repr=False, compare=False)
    _decoded_color_key: Optional[tuple] = field(default=None, init=False, repr=False, compare=False)
    _decoded_video_frame: Optional[Any] = field(default=None, init=False, repr=False, compare=False)

    @property
    def has_depth_image(self) -> bool:
        return bool(self.depth_img) and self.depth_width > 0 and self.depth_height > 0

    @property
    def has_pose(self) -> bool:
        return len(self.local_pose) > 0 or len(self.global_pose) > 0

    @property
    def depth_array(self) -> Optional[np.ndarray]:
        if not self.has_depth_image:
            return None
        expected = self.depth_width * self.depth_height * 2
        if len(self.depth_img) != expected:
            raise ValueError("Depth byte count does not match width * height * 2")
        return np.frombuffer(self.depth_img, dtype="<u2").reshape(self.depth_height, self.depth_width)

    @property
    def depth(self) -> Optional[np.ndarray]:
        return self.depth_array

    @property
    def depth_confidence_array(self) -> Optional[np.ndarray]:
        if not self.depth_confidence:
            return None
        if self.depth_width <= 0 or self.depth_height <= 0 or len(self.depth_confidence) != self.depth_width * self.depth_height:
            raise ValueError("Depth confidence byte count does not match dimensions")
        return np.frombuffer(self.depth_confidence, dtype=np.uint8).reshape(self.depth_height, self.depth_width)

    @property
    def local_pose_matrix(self) -> Optional[np.ndarray]:
        """4x4 local transform derived from local_pose."""
        return pose_matrix(self.local_pose)

    @property
    def global_pose_matrix(self) -> Optional[np.ndarray]:
        """4x4 global transform derived from global_pose."""
        return pose_matrix(self.global_pose)

    @property
    def camera_intrinsics_matrix(self) -> Optional[np.ndarray]:
        """3x3 intrinsics; camera_intrinsics retains its received array."""
        if self.camera_intrinsics.size == 9:
            return self.camera_intrinsics.reshape(3, 3, order="F")
        return None

    @property
    def depth_upright(self) -> Optional[np.ndarray]:
        image = self.depth_array
        return None if image is None else np.rot90(image, -(self.image_rotation_quarter_turns_clockwise % 4))

    def show_depth(self, window_name: str = "Depth Image", colormap: int = None) -> bool:
        image = self.depth_array
        if image is None:
            return False
        import cv2
        normalized = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        cv2.imshow(window_name, cv2.applyColorMap(normalized, cv2.COLORMAP_JET if colormap is None else colormap))
        return True

    def show_images(self, show_color: bool = True, show_depth: bool = True,
                    color_window: str = "Color Image", depth_window: str = "Depth Image") -> tuple:
        """Display color and depth by default; returns two display booleans."""
        return (self.show_color(color_window) if show_color else False,
                self.show_depth(depth_window) if show_depth else False)


@dataclass
class IMUFrame:
    """
    A single frame of IMU data containing all sensor readings.

    Attributes:
        timestamp: Sender wall-clock seconds (iPhone IMU).
        accelerometer: 3-axis accelerometer data [x, y, z] in G
        gyroscope: 3-axis gyroscope data [x, y, z] in rad/s
        magnetometer: 3-axis magnetometer data [x, y, z] in μT
        gravity: 3-axis gravity vector [x, y, z] in G
        user_acceleration: 3-axis user acceleration [x, y, z] in G
        attitude: Device attitude as quaternion [x, y, z, w]

    Received frames keep the original 3/4-element zero fallback for an omitted
    sensor. Check has_* before treating those placeholders as measurements.
    """
    timestamp: float = 0.0
    accelerometer: np.ndarray = field(default_factory=lambda: np.array([]))
    gyroscope: np.ndarray = field(default_factory=lambda: np.array([]))
    magnetometer: np.ndarray = field(default_factory=lambda: np.array([]))
    gravity: np.ndarray = field(default_factory=lambda: np.array([]))
    user_acceleration: np.ndarray = field(default_factory=lambda: np.array([]))
    attitude: np.ndarray = field(default_factory=lambda: np.array([]))

    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    def _has_sensor(self, name: str) -> bool:
        if self.protobuf is not None:
            return self.protobuf.HasField(name)
        return len(getattr(self, name)) > 0

    @property
    def has_accelerometer(self) -> bool:
        """Check if accelerometer data is available"""
        return self._has_sensor("accelerometer")

    @property
    def has_gyroscope(self) -> bool:
        """Check if gyroscope data is available"""
        return self._has_sensor("gyroscope")

    @property
    def has_magnetometer(self) -> bool:
        """Check if magnetometer data is available"""
        return self._has_sensor("magnetometer")

    @property
    def has_gravity(self) -> bool:
        """Check if gravity data is available"""
        return self._has_sensor("gravity")

    @property
    def has_user_acceleration(self) -> bool:
        """Check if user acceleration data is available"""
        return self._has_sensor("user_acceleration")

    @property
    def has_attitude(self) -> bool:
        """Check if attitude data is available"""
        return self._has_sensor("attitude")


@dataclass
class JoystickFrame(JoystickControls):
    """
    A single frame of joystick data containing joystick positions and button states.

    Attributes:
        timestamp: Sender wall-clock seconds.
        left_joystick: Left joystick [x, y], raw values from the sender
        right_joystick: Right joystick [x, y], raw values from the sender
        buttons: Button states [button1, button2, button3, button4] as boolean list
        button: Named states such as button.square; button.l2/r2 are 0..1 floats

    Modern asMagic sticks use -1..1 with neutral 0; legacy values are returned
    unchanged. Default-constructed frames retain the old 0.5 fallback.
    """
    timestamp: float = 0.0
    left_joystick: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5], dtype=np.float32))
    right_joystick: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5], dtype=np.float32))
    buttons: list = field(default_factory=lambda: [False, False, False, False])

    controller_name: str = ""
    is_connected: bool = False
    battery_level: float = 0.0
    is_charging: bool = False
    face_buttons: Optional[Message] = None
    dpad: Optional[Message] = None
    shoulders: Optional[Message] = None
    triggers: Optional[Message] = None
    stick_buttons: Optional[Message] = None
    system_buttons: Optional[Message] = None
    motion: Optional[Message] = None
    protobuf: Optional[Message] = field(default=None, repr=False, compare=False)

    @property
    def left_stick(self) -> np.ndarray:
        return self.left_joystick

    @property
    def right_stick(self) -> np.ndarray:
        return self.right_joystick

    @property
    def has_left_joystick(self) -> bool:
        """Check if left joystick data is available"""
        return len(self.left_joystick) >= 2

    @property
    def has_right_joystick(self) -> bool:
        """Check if right joystick data is available"""
        return len(self.right_joystick) >= 2

    @property
    def has_buttons(self) -> bool:
        """Check if button data is available"""
        return len(self.buttons) > 0

    @property
    def left_x(self) -> float:
        """Left joystick X position (raw sender range, right is positive)"""
        return float(self.left_joystick[0]) if self.has_left_joystick else 0.5

    @property
    def left_y(self) -> float:
        """Left joystick Y position (raw sender range, up is positive)"""
        return float(self.left_joystick[1]) if self.has_left_joystick else 0.5

    @property
    def right_x(self) -> float:
        """Right joystick X position (raw sender range, right is positive)"""
        return float(self.right_joystick[0]) if self.has_right_joystick else 0.5

    @property
    def right_y(self) -> float:
        """Right joystick Y position (raw sender range, up is positive)"""
        return float(self.right_joystick[1]) if self.has_right_joystick else 0.5

    @property
    def button1(self) -> bool:
        """Button 1 state"""
        return self.buttons[0] if len(self.buttons) > 0 else False

    @property
    def button2(self) -> bool:
        """Button 2 state"""
        return self.buttons[1] if len(self.buttons) > 1 else False

    @property
    def button3(self) -> bool:
        """Button 3 state"""
        return self.buttons[2] if len(self.buttons) > 2 else False

    @property
    def button4(self) -> bool:
        """Button 4 state"""
        return self.buttons[3] if len(self.buttons) > 3 else False
