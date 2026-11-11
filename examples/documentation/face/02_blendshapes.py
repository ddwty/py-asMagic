from asmagic import FaceDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.


def main():
    sub = FaceDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            if not frame.has_face:
                print('No face in this frame')
                continue
            if frame.tracking_mode != 'true_depth':
                print('Blendshapes unavailable in mode:', frame.tracking_mode)
                continue
            print('Coefficient count:', len(frame.blendshapes))
            for name, value in sorted(frame.blendshape_coefficients.items()):
                print(name, value, type(value).__name__)
            # None means the named channel is absent; 0.0 is a received value.
            print('Jaw open:', frame.blendshapes.get('jawOpen'))
            print('Left / right blink:', frame.blendshapes.get('eyeBlinkLeft'), frame.blendshapes.get('eyeBlinkRight'))
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
