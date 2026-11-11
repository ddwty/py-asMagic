from asmagic import IMUDataSubscriber

sub = IMUDataSubscriber("192.168.1.100")  # Replace with your iPhone's IP.

try:
    while True:
        frame = sub.receive()
        print(frame.timestamp, frame.gyroscope)
except KeyboardInterrupt:
    pass
finally:
    sub.close()
