"""Decode the app's native body streams; validate identity and space availability."""
from typing import Optional

import numpy as np
from google.protobuf.message import DecodeError

from .body_tracking import (ARKIT_JOINT_NAMES, ARKIT_JOINT_NAMES_BY_WIRE, MEDIAPIPE_BONES,
                            MEDIAPIPE_JOINT_NAMES, BodyTrackingFrame, BodyTrackingJoint,
                            BodyTrackingJoints, BodyTrackingModel, BodyTrackingPerson)
from .joints import BODY_JOINT_NAMES
from .tracking_types import JointTransform
from .proto import armpose_msg_pb2, multi_person_pose_pb2


def _vector(value) -> np.ndarray:
    result = np.array([value.x, value.y, value.z], dtype=np.float32)
    if not np.isfinite(result).all():
        raise ValueError("Body positions must be finite")
    return result


def _rotation(value) -> Optional[np.ndarray]:
    q = np.array([value.x, value.y, value.z, value.w], dtype=np.float32)
    if not np.isfinite(q).all():
        raise ValueError("Body rotations must be finite")
    return q if np.linalg.norm(q) > 0 else None


def _transform(value) -> Optional[JointTransform]:
    if not value.HasField("position") or not value.HasField("rotation"):
        return None
    p, q = _vector(value.position), _rotation(value.rotation)
    return JointTransform(p, q) if q is not None else None


def _matrix(values, size: int) -> np.ndarray:
    if len(values) != size * size or not np.isfinite(values).all():
        raise ValueError("Body camera metadata has an invalid matrix")
    # Swift serializes columns; numpy's default reshape order is rows.
    return np.array(values, dtype=np.float32).reshape(size, size, order="F").copy()


def _compose_rotation(anchor: np.ndarray, joint: np.ndarray) -> np.ndarray:
    a, b = anchor / np.linalg.norm(anchor), joint / np.linalg.norm(joint)
    return np.r_[a[3] * b[:3] + b[3] * a[:3] + np.cross(a[:3], b[:3]),
                 a[3] * b[3] - np.dot(a[:3], b[:3])].astype(np.float32)


def _arkit(message) -> BodyTrackingFrame:
    if message.tracking_state not in ("tracking", "searching", "interrupted", "unavailable", "failed"):
        raise ValueError("Expected native ARKit body tracking data on port 8100")
    frame = BodyTrackingFrame(BodyTrackingModel.ARKIT, message.timestamp, message.source_timestamp,
                              message.session_id, message.session_id, message.tracking_state,
                              model_name="arkit.body_tracking", protobuf=message)
    if message.tracking_state != "tracking":
        return frame
    if not set(BODY_JOINT_NAMES).issubset(message.joints):
        raise ValueError("Native ARKit frames must contain their complete 91-node skeleton")
    world = _transform(message.body_transform) if message.HasField("body_transform") else None
    joints = BodyTrackingJoints()
    name_map = dict(ARKIT_JOINT_NAMES_BY_WIRE)
    # Keep extensions even though they do not have a known anatomical mapping.
    for name in set(message.joints) | set(message.local_joints):
        name_map.setdefault(name, name)
    for native, value in message.joints.items():
        name = name_map[native]
        p = _vector(value.position) if value.HasField("position") else None
        q = _rotation(value.rotation) if value.HasField("rotation") else None
        joint = BodyTrackingJoint(name, native, position=p, rotation=q,
                                  tracked=message.tracked_joints.get(native) if native in message.tracked_joints else None)
        if world is not None:
            if p is not None:
                joint.world_position = (world.matrix @ np.r_[p, 1])[:3].astype(np.float32)
            if q is not None:
                joint.world_rotation = _compose_rotation(world.rotation, q)
        joints[name] = joint
    for native, value in message.local_joints.items():
        name = name_map[native]
        joint = joints.setdefault(name, BodyTrackingJoint(name, native))
        joint.parent_position = _vector(value.position) if value.HasField("position") else None
        joint.parent_rotation = _rotation(value.rotation) if value.HasField("rotation") else None
    parents = {name_map.get(child, child): name_map.get(parent, parent)
               for child, parent in message.joint_parents.items() if child != parent}
    names = ARKIT_JOINT_NAMES + tuple(sorted(set(joints).difference(ARKIT_JOINT_NAMES)))
    person = BodyTrackingPerson("body", 1, BodyTrackingModel.ARKIT, "arkit.body_91.v1", "body_slot",
                                joints, names, tuple((p, c) for c, p in parents.items()), parents,
                                body_transform=world, metric_scale=message.estimated_scale,
                                protobuf=message)
    frame.people = (person,)
    return frame


def _mediapipe(message) -> BodyTrackingFrame:
    if message.schema_version != 1 or not message.model.startswith("mediapipe."):
        raise ValueError("Expected MediaPipe MultiPersonPoseFrame schema version 1 on port 8104")
    if not message.session_id or not message.world_frame_id:
        raise ValueError("MediaPipe session and world frame IDs are required")
    if message.camera_tracking not in ("normal", "limited", "unavailable", "interrupted", "failed", "stopped"):
        raise ValueError("MediaPipe camera tracking state is invalid")
    ids = [person.id for person in message.people]
    if not all(ids) or len(set(ids)) != len(ids):
        raise ValueError("Each person must have a nonempty, distinct session-scoped ID")
    if len(ids) > 6:
        raise ValueError("MediaPipe schema v1 supports at most six people per frame")
    camera_world = _matrix(message.camera_world_transform, 4)
    intrinsics = _matrix(message.camera_intrinsics, 3)
    if message.image_width == 0 or message.image_height == 0:
        raise ValueError("MediaPipe image dimensions must be positive")
    people = []
    for person in message.people:
        landmarks = {joint.index: joint for joint in person.landmarks}
        if len(person.landmarks) != 33 or set(landmarks) != set(range(33)):
            raise ValueError("Each MediaPipe person must have exactly 33 distinct indices, 0 through 32")
        has_camera, has_world = person.HasField("body_camera"), person.HasField("body_world")
        if has_camera != has_world or (has_world and message.camera_tracking != "normal"):
            raise ValueError("World registration requires both body transforms and normal camera tracking")
        body_camera = _transform(person.body_camera) if has_camera else None
        body_world = _transform(person.body_world) if has_world else None
        if has_world and (body_world is None or body_camera is None):
            raise ValueError("Registered body transforms require positions and nonzero quaternions")
        joints = BodyTrackingJoints()
        for index, name in enumerate(MEDIAPIPE_JOINT_NAMES):
            value = landmarks[index]
            if not value.HasField("local") or not value.HasField("model"):
                raise ValueError("MediaPipe local and model positions are required for all 33 landmarks")
            if value.HasField("camera") != has_camera or value.HasField("world") != has_world:
                raise ValueError("Landmark camera/world availability must match body registration")
            if not (0 <= value.visibility <= 1 and 0 <= value.presence <= 1):
                raise ValueError("MediaPipe visibility and presence must be between zero and one")
            image = np.array([value.image_x, value.image_y], dtype=np.float32)
            if not np.isfinite(image).all():
                raise ValueError("Image positions must be finite")
            depth = value.measured_depth if value.HasField("measured_depth") else None
            if depth is not None and (not np.isfinite(depth) or not 0.25 <= depth <= 8):
                raise ValueError("Measured scene depth must be finite and within the sender's accepted range")
            joints[name] = BodyTrackingJoint(
                name, name, index, position=_vector(value.local),
                camera_position=_vector(value.camera) if has_camera else None,
                world_position=_vector(value.world) if has_world else None,
                model_position=_vector(value.model), image_position=image,
                visibility=value.visibility, presence=value.presence, measured_depth=depth)
        fit = person.fit_rms if person.HasField("fit_rms") else None
        if not np.isfinite(person.metric_scale) or not 0.65 <= person.metric_scale <= 1.5:
            raise ValueError("Metric scale is outside the sender's accepted range")
        if fit is not None and (not np.isfinite(fit) or fit < 0):
            raise ValueError("Fit RMS must be finite and nonnegative")
        people.append(BodyTrackingPerson(
            person.id, person.label, BodyTrackingModel.MEDIAPIPE, "mediapipe.pose_33.v1", "session_track",
            joints, MEDIAPIPE_JOINT_NAMES,
            tuple((MEDIAPIPE_JOINT_NAMES[a], MEDIAPIPE_JOINT_NAMES[b]) for a, b in MEDIAPIPE_BONES),
            body_transform=body_world, body_camera_transform=body_camera,
            identity_ambiguous=person.identity_ambiguous, metric_scale=person.metric_scale, fit_rms=fit,
            depth_joint_count=person.depth_joint_count, robot_eligible=person.robot_eligible, protobuf=person))
    state = ("tracking" if people else "searching") if message.camera_tracking == "normal" else message.camera_tracking
    return BodyTrackingFrame(
        BodyTrackingModel.MEDIAPIPE, message.timestamp, message.source_timestamp,
        message.session_id, message.world_frame_id, state, tuple(people),
        selected_person_id=message.selected_person_id or None, model_name=message.model,
        schema_version=message.schema_version, sequence=message.sequence,
        camera_world_transform=camera_world, camera_intrinsics=intrinsics,
        image_width=message.image_width, image_height=message.image_height,
        camera_tracking=message.camera_tracking, has_scene_depth=message.has_scene_depth, protobuf=message)


def decode_body_tracking(payload: bytes, model: BodyTrackingModel) -> BodyTrackingFrame:
    if len(payload) > 128_000:
        raise ValueError("Body frame exceeds the native protocol's size limit")
    message = (armpose_msg_pb2.Armpose() if model == BodyTrackingModel.ARKIT
               else multi_person_pose_pb2.MultiPersonPoseFrame())
    try:
        message.ParseFromString(payload)
    except DecodeError as error:
        name = "ARKit" if model == BodyTrackingModel.ARKIT else "MediaPipe"
        raise ValueError("Unable to parse native {} body data; match the App recognition model".format(name)) from error
    if not np.isfinite([message.timestamp, message.source_timestamp]).all():
        raise ValueError("Body timestamps must be finite")
    return _arkit(message) if model == BodyTrackingModel.ARKIT else _mediapipe(message)
