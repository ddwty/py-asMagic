"""Native body contracts: anatomy, identity, coordinate presence and transport."""
from pathlib import Path
import runpy

import numpy as np
import pytest

from asmagic import (BodyTrackingDataSubscriber, BodyTrackingFrame, BodyTrackingModel,
                     CommonBodyJointName, COMMON_BODY_JOINT_NAMES, ARKIT_JOINT_NAMES,
                     MEDIAPIPE_JOINT_NAMES, TrackingPlotter, subscribe)
from asmagic.joints import BODY_JOINT_NAMES
from asmagic.proto import armpose_msg_pb2, multi_person_pose_pb2

FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]


def native(name="swift_body_people.bin"):
    return BodyTrackingFrame.from_bytes((FIXTURES / name).read_bytes(), model="mediapipe")


def arkit_message():
    message = armpose_msg_pb2.Armpose(timestamp=123, source_timestamp=42,
                                     session_id="arkit-session", tracking_state="tracking", estimated_scale=1)
    for name in BODY_JOINT_NAMES:
        message.joints[name].position.x = 0
        message.joints[name].rotation.w = 1
        message.tracked_joints[name] = True
    message.joints["left_arm_joint"].position.x = .2
    message.joints["left_forearm_joint"].position.x = .4
    message.joints["left_hand_joint"].position.x = .6
    message.joints["left_hand_joint"].rotation.x = np.sqrt(.5)
    message.joints["left_hand_joint"].rotation.w = np.sqrt(.5)
    message.local_joints["left_hand_joint"].position.y = .3
    message.local_joints["left_hand_joint"].rotation.w = 1
    message.joint_parents["left_hand_joint"] = "left_forearm_joint"
    message.body_transform.position.x = 10
    message.body_transform.rotation.z = np.sqrt(.5)
    message.body_transform.rotation.w = np.sqrt(.5)
    message.tracked_joints["left_hand_joint"] = False
    return message


def test_swift_native_people_keep_all_nodes_and_independent_availability():
    frame = native()
    assert frame.model == BodyTrackingModel.MEDIAPIPE
    assert frame.person_count == 2 and frame.is_tracking
    assert frame.timestamp == 1_800_000_000 and frame.source_timestamp == 123.25
    assert frame.session_id == "swift-body-session" and frame.world_frame_id == "swift-world-1"
    assert frame.sequence == 7 and frame.schema_version == 1
    np.testing.assert_equal(frame.camera_world_transform[:3, 3], [10, 0, 0])
    np.testing.assert_equal(frame.camera_intrinsics, [[600, 0, 320], [0, 600, 240], [0, 0, 1]])
    person = frame.person("person-a")
    assert person.identity_kind == "session_track" and person.has_world_coordinates
    wrist = person.joints.left_wrist
    assert wrist is person.joints["left_wrist"] and wrist.native_index == 15
    np.testing.assert_allclose(wrist.position, [.6, .3, 0])
    np.testing.assert_allclose(wrist.world_position, [10.6, .3, -2], atol=1e-6)
    assert wrist.rotation is None and wrist.tracked is None and not wrist.usable
    assert wrist.visibility == pytest.approx(.2) and wrist.presence == pytest.approx(.8)
    assert person.joints.head is None
    bulk = person.skeleton()
    assert bulk.names == MEDIAPIPE_JOINT_NAMES and bulk.positions.shape == (33, 3)
    assert bulk.valid.all() and not bulk.usable[15]  # low scores do not remove a node
    assert not bulk.rotation_valid.any() and np.isnan(bulk.rotations).all()
    assert not bulk.tracking_known.any() and not bulk.tracked.any()
    np.testing.assert_equal(bulk.native_indices, np.arange(33))
    assert (bulk.parent_indices == -1).all() and bulk.bones.shape == (35, 2)
    assert person.fit_rms == pytest.approx(.03) and person.depth_joint_count == 4
    assert person.joints.left_shoulder.measured_depth == 2


def test_id_lookup_survives_reordering_and_never_substitutes_a_lost_person():
    first, reordered, lost = native(), native("swift_body_reordered.bin"), native("swift_body_empty.bin")
    assert first.people[0].id == "person-a" and reordered.people[0].id == "person-b"
    assert reordered.person("person-a").id == first.selected_person.id
    assert reordered.selected_person is reordered.person("person-a")
    assert lost.people == () and lost.person_count == 0 and not lost.is_tracking
    assert lost.person("person-a") is None and lost.selected_person is None
    assert lost.tracking_state == "interrupted"
    message = multi_person_pose_pb2.MultiPersonPoseFrame.FromString(first.protobuf.SerializeToString())
    del message.people[:1]
    remaining = BodyTrackingFrame.from_bytes(message.SerializeToString(), model="mediapipe")
    assert remaining.person("person-a") is None and remaining.selected_person is None
    assert remaining.person("person-b") is not None


def test_missing_world_never_falls_back_and_arrays_do_not_mutate_the_frame():
    person = native("swift_body_local.bin").people[0]
    assert not person.has_world_coordinates and person.joints.left_wrist.world_position is None
    assert person.body_transform is None and person.fit_rms is None
    for space in ("world", "camera", "parent"):
        bulk = person.skeleton(space)
        assert not bulk.valid.any() and np.isnan(bulk.positions).all()
    image = person.skeleton("image")
    assert image.positions.shape == (33, 2) and image.valid.all()
    assert not image.rotation_valid.any()
    body = person.skeleton()
    body.positions[15, 0] = 100
    assert person.joints.left_wrist.position[0] == pytest.approx(.6)
    with pytest.raises(ValueError, match="layout"):
        person.skeleton(layout="unknown")


def test_arkit_anatomical_mapping_full_nodes_and_world_rotation():
    message = arkit_message()
    frame = BodyTrackingFrame.from_bytes(message.SerializeToString(), model="arkit")
    assert frame.person_count == 1 and frame.people[0].identity_kind == "body_slot"
    assert frame.people[0].id == "body" and frame.selected_person is None
    assert frame.sequence is None and frame.camera_world_transform is None
    person = frame.people[0]
    assert person.skeleton().names == ARKIT_JOINT_NAMES and len(person.joints) == 91
    np.testing.assert_allclose(person.joints.left_shoulder.position, [.2, 0, 0])
    np.testing.assert_allclose(person.joints.left_elbow.position, [.4, 0, 0])
    wrist = person.joints.left_wrist
    assert wrist.native_name == "left_hand_joint" and wrist.native_index is None
    assert wrist.tracked is False and wrist.visibility is None and not wrist.usable
    np.testing.assert_allclose(wrist.world_position, [10, .6, 0], atol=1e-6)
    np.testing.assert_allclose(wrist.world_rotation, [.5, .5, .5, .5], atol=1e-6)
    np.testing.assert_allclose(wrist.parent_position, [0, .3, 0])
    bulk = person.skeleton(layout="common")
    assert bulk.names == COMMON_BODY_JOINT_NAMES and bulk.positions.shape == (12, 3)
    assert bulk.valid.all() and bulk.rotation_valid.all() and bulk.tracking_known.all()
    assert not bulk.tracked[CommonBodyJointName.LEFT_WRIST.row]
    mp = native().people[0].skeleton(layout="common")
    assert mp.names == bulk.names and mp.positions.shape == bulk.positions.shape
    assert mp.native_indices[CommonBodyJointName.LEFT_WRIST.row] == 15
    assert not mp.rotation_valid.any()
    parent = person.skeleton("parent")
    assert parent.valid.sum() == 1  # no body-space substitution for missing local transforms
    message.ClearField("body_transform")
    assert not BodyTrackingFrame.from_bytes(message.SerializeToString(), model="arkit").people[0].skeleton("world").valid.any()


@pytest.mark.parametrize("mutation,match", [
    (lambda m: setattr(m, "schema_version", 2), "version"),
    (lambda m: setattr(m.people[1], "id", "person-a"), "distinct"),
    (lambda m: m.people[0].landmarks.pop(), "33"),
    (lambda m: setattr(m.people[0].landmarks[1], "index", 0), "33"),
    (lambda m: m.people[0].landmarks[15].ClearField("world"), "availability"),
    (lambda m: setattr(m.people[0].landmarks[15], "visibility", float("nan")), "visibility"),
    (lambda m: setattr(m, "camera_tracking", "limited"), "registration"),
])
def test_invalid_native_packets_are_rejected(mutation, match):
    message = multi_person_pose_pb2.MultiPersonPoseFrame.FromString((FIXTURES / "swift_body_people.bin").read_bytes())
    mutation(message)
    with pytest.raises(ValueError, match=match):
        BodyTrackingFrame.from_bytes(message.SerializeToString(), model="mediapipe")


def test_wrong_model_and_incomplete_arkit_skeleton_are_rejected():
    with pytest.raises(ValueError, match="ARKit"):
        BodyTrackingFrame.from_bytes((FIXTURES / "swift_body_people.bin").read_bytes(), model="arkit")
    message = arkit_message()
    del message.joints["root"]
    with pytest.raises(ValueError, match="91"):
        BodyTrackingFrame.from_bytes(message.SerializeToString(), model="arkit")


@pytest.mark.parametrize("model", ["mediapipe", "arkit"])
def test_native_model_receivers_transport_timeout_raw_frame_and_close(publisher, model):
    socket, connect = publisher
    sub = connect(BodyTrackingDataSubscriber, model=model)
    payload = (FIXTURES / "swift_body_people.bin").read_bytes() if model == "mediapipe" else arkit_message().SerializeToString()
    assert sub.receive(timeout=0) is None
    socket.send(payload)
    frame = sub.receive(timeout=2000)
    assert frame is not None and frame.model.value == model
    assert sub.received_frames == 1 and sub.decode(payload).person_count == frame.person_count
    assert sub.get(timeout=0) is None
    socket.send(payload)
    assert sub.receive(timeout=2000).protobuf == sub._message_type.FromString(payload)
    sub.close()
    assert sub.get() is None
    with pytest.raises(StopIteration):
        sub.receive()


def test_factory_uses_explicit_model_and_correct_native_port():
    for model, port in (("arkit", 8100), ("mediapipe", 8104)):
        with subscribe("body", "127.0.0.1", model=model) as sub:
            assert sub.port == port and sub.model.value == model


def test_multi_person_plot_reorders_panels_and_clears_world_and_loss():
    import matplotlib
    matplotlib.use("Agg", force=True)
    with TrackingPlotter(space="world", labels=True, min_confidence=.5) as plot:
        plot.update(native(), force=True)
        assert len(plot.axes) == 2
        assert len(plot._artists[0][0]._offsets3d[0]) == 32
        plot.update(native("swift_body_reordered.bin"), force=True)
        assert "person-b" in plot.axes[0].get_title()
        plot.update(native("swift_body_local.bin"), force=True)
        assert len(plot.axes) == 1 and not len(plot._artists[0][0]._offsets3d[0])
        plot.update(native("swift_body_empty.bin"), force=True)
        assert not len(plot._artists[0][0]._offsets3d[0]) and not plot._texts


def test_body_stream_plot_yields_the_same_complete_frame(publisher):
    import matplotlib
    matplotlib.use("Agg", force=True)
    socket, connect = publisher
    sub = connect(BodyTrackingDataSubscriber, model="mediapipe")
    socket.send((FIXTURES / "swift_body_people.bin").read_bytes())
    stream = sub.stream(timeout=2000, plot=True)
    try:
        assert next(stream).person_count == 2 and sub.received_frames == 1
    finally:
        stream.close()
