"""Named controls and compatibility contracts for asMagic joystick input."""
import numpy as np
import pytest

from asmagic import JoystickButtons, JoystickDataSubscriber
from asmagic.proto import joystick_msg_pb2


def decode(message):
    return JoystickDataSubscriber.decode(message.SerializeToString())


def virtual_message():
    return joystick_msg_pb2.Joystick(
        l_joystick_position=[-.25, .75], r_joystick_position=[.5, -1],
        button_pressed=[True, False, True, False])


@pytest.mark.parametrize("app_index,name", [(0, "triangle"), (1, "square"),
                                           (2, "cross"), (3, "circle")])
def test_named_face_buttons_match_screen_and_physical_input(app_index, name):
    virtual = joystick_msg_pb2.Joystick(button_pressed=[False] * 4)
    virtual.button_pressed[app_index] = True
    physical = joystick_msg_pb2.Joystick(is_connected=True)
    setattr(physical.face_buttons, name, True)
    for frame in (decode(virtual), decode(physical)):
        assert isinstance(frame.button, JoystickButtons)
        assert [key for key in ("triangle", "square", "cross", "circle")
                if getattr(frame.button, key)] == [name]
        assert getattr(frame, "button{}".format(app_index + 1)) is True


@pytest.mark.parametrize("name,section,field", [
    ("l1", "shoulders", "l1"), ("r1", "shoulders", "r1"),
    ("l3", "stick_buttons", "l3"), ("r3", "stick_buttons", "r3"),
    ("up", "dpad", "up"), ("down", "dpad", "down"),
    ("left", "dpad", "left"), ("right", "dpad", "right"),
    ("share", "system_buttons", "options"), ("options", "system_buttons", "menu"),
    ("home", "system_buttons", "home"), ("touchpad", "system_buttons", "touchpad"),
])
def test_named_buttons_remain_independent(name, section, field):
    message = joystick_msg_pb2.Joystick()
    setattr(getattr(message, section), field, True)
    buttons = decode(message).button
    assert getattr(buttons, name) is True
    assert sum(value is True for value in vars(buttons).values()) == 1


@pytest.mark.parametrize("travel,pressed", [(0.0, False), (.25, False), (.75, True), (1.0, True)])
def test_named_triggers_are_numbers_independent_of_legacy_press_flags(travel, pressed):
    message = joystick_msg_pb2.Joystick()
    message.triggers.l2.value = travel
    message.triggers.l2.pressed = pressed
    message.triggers.r2.value = 1.0 - travel
    frame = decode(message)
    assert type(frame.button.l2) is float and type(frame.button.r2) is float
    assert frame.button.l2 == pytest.approx(travel)
    assert frame.button.r2 == pytest.approx(1.0 - travel)
    assert frame.get_button(frame.BUTTON_L2) is pressed
    assert frame.l2 == frame.button.l2 and frame.r2 == frame.button.r2


def test_named_missing_controls_are_released_and_old_fields_keep_priority():
    frame = decode(virtual_message())
    for name, value in vars(frame.button).items():
        if name in ("triangle", "cross"):
            assert value is True
        elif name in ("l2", "r2"):
            assert type(value) is float and value == 0.0
        else:
            assert value is False
    # Existing packets retain their flat button order even if extended fields disagree.
    message = virtual_message()
    message.face_buttons.square = True
    assert decode(message).button.square is False


def test_virtual_and_physical_have_the_same_control_layout():
    virtual = decode(virtual_message())
    message = virtual_message()
    message.is_connected = True
    message.controller_name = "DualSense"
    message.triggers.l2.value = .75
    message.dpad.up = True
    physical = decode(message)
    for frame in (virtual, physical):
        assert (frame.get_numaxes(), frame.get_numbuttons(), frame.get_numhats()) == (6, 14, 1)
        assert frame.get_axis(frame.AXIS_LEFT_X) == -.25
        assert frame.get_axis(frame.AXIS_LEFT_Y) == -.75
        assert frame.get_axis(frame.AXIS_RIGHT_X) == .5
        assert frame.get_axis(frame.AXIS_RIGHT_Y) == 1
        assert frame.get_button(frame.BUTTON_A) is True
        assert frame.get_button(frame.BUTTON_B) is False
        assert frame.get_button(frame.BUTTON_C) is True
        assert frame.get_button(frame.BUTTON_D) is False
        # The original App-oriented API is unchanged, including up-positive Y.
        assert frame.left_y == .75 and frame.right_y == -1
        assert frame.button1 and frame.button3
        assert not frame.button2 and not frame.button4
    assert virtual.get_axis(2) == -1 and physical.get_axis(2) == .5
    assert virtual.get_hat(0) == (0, 0) and physical.get_hat(0) == (0, 1)
    assert virtual.get_name() == "asMagic joystick"
    assert physical.get_name() == "DualSense"


@pytest.mark.parametrize("app_index,pygame_index", [(0, 3), (1, 2), (2, 0), (3, 1)])
def test_each_screen_button_matches_its_physical_button(app_index, pygame_index):
    virtual = joystick_msg_pb2.Joystick(button_pressed=[False] * 4)
    virtual.button_pressed[app_index] = True
    physical = joystick_msg_pb2.Joystick(is_connected=True)
    setattr(physical.face_buttons, ("triangle", "square", "cross", "circle")[app_index], True)
    for frame in (decode(virtual), decode(physical)):
        assert [i for i in range(14) if frame.get_button(i)] == [pygame_index]


def test_trigger_travel_and_digital_press_are_distinct():
    message = joystick_msg_pb2.Joystick()
    message.triggers.l2.value = 1
    message.triggers.l2.pressed = True
    message.triggers.r2.value = .25
    frame = decode(message)
    assert frame.l2 == 1 and frame.r2 == .25
    assert frame.get_axis(2) == 1 and frame.get_axis(5) == -.5
    assert frame.get_button(6) is True and frame.get_button(7) is False


@pytest.mark.parametrize("index,section,field", [
    (4, "shoulders", "l1"), (5, "shoulders", "r1"),
    (8, "system_buttons", "options"), (9, "system_buttons", "menu"),
    (10, "system_buttons", "home"), (11, "stick_buttons", "l3"),
    (12, "stick_buttons", "r3"), (13, "system_buttons", "touchpad"),
])
def test_extra_buttons_are_independent(index, section, field):
    message = joystick_msg_pb2.Joystick()
    setattr(getattr(message, section), field, True)
    frame = decode(message)
    assert [i for i in range(14) if frame.get_button(i)] == [index]


def test_hat_directions_and_opposing_inputs():
    message = joystick_msg_pb2.Joystick()
    message.dpad.left = True
    message.dpad.down = True
    assert decode(message).get_hat(0) == (-1, -1)
    message.dpad.right = True
    message.dpad.up = True
    assert decode(message).get_hat(0) == (0, 0)


def test_empty_frame_has_neutral_controls_and_missing_motion():
    frame = decode(joystick_msg_pb2.Joystick())
    assert [frame.get_axis(i) for i in range(6)] == [0, 0, -1, 0, 0, -1]
    assert not any(frame.get_button(i) for i in range(14))
    assert frame.get_hat(0) == (0, 0)
    assert not frame.has_motion
    assert all(getattr(frame, field).size == 0 for field in
               ("gravity", "user_acceleration", "rotation_rate", "attitude"))


def test_motion_preserves_presence_and_sensor_state():
    message = joystick_msg_pb2.Joystick()
    message.motion.sensors_active = True
    message.motion.gravity.SetInParent()
    message.motion.user_acceleration.x = .25
    message.motion.rotation_rate.z = .5
    message.motion.attitude.w = 1
    frame = decode(message)
    assert frame.has_motion
    np.testing.assert_array_equal(frame.gravity, [0, 0, 0])
    np.testing.assert_array_equal(frame.user_acceleration, [.25, 0, 0])
    np.testing.assert_array_equal(frame.rotation_rate, [0, 0, .5])
    np.testing.assert_array_equal(frame.attitude, [0, 0, 0, 1])
    message.motion.ClearField("gravity")
    assert decode(message).gravity.size == 0
    message.motion.sensors_active = False
    inactive = decode(message)
    assert not inactive.has_motion and inactive.attitude.size == 0


@pytest.mark.parametrize("method,index", [("get_axis", -1), ("get_axis", 6),
                                          ("get_button", 14), ("get_hat", 1)])
def test_invalid_indices_do_not_wrap_or_return_fabricated_controls(method, index):
    frame = decode(virtual_message())
    with pytest.raises(IndexError):
        getattr(frame, method)(index)
    with pytest.raises(TypeError):
        getattr(frame, method)(.5)


def test_all_queries_share_one_received_frame_and_disconnect_clears_extras(publisher):
    socket, connect = publisher
    sub = connect(JoystickDataSubscriber)
    physical = virtual_message()
    physical.is_connected = True
    physical.shoulders.l1 = True
    physical.triggers.r2.value = 1
    physical.motion.sensors_active = True
    physical.motion.attitude.w = 1
    socket.send(physical.SerializeToString())
    frame = sub.get(timeout=2000)
    assert frame.get_button(4) and frame.get_axis(5) == 1
    assert frame.button.l1 is True and frame.button.r2 == 1.0
    assert frame.button.triangle is True
    assert frame.attitude[3] == 1 and sub.received_frames == 1
    assert sub.get(timeout=0) is None
    socket.send(virtual_message().SerializeToString())
    virtual = sub.get(timeout=2000)
    assert virtual.get_button(3) and not virtual.get_button(4)
    assert virtual.button.triangle is True and virtual.button.l1 is False
    assert virtual.button.r2 == 0.0
    assert virtual.get_axis(5) == -1 and virtual.attitude.size == 0
    assert not virtual.is_connected and sub.received_frames == 2


def test_joystick_fields_share_one_received_frame(publisher):
    socket, connect = publisher
    sub = connect(JoystickDataSubscriber)
    message = virtual_message()
    message.timestamp = 42.5
    socket.send(message.SerializeToString())
    frame = sub.receive(timeout=2000)
    for field, expected in (("timestamp", 42.5),
                            ("left_joystick", [-.25, .75]),
                            ("right_joystick", [.5, -1]),
                            ("buttons", [True, False, True, False])):
        result = getattr(frame, field)
        np.testing.assert_array_equal(result, expected)
    assert sub.received_frames == 1
