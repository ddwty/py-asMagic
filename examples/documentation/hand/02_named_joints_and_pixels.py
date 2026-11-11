from asmagic import HandPoseDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def print_hand_pixels(side, hand, width, height):
    print(f"\n{side} hand:")
    if hand is None:
        print("  Not detected")
        return

    named_joints = [
        ("Wrist", hand.wrist),
        ("Thumb fingertip", hand.thumb.tip),
        ("Index fingertip", hand.index.tip),
        ("Middle fingertip", hand.middle.tip),
        ("Ring fingertip", hand.ring.tip),
        ("Little fingertip", hand.little.tip),
    ]
    for location, hand_joint in named_joints:
        if hand_joint is None:
            print(f"  {location}: not detected")
            continue
        print(f"  {location}: normalized (x, y)={hand_joint.xy}")
        if width > 0 and height > 0:
            print(f"  {location}: pixels (x, y)="
                  f"{hand_joint.to_pixels(width, height)}")


def main():
    sub = HandPoseDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            width, height = frame.image_width, frame.image_height
            print("\nTime:", frame.timestamp)
            print("Image size (width, height):", (width, height))
            if width <= 0 or height <= 0:
                print("Image size unavailable; printing normalized coordinates only")
            print_hand_pixels("Left", frame.left, width, height)
            print_hand_pixels("Right", frame.right, width, height)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
