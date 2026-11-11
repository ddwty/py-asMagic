from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive(timeout=1000)
            if frame is None:
                print("No frame within 1000 ms")
                continue
            print("Time:", frame.timestamp)
            print("Received frames:", sub.received_frames)
            print("Last received:", sub.last_received_at)
            print("Last error:", sub.last_error)
            print("Local pose:", frame.local_pose)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
