from asmagic import BodyTrackingDataSubscriber

IPHONE_IP = "192.168.1.100"
MODEL = "mediapipe"  # This example uses MediaPipe multi-person output.


def main():
    sub = BodyTrackingDataSubscriber(IPHONE_IP, model=MODEL)
    target_id = None
    target_session = None
    try:
        while True:
            frame = sub.receive()
            if target_id is None and frame.people:
                # Choose an initial track once. Keep its ID after tracking loss.
                target_id = frame.people[0].id
                target_session = frame.session_id
                print("Chosen person:", target_id)
            if target_id is None:
                continue
            if frame.session_id != target_session:
                print("Session changed. Choose a new person explicitly.")
                continue
            person = frame.person(target_id)
            if person is None:
                print("Chosen person is absent:", target_id)
                continue
            print("Person:", person.id, "Identity ambiguous:", person.identity_ambiguous)
            skeleton = person.skeleton()
            print("All joint names:", skeleton.names)
            print("Body positions (m):", skeleton.positions)
            print("Position available:", skeleton.valid)
    except (KeyboardInterrupt, StopIteration):
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
