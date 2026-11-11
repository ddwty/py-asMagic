# Watch IMU Receiving Examples

Watch motion samples received on your computer.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Receive Watch HTTP batches continuously

receive() returns one batch; batch.frames contains its motion samples.

Source: [watch/01_batches.py](../../examples/documentation/watch/01_batches.py)

Run from the SDK project directory:

```bash
python examples/documentation/watch/01_batches.py
```

```python
from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 2: Flatten batches into individual Watch samples

Read each motion sample in the received batch.

Source: [watch/02_individual_samples.py](../../examples/documentation/watch/02_individual_samples.py)

Run from the SDK project directory:

```bash
python examples/documentation/watch/02_individual_samples.py
```

```python
from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 3: Receive Watch samples

Read motion samples from the received batch.

Source: [watch/03_receive_methods.py](../../examples/documentation/watch/03_receive_methods.py)

Run from the SDK project directory:

```bash
python examples/documentation/watch/03_receive_methods.py
```

```python
from asmagic import WatchIMUReceiver



def main():
    sub = WatchIMUReceiver(host="0.0.0.0")
    try:
        while True:
            frame = sub.receive()
            for sample in frame.frames:
                print("Time:", sample.timestamp)
                print("Attitude:", sample.attitude)
                print("Rotation rate (rad/s):", sample.rotation_rate)
                print("Gravity (G):", sample.gravity)
                print("Acceleration (G):", sample.acceleration)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```

## Example 4: Select Watch payload format and decode a batch

Select the format to match your Watch sender.

Source: [watch/04_payload_format_and_decode.py](../../examples/documentation/watch/04_payload_format_and_decode.py)

Run from the SDK project directory:

```bash
python examples/documentation/watch/04_payload_format_and_decode.py
```

```python
from asmagic import WatchIMUReceiver

PAYLOAD_FORMAT = "batch"  # "batch", "single" or "legacy".


def main():
    sub = WatchIMUReceiver(host="0.0.0.0", payload_format=PAYLOAD_FORMAT)
    try:
        while True:
            frame = sub.receive()
            message = frame.protobuf
            decoded = sub.decode(message.SerializeToString())
            print("Batch time:", decoded.timestamp)
            print("Samples:", decoded.frames)
    except KeyboardInterrupt:
        pass
    finally:
        sub.close()


if __name__ == "__main__":
    main()
```
