"""Export explicitly synthetic plot previews; this does not connect to the App."""
import argparse
from pathlib import Path

from asmagic import ARBodyDataSubscriber, HandPoseDataSubscriber, TrackingPlotter, HAND_JOINT_NAMES
from asmagic.proto import armpose_msg_pb2, hand_pose_pb2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="reports", help="Output PNG directory")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    message = armpose_msg_pb2.Armpose(tracking_state="tracking", session_id="synthetic-preview")
    joints = {
        "hips_joint": ((0, 0, 0), None), "spine_3_joint": ((0, .28, 0), "hips_joint"),
        "spine_7_joint": ((0, .59, 0), "spine_3_joint"), "neck_1_joint": ((0, .72, 0), "spine_7_joint"),
        "head_joint": ((0, .92, 0), "neck_1_joint"),
        "left_shoulder_1_joint": ((-.18, .59, 0), "spine_7_joint"),
        "left_arm_joint": ((-.23, .58, 0), "left_shoulder_1_joint"),
        "left_forearm_joint": ((-.45, .35, .03), "left_arm_joint"),
        "left_hand_joint": ((-.59, .50, .08), "left_forearm_joint"),
        "right_shoulder_1_joint": ((.18, .59, 0), "spine_7_joint"),
        "right_arm_joint": ((.23, .58, 0), "right_shoulder_1_joint"),
        "right_forearm_joint": ((.46, .35, .02), "right_arm_joint"),
        "right_hand_joint": ((.54, .14, .06), "right_forearm_joint"),
        "left_upLeg_joint": ((-.12, -.08, 0), "hips_joint"),
        "left_leg_joint": ((-.14, -.49, .02), "left_upLeg_joint"),
        "left_foot_joint": ((-.14, -.9, 0), "left_leg_joint"),
        "left_toes_joint": ((-.14, -.93, .14), "left_foot_joint"),
        "right_upLeg_joint": ((.12, -.08, 0), "hips_joint"),
        "right_leg_joint": ((.14, -.49, .01), "right_upLeg_joint"),
        "right_foot_joint": ((.14, -.9, 0), "right_leg_joint"),
        "right_toes_joint": ((.14, -.93, .14), "right_foot_joint"),
    }
    for name, (position, parent) in joints.items():
        joint = message.joints[name]
        joint.position.x, joint.position.y, joint.position.z = position
        joint.rotation.w = 1
        message.tracked_joints[name] = name not in ("spine_3_joint", "left_toes_joint", "right_toes_joint")
        if parent:
            message.joint_parents[name] = parent
    body = ARBodyDataSubscriber.decode(message.SerializeToString())
    with TrackingPlotter() as plot:
        plot.update(body)
        plot.figure.suptitle("Synthetic fixture - not a device capture", fontsize=10)
        plot.save(output / "body-preview.png", dpi=150)

    message = hand_pose_pb2.HandPoseFrame(source_timestamp=1, image_width=1920, image_height=1080)
    points = [(.45, .85), (.34, .75), (.23, .65), (.14, .58), (.09, .51),
              (.37, .59), (.34, .4), (.33, .27), (.32, .16),
              (.49, .55), (.49, .32), (.49, .18), (.49, .08),
              (.60, .58), (.63, .36), (.65, .23), (.67, .14),
              (.70, .64), (.78, .49), (.83, .38), (.87, .30)]
    for side, hand in (("left", message.left_hand), ("right", message.right_hand)):
        hand.confidence = .95
        for name, (x, y) in zip(HAND_JOINT_NAMES, points):
            hand.joints.add(name=name, x=x if side == "left" else 1 - x, y=y, confidence=.95)
    with TrackingPlotter() as plot:
        plot.update(HandPoseDataSubscriber.decode(message.SerializeToString()))
        plot.figure.suptitle("Synthetic fixture - not a device capture", fontsize=10)
        plot.save(output / "hands-preview.png", dpi=150)
    print((output / "body-preview.png").resolve())
    print((output / "hands-preview.png").resolve())


if __name__ == "__main__":
    main()
