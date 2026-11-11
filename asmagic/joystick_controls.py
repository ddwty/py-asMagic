"""Named controls and pygame-compatible reads from one received frame."""
from dataclasses import dataclass
import operator
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class JoystickButtons:
    """Button states; L2/R2 are analog travel from 0.0 to 1.0.

    Available on every frame, including on-screen input and older packets.
    Controls absent from the received frame are released.
    """

    triangle: bool = False
    square: bool = False
    cross: bool = False
    circle: bool = False
    l1: bool = False
    r1: bool = False
    l2: float = 0.0
    r2: float = 0.0
    l3: bool = False
    r3: bool = False
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    share: bool = False
    options: bool = False
    home: bool = False
    touchpad: bool = False


class JoystickControls:
    """Input-query methods shared by physical and on-screen controllers.

    Indices follow pygame's documented PS5 layout. Index 13 additionally exposes
    the touchpad click sent by asMagic. These methods never receive another frame.
    """

    AXIS_LEFT_X = 0
    AXIS_LEFT_Y = 1
    AXIS_L2 = 2
    AXIS_RIGHT_X = 3
    AXIS_RIGHT_Y = 4
    AXIS_R2 = 5

    BUTTON_C = BUTTON_CROSS = 0
    BUTTON_D = BUTTON_CIRCLE = 1
    BUTTON_B = BUTTON_SQUARE = 2
    BUTTON_A = BUTTON_TRIANGLE = 3
    BUTTON_L1 = 4
    BUTTON_R1 = 5
    BUTTON_L2 = 6
    BUTTON_R2 = 7
    BUTTON_SHARE = 8
    BUTTON_OPTIONS = 9
    BUTTON_HOME = 10
    BUTTON_L3 = 11
    BUTTON_R3 = 12
    BUTTON_TOUCHPAD = 13

    @property
    def button(self) -> JoystickButtons:
        """Named button states from this frame, without receiving new data."""
        return JoystickButtons(
            triangle=self.get_button(self.BUTTON_TRIANGLE),
            square=self.get_button(self.BUTTON_SQUARE),
            cross=self.get_button(self.BUTTON_CROSS),
            circle=self.get_button(self.BUTTON_CIRCLE),
            l1=self.get_button(self.BUTTON_L1),
            r1=self.get_button(self.BUTTON_R1),
            l2=self.l2,
            r2=self.r2,
            l3=self.get_button(self.BUTTON_L3),
            r3=self.get_button(self.BUTTON_R3),
            up=bool(getattr(self.dpad, "up", False)),
            down=bool(getattr(self.dpad, "down", False)),
            left=bool(getattr(self.dpad, "left", False)),
            right=bool(getattr(self.dpad, "right", False)),
            share=self.get_button(self.BUTTON_SHARE),
            options=self.get_button(self.BUTTON_OPTIONS),
            home=self.get_button(self.BUTTON_HOME),
            touchpad=self.get_button(self.BUTTON_TOUCHPAD),
        )

    def get_name(self) -> str:
        return self.controller_name or "asMagic joystick"

    def get_numaxes(self) -> int:
        """Six fixed logical axes, including the two triggers."""
        return 6

    def get_numbuttons(self) -> int:
        """Fourteen fixed logical buttons, independent of attached hardware."""
        return 14

    def get_numhats(self) -> int:
        return 1

    @staticmethod
    def _index(index: int, count: int) -> int:
        index = operator.index(index)
        if not 0 <= index < count:
            raise IndexError("Control index must be between 0 and {}".format(count - 1))
        return index

    def get_axis(self, axis_number: int) -> float:
        """Stick Y is down-positive; triggers are -1 released, +1 fully pressed."""
        index = self._index(axis_number, self.get_numaxes())
        if index in (self.AXIS_L2, self.AXIS_R2):
            value = self.l2 if index == self.AXIS_L2 else self.r2
            return 2.0 * value - 1.0
        stick = self.left_joystick if index < 2 else self.right_joystick
        component = 0 if index in (self.AXIS_LEFT_X, self.AXIS_RIGHT_X) else 1
        value = float(stick[component]) if len(stick) > component else 0.0
        return -value if component == 1 else value

    def get_button(self, button: int) -> bool:
        """Pressed state only; ordinary button pressure is not needed."""
        index = self._index(button, self.get_numbuttons())
        if index < 4:
            # The App's wire order is A/Triangle, B/Square, C/Cross, D/Circle.
            legacy_index = (2, 3, 1, 0)[index]
            return bool(self.buttons[legacy_index]) if len(self.buttons) > legacy_index else False
        section, field = (
            ("shoulders", "l1"), ("shoulders", "r1"),
            ("triggers", "l2"), ("triggers", "r2"),
            ("system_buttons", "options"), ("system_buttons", "menu"),
            ("system_buttons", "home"), ("stick_buttons", "l3"),
            ("stick_buttons", "r3"), ("system_buttons", "touchpad"),
        )[index - 4]
        message = getattr(self, section, None)
        if message is None:
            return False
        value = getattr(message, field)
        return bool(value.pressed if section == "triggers" else value)

    def get_hat(self, hat_number: int) -> Tuple[int, int]:
        """D-pad: right/up are +1; left/down are -1; released is (0, 0)."""
        self._index(hat_number, self.get_numhats())
        if self.dpad is None:
            return (0, 0)
        return (int(self.dpad.right) - int(self.dpad.left),
                int(self.dpad.up) - int(self.dpad.down))

    @property
    def l2(self) -> float:
        """Left trigger travel, 0 released to 1 fully pressed."""
        return float(self.triggers.l2.value) if self.triggers is not None else 0.0

    @property
    def r2(self) -> float:
        """Right trigger travel, 0 released to 1 fully pressed."""
        return float(self.triggers.r2.value) if self.triggers is not None else 0.0

    @property
    def has_motion(self) -> bool:
        return self.motion is not None and bool(self.motion.sensors_active)

    def _motion_array(self, name: str, components: str = "xyz") -> np.ndarray:
        if not self.has_motion or not self.motion.HasField(name):
            return np.array([], dtype=np.float32)
        vector = getattr(self.motion, name)
        return np.array([getattr(vector, component) for component in components], dtype=np.float32)

    @property
    def gravity(self) -> np.ndarray:
        """Controller gravity in G, or an empty array when unavailable."""
        return self._motion_array("gravity")

    @property
    def user_acceleration(self) -> np.ndarray:
        """Controller acceleration with gravity removed, in G."""
        return self._motion_array("user_acceleration")

    @property
    def rotation_rate(self) -> np.ndarray:
        """Controller angular rate in rad/s."""
        return self._motion_array("rotation_rate")

    @property
    def attitude(self) -> np.ndarray:
        """Controller quaternion in x/y/z/w order."""
        return self._motion_array("attitude", "xyzw")
