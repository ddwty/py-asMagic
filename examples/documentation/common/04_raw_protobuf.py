from asmagic import ClawDataSubscriber, ProtobufSubscriber
from asmagic.proto import claw_msg_pb2

IPHONE_IP = "192.168.1.100"
USE_TYPED_SUBSCRIBER = True


def main():
    if USE_TYPED_SUBSCRIBER:
        sub = ClawDataSubscriber(IPHONE_IP, port=5301)
    else:
        sub = ProtobufSubscriber(IPHONE_IP, 5301, claw_msg_pb2.Claw)
    try:
        while True:
            frame = sub.receive()
            message = frame.protobuf if USE_TYPED_SUBSCRIBER else frame
            print('Schema:', message.DESCRIPTOR.full_name)
            print('Message:', message)
            if message.HasField('motor'):
                print('Motor percent:', message.motor.angle_percent)
            if not USE_TYPED_SUBSCRIBER:
                decoded = sub.decode(message.SerializeToString())
                print('Decoded without receiving another frame:', decoded)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
