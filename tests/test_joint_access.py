"""Joint API regression checks: stable rows, missing samples and coordinate composition."""
import numpy as np
import pytest

from asmagic import (ARBodyDataSubscriber, ARBodyFrame, BodyCoordinateSpace,
                     BodyJointName, BodyJoints, FaceAndHandTrackingDataSubscriber,
                     Hand, HandJoint, HandJointName, HandJoints, HandPoseDataSubscriber,
                     JointTransform, BODY_JOINT_NAMES, HAND_JOINT_NAMES)
from asmagic.proto import armpose_msg_pb2, hand_pose_pb2, face_tracking_pb2


def body_message():
    message = armpose_msg_pb2.Armpose(tracking_state="tracking")
    message.joints["left_hand_joint"].position.x = 2
    message.joints["left_hand_joint"].rotation.w = 1
    message.local_joints["left_hand_joint"].position.y = 3
    message.local_joints["left_hand_joint"].rotation.w = 1
    message.tracked_joints["left_hand_joint"] = False
    message.joint_parents["left_hand_joint"] = "left_forearm_joint"
    return message


def test_typed_access_keeps_dictionary_behavior_and_missing_nodes():
    frame = ARBodyDataSubscriber.decode(body_message().SerializeToString())
    assert isinstance(frame.joints, BodyJoints)
    joint = frame.joints.left_hand
    assert joint is frame.joints["left_hand_joint"]
    assert joint is frame.joints[BodyJointName.LEFT_HAND]
    assert frame.joints.right_hand is None
    assert frame.local_joints.left_hand.position[1] == 3
    assert dict(frame.joints)["left_hand_joint"] is joint
    frame.joints[BodyJointName.RIGHT_HAND] = joint
    assert frame.joints.right_hand is joint
    with pytest.raises(AttributeError):
        _ = frame.joints.left_hnad
    with pytest.raises(AttributeError, match="read-only"):
        frame.joints.left_hand = joint


def test_manual_construction_and_every_declared_accessor():
    transform = JointTransform(np.zeros(3, dtype=np.float32), np.array([0, 0, 0, 1], dtype=np.float32))
    frame = ARBodyFrame(joints={name: transform for name in BODY_JOINT_NAMES})
    assert len(BODY_JOINT_NAMES) == 91 and len(set(BODY_JOINT_NAMES)) == 91
    for name, accessor in vars(BodyJoints).items():
        if hasattr(accessor, "name"):
            assert getattr(frame.joints, name) is transform
    hand = Hand(.9, {name: HandJoint(name, .2, .8, .9) for name in HAND_JOINT_NAMES})
    assert isinstance(hand.joints, HandJoints)
    assert len(HAND_JOINT_NAMES) == 21
    for name, accessor in vars(HandJoints).items():
        if hasattr(accessor, "name"):
            assert getattr(hand.joints, name) is hand.joints[accessor.name]


def test_body_arrays_have_fixed_rows_masks_parents_and_independent_storage():
    message = body_message()
    message.joints["hips_joint"].rotation.w = 1
    message.tracked_joints["hips_joint"] = True
    frame = ARBodyDataSubscriber.decode(message.SerializeToString())
    body = frame.skeleton()
    left = BodyJointName.LEFT_HAND.row
    hips = BodyJointName.HIPS.row
    right = BodyJointName.RIGHT_HAND.row
    assert body.names == BODY_JOINT_NAMES
    assert body.positions.shape == (91, 3) and body.rotations.shape == (91, 4)
    assert body.positions.dtype == body.rotations.dtype == np.float32
    assert body.valid.dtype == body.tracked.dtype == bool
    np.testing.assert_equal(body.positions[left], [2, 0, 0])
    np.testing.assert_equal(body.rotations[left], [0, 0, 0, 1])
    assert body.valid[left] and body.valid.sum() == 2
    assert body.tracking_known[left] and not body.tracked[left]
    assert body.tracked[hips] and not body.tracking_known[right]
    assert body.parent_indices[left] == BodyJointName.LEFT_FOREARM.row
    assert body.parent_indices[hips] == -1
    assert body.parent_indices.dtype == np.int32
    assert np.isnan(body.positions[right]).all() and not body.valid[right]
    assert body.matrices.shape == (91, 4, 4) and np.isnan(body.matrices[right]).all()
    body.positions[left, 0] = 100
    assert frame.joints.left_hand.position[0] == 2
    empty = ARBodyFrame().skeleton()
    assert empty.names == body.names and empty.positions.shape == (91, 3)
    assert not empty.valid.any() and np.isnan(empty.positions).all()


def test_world_and_parent_exports_do_not_fall_back_to_model_coordinates():
    message = body_message()
    frame = ARBodyDataSubscriber.decode(message.SerializeToString())
    world = frame.skeleton(BodyCoordinateSpace.WORLD)
    assert not world.valid.any() and np.isnan(world.positions).all()
    parent = frame.skeleton(BodyCoordinateSpace.PARENT)
    np.testing.assert_equal(parent.positions[BodyJointName.LEFT_HAND.row], [0, 3, 0])
    assert parent.space is BodyCoordinateSpace.PARENT
    assert not ARBodyFrame(joints=frame.joints).skeleton(BodyCoordinateSpace.PARENT).valid.any()
    with pytest.raises(ValueError):
        frame.skeleton("camera")


def test_world_export_composes_position_and_noncommuting_quaternions():
    message = body_message()
    # Anchor rotates 90 degrees about Z; joint rotates 90 degrees about X.
    message.body_transform.position.x = 10
    message.body_transform.rotation.z = np.sqrt(.5)
    message.body_transform.rotation.w = np.sqrt(.5)
    message.joints["left_hand_joint"].rotation.x = np.sqrt(.5)
    message.joints["left_hand_joint"].rotation.w = np.sqrt(.5)
    frame = ARBodyDataSubscriber.decode(message.SerializeToString())
    world = frame.skeleton(BodyCoordinateSpace.WORLD)
    left = BodyJointName.LEFT_HAND.row
    np.testing.assert_allclose(world.positions[left], [10, 2, 0], atol=1e-6)
    np.testing.assert_allclose(world.rotations[left], [.5, .5, .5, .5], atol=1e-6)
    np.testing.assert_allclose(world.matrices[left], frame.joint_world_matrix(BodyJointName.LEFT_HAND), atol=1e-6)


def test_unknown_body_nodes_are_preserved_and_share_rows_across_spaces():
    message = body_message()
    message.joints["future_z_joint"].rotation.w = 1
    message.local_joints["future_a_joint"].rotation.w = 1
    frame = ARBodyDataSubscriber.decode(message.SerializeToString())
    body = frame.skeleton()
    parent = frame.skeleton(BodyCoordinateSpace.PARENT)
    assert body.names == parent.names == BODY_JOINT_NAMES + ("future_a_joint", "future_z_joint")
    assert body.positions.shape == (93, 3)
    np.testing.assert_equal(body.valid[-2:], [False, True])
    np.testing.assert_equal(parent.valid[-2:], [True, False])
    assert "future_z_joint" in frame.joints


def test_hand_arrays_keep_missing_rows_and_legacy_compact_points():
    message = hand_pose_pb2.HandPoseFrame(source_timestamp=4)
    # Deliberately out of canonical order; zero is a real measurement.
    message.left_hand.joints.add(name="index_tip", x=.4, y=.2, confidence=.1)
    message.left_hand.joints.add(name="wrist", x=0, y=0, confidence=0)
    frame = HandPoseDataSubscriber.decode(message.SerializeToString())
    hand = frame.left_hand
    assert hand.joints.wrist is hand.joints[HandJointName.WRIST]
    assert hand.joints.middle_tip is None and frame.right_hand is None
    compact = hand.points
    assert compact.shape == (2, 2) and compact[0, 0] == pytest.approx(.4)
    bulk = hand.as_arrays()
    assert bulk.names == HAND_JOINT_NAMES
    assert bulk.points.shape == (21, 2) and bulk.confidences.shape == (21,)
    assert bulk.points.dtype == bulk.confidences.dtype == np.float32
    assert bulk.valid.dtype == bool and bulk.valid.sum() == 2
    wrist = HandJointName.WRIST.row
    tip = HandJointName.INDEX_TIP.row
    middle = HandJointName.MIDDLE_TIP.row
    np.testing.assert_equal(bulk.points[wrist], [0, 0])
    assert bulk.valid[wrist] and bulk.confidences[wrist] == 0
    assert bulk.confidences[tip] == pytest.approx(.1)  # no implicit threshold
    assert not bulk.valid[middle] and np.isnan(bulk.points[middle]).all()
    assert np.isnan(bulk.confidences[middle])
    bulk.points[wrist, 0] = 10
    assert hand.joints.wrist.x == 0


def test_empty_and_extended_hands_and_face_hand_use_the_same_api():
    empty = Hand(.5, {}).as_arrays()
    assert empty.points.shape == (21, 2) and not empty.valid.any()
    hand = Hand(.5, {"future_joint": HandJoint("future_joint", .3, .7, .8)})
    bulk = hand.as_arrays()
    assert bulk.names == HAND_JOINT_NAMES + ("future_joint",)
    assert bulk.valid[-1] and bulk.points.shape == (22, 2)
    message = face_tracking_pb2.FaceAndHandTrackingFrame(source_timestamp=5)
    message.hand_pose.source_timestamp = 4.9
    message.hand_pose.right_hand.joints.add(name="wrist", x=.2, y=.8, confidence=.9)
    frame = FaceAndHandTrackingDataSubscriber.decode(message.SerializeToString())
    assert frame.hands.timestamp == 4.9 and frame.timestamp == 5
    assert frame.left_hand is None
    assert frame.right_hand.joints.wrist.x == pytest.approx(.2)
    assert frame.right_hand.as_arrays().valid[HandJointName.WRIST.row]
