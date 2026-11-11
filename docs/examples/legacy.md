# Legacy Receiving Examples

Receivers for explicitly configured older publishers.

[All examples](index.md) · [Data format and API](api-reference.md)

Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.

## Example 1: Legacy combined MagiClaw publisher

Requires an older combined publisher with a known port.

Source: [legacy/01_magiclaw_combined.py](../../examples/documentation/legacy/01_magiclaw_combined.py)

Run from the SDK project directory:

```bash
python examples/documentation/legacy/01_magiclaw_combined.py
```

```python
from asmagic import MagiClawDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = None
    try:
        port = int(input("Enter your legacy MagiClaw publisher's TCP port: "))
        sub = MagiClawDataSubscriber(IPHONE_IP, port=port)
        while True:
            message = sub.receive()
            print('Timestamp:', message.timestamp)
            for name in ('claw', 'finger_0', 'finger_1', 'phone'):
                if message.HasField(name):
                    print(name, getattr(message, name))
    except KeyboardInterrupt:
        pass
    finally:
        if sub is not None:
            sub.close()


if __name__ == "__main__":
    main()
```

## Example 2: Legacy Watch ZeroMQ publisher

Requires an older Watch ZeroMQ publisher with a known port.

Source: [legacy/02_watch_zmq.py](../../examples/documentation/legacy/02_watch_zmq.py)

Run from the SDK project directory:

```bash
python examples/documentation/legacy/02_watch_zmq.py
```

```python
from asmagic import LegacyWatchDataSubscriber

IPHONE_IP = "192.168.1.100"


def main():
    sub = None
    try:
        port = int(input("Enter your legacy Watch publisher's TCP port: "))
        sub = LegacyWatchDataSubscriber(IPHONE_IP, port=port)
        while True:
            frame = sub.receive()
            print(frame.timestamp, frame.attitude, frame.rotation_rate, frame.gravity, frame.acceleration)
            offline = LegacyWatchDataSubscriber.decode(frame.protobuf.SerializeToString())
            print('Offline decoded attitude:', offline.attitude)
    except KeyboardInterrupt:
        pass
    finally:
        if sub is not None:
            sub.close()


if __name__ == "__main__":
    main()
```
