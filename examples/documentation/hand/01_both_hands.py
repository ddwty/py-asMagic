from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def print_hand_joints(side, hand):
    print(f"\n{side} hand:")
    if hand is None:
        print("  Not detected")
        return

    # Select the wrist and all four joints of each of the five fingers.
    named_joints = [
        ("Wrist", hand.wrist),
        ("Thumb palm base (CMC)", hand.thumb.cmc),
        ("Thumb knuckle (MP)", hand.thumb.mp),
        ("Thumb middle joint (IP)", hand.thumb.ip),
        ("Thumb fingertip", hand.thumb.tip),
        ("Index knuckle (MCP)", hand.index.mcp),
        ("Index middle joint (PIP)", hand.index.pip),
        ("Index joint near fingertip (DIP)", hand.index.dip),
        ("Index fingertip", hand.index.tip),
        ("Middle knuckle (MCP)", hand.middle.mcp),
        ("Middle middle joint (PIP)", hand.middle.pip),
        ("Middle joint near fingertip (DIP)", hand.middle.dip),
        ("Middle fingertip", hand.middle.tip),
        ("Ring knuckle (MCP)", hand.ring.mcp),
        ("Ring middle joint (PIP)", hand.ring.pip),
        ("Ring joint near fingertip (DIP)", hand.ring.dip),
        ("Ring fingertip", hand.ring.tip),
        ("Little knuckle (MCP)", hand.little.mcp),
        ("Little middle joint (PIP)", hand.little.pip),
        ("Little joint near fingertip (DIP)", hand.little.dip),
        ("Little fingertip", hand.little.tip),
    ]
    for location, hand_joint in named_joints:
        if hand_joint is None:
            print(f"  {location}: not detected")
        else:
            print(f"  {location}: (x, y)={hand_joint.xy}, "
                  f"confidence={hand_joint.confidence}")


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("\nTime:", frame.timestamp)
            print_hand_joints("Left", frame.left)
            print_hand_joints("Right", frame.right)
            if frame.unknown_hand_count:
                print("Hands with unassigned side:", frame.unknown_hand_count)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
