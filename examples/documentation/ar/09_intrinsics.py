from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            print("Time:", frame.timestamp)
            print("Velocity:", frame.velocity)
            print("Local pose:", frame.local_pose)
            print("Global pose:", frame.global_pose)
            print("Intrinsics:", frame.camera_intrinsics)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
