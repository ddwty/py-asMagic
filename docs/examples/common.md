# Common Receiving API Examples

Receiving, processing and saving frames.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Receive one frame and read its fields

receive() waits for a valid frame. Read all related fields from that frame; Ctrl-C stops and closes the receiver.

Source: [common/07_receive_loop.py](../../examples/documentation/common/07_receive_loop.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/07_receive_loop.py
```

```python
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
```

## Example 2: Receiving with a timeout and status

Use receive(timeout=1000); None means no valid frame arrived within 1000 milliseconds. Print status after receiving a frame.

Source: [common/01_options_timeout_and_cleanup.py](../../examples/documentation/common/01_options_timeout_and_cleanup.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/01_options_timeout_and_cleanup.py
```

```python
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
```

## Example 3: Process a received frame

Call your processing function with the received frame.

Source: [common/02_stream_callback.py](../../examples/documentation/common/02_stream_callback.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/02_stream_callback.py
```

```python
from asmagic import IMUDataSubscriber

IPHONE_IP = "192.168.1.100"


def on_frame(frame):
    print(frame.timestamp, frame.gyroscope)


def main():
    sub = IMUDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            on_frame(frame)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 4: Discover streams and subscribe by name

Choose a receiver with subscribe(stream_name, ip).

Source: [common/03_named_stream_factory.py](../../examples/documentation/common/03_named_stream_factory.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/03_named_stream_factory.py
```

```python
from asmagic import STREAMS, subscribe

IPHONE_IP = "192.168.1.100"
STREAM_NAME = "hand"


def main():
    for name, info in STREAMS.items():
        print(name, info.subscriber.__name__, info.port, info.message, info.feature)
    sub = subscribe(STREAM_NAME, IPHONE_IP, verbose=True)
    try:
        while True:
            frame = sub.receive()
            print(type(frame).__name__, frame.timestamp)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 5: Read raw Protobuf from a received frame

Use frame.protobuf or receive a raw message with ProtobufSubscriber.

Source: [common/04_raw_protobuf.py](../../examples/documentation/common/04_raw_protobuf.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/04_raw_protobuf.py
```

```python
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
```

## Example 6: Save one received frame for offline decoding

Wait for one frame, then save its reserialized Protobuf for offline decoding.

Source: [common/05_save_protobuf_frame.py](../../examples/documentation/common/05_save_protobuf_frame.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/05_save_protobuf_frame.py
```

```python
from pathlib import Path
from asmagic import ARDataSubscriber

IPHONE_IP = "192.168.1.100"  # Replace with your iPhone's IP address.
OUTPUT = Path("reports/manual-ar-frame.bin")


def main():
    sub = ARDataSubscriber(IPHONE_IP)
    try:
        while True:
            frame = sub.receive()
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(frame.protobuf.SerializeToString())
            print("Saved:", OUTPUT)
            break
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 7: Decode a saved typed frame without a socket

Run the preceding save example first, then decode the saved data.

Source: [common/06_decode_saved_frame.py](../../examples/documentation/common/06_decode_saved_frame.py)

Run from the SDK project directory:

```bash
python examples/documentation/common/06_decode_saved_frame.py
```

```python
from pathlib import Path
from asmagic import ARDataSubscriber

INPUT = Path("reports/manual-ar-frame.bin")


def main():
    if not INPUT.is_file():
        print("First run common/05_save_protobuf_frame.py to create", INPUT)
        return
    frame = ARDataSubscriber.decode(INPUT.read_bytes())
    print("Timestamp:", frame.timestamp)
    print("Local pose:", frame.local_pose)
    print("RGB:", frame.color_array)
    print("Depth:", frame.depth)
    print("Depth size:", frame.depth_width, frame.depth_height)


if __name__ == "__main__":
    main()
```
