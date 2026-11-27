# Quick Start

Code copied verbatim from [the GitBook chapter](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/quick-start). See that chapter for setup, data formats and limitations.

## Receive your first frame (Network)

Source: [quick_start/01_first_frame.py](../../examples/documentation/quick_start/01_first_frame.py)

```bash
python examples/documentation/quick_start/01_first_frame.py
```

```python
from asmagic import ARDataSubscriber

sub = ARDataSubscriber("192.168.1.100")
try:
    while True:
        data = sub.receive()
        print(data.timestamp)
except KeyboardInterrupt:
    pass
finally:
    sub.close()
```
