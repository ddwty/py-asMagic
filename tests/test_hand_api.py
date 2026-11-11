"""Consumer hand semantics: anatomical identity, readable joints and missing data."""
import numpy as np
import pytest

from asmagic import (HAND_JOINT_NAMES, Hand, HandJoint, HandJointName, HandPoseDataSubscriber,
                     HandSide, FaceAndHandTrackingDataSubscriber)
from asmagic.proto import hand_pose_pb2, face_tracking_pb2


def test_crossed_hands_keep_wire_side_and_readable_joint_identity():
    message = hand_pose_pb2.HandPoseFrame(source_timestamp=4, unknown_hand_count=1)
    # Screen position must never override anatomical side, including crossed hands.
    message.left_hand.joints.add(name="index_tip", x=.9, y=.2, confidence=.8)
    message.right_hand.joints.add(name="index_tip", x=.1, y=.3, confidence=.7)
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    assert frame.left is frame.left_hand and frame.right is frame.right_hand
    assert frame.hands == (frame.left, frame.right)
    assert tuple(hand.side for hand in frame.hands) == (HandSide.LEFT, HandSide.RIGHT)
    assert frame.left.index.tip is frame.left.joints.index_tip
    assert frame.right.index.tip is frame.right.joints[HandJointName.INDEX_TIP]
    assert frame.left.index.tip.xy == pytest.approx((.9, .2))
    assert frame.unknown_hand_count == 1 and frame.hand_count == 2


def test_every_finger_joint_matches_stable_array_rows():
    joints = {name: HandJoint(name, row / 21, .5, .9) for row, name in enumerate(HAND_JOINT_NAMES)}
    hand = Hand(.9, joints)
    assert hand.side == HandSide.UNKNOWN  # A standalone hand must not invent a side.
    assert hand.wrist is hand.joints.wrist
    for finger_name in ("thumb", "index", "middle", "ring", "little"):
        finger = getattr(hand, finger_name)
        nodes = ("cmc", "mp", "ip", "tip") if finger_name == "thumb" else ("mcp", "pip", "dip", "tip")
        for node in nodes:
            name = finger_name + "_" + node
            joint = getattr(finger, node)
            assert joint is hand.joints[name]
            np.testing.assert_allclose(hand.as_arrays().points[HandJointName(name).row], joint.xy)


def test_missing_hands_joints_and_zero_coordinates_are_distinct():
    message = hand_pose_pb2.HandPoseFrame(unknown_hand_count=2)
    empty = HandPoseDataSubscriber.decode(message.SerializeToString())
    assert empty.left is empty.right is None and empty.hands == ()
    assert empty.unknown_hand_count == 2
    message.right_hand.joints.add(name="wrist", x=0, y=0, confidence=0)
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    assert frame.hands == (frame.right,) and frame.right.side == HandSide.RIGHT
    assert frame.right.wrist.xy == (0, 0) and frame.right.wrist.confidence == 0
    assert frame.right.index.tip is None and frame.right.thumb.cmc is None
    assert frame.right.middle.pip is None
    arrays = frame.right.as_arrays()
    assert arrays.valid[0] and not arrays.valid[HandJointName.INDEX_TIP.row]
    assert np.isnan(arrays.points[HandJointName.INDEX_TIP.row]).all()


def test_joint_pixels_are_continuous_unclipped_and_use_raw_dimensions():
    joint = HandJoint("index_tip", .25, .6, .9)
    assert joint.to_pixels(640, 480) == (160, 288)
    assert joint.xy == (.25, .6)
    assert HandJoint("wrist", 1.1, -.1, .8).to_pixels(100, 200) == pytest.approx((110, -20))
    for width, height in ((0, 480), (640, -1), (np.nan, 480), (640, np.inf)):
        with pytest.raises(ValueError, match="dimensions"):
            joint.to_pixels(width, height)


def test_legacy_embedded_hands_share_the_same_side_and_finger_api():
    message = face_tracking_pb2.FaceAndHandTrackingFrame(source_timestamp=5)
    message.hand_pose.source_timestamp = 4.9
    message.hand_pose.right_hand.joints.add(name="thumb_tip", x=.2, y=.8, confidence=.9)
    frame = FaceAndHandTrackingDataSubscriber.decode(message.SerializeToString())
    assert frame.left is None and frame.right is frame.right_hand
    assert frame.right.side == HandSide.RIGHT
    assert frame.right.thumb.tip is frame.hand_pose.right.thumb.tip
    assert frame.hand_pose.timestamp == 4.9
