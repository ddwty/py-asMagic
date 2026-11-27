# asMagic Python SDK

[![Tests](https://github.com/ddwty/py-asMagic/actions/workflows/ci.yml/badge.svg)](https://github.com/ddwty/py-asMagic/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/asmagic.svg)](https://pypi.org/project/asmagic/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Receive camera, depth, motion, controller and tracking data from the [asMagic iPhone app](https://apps.apple.com/app/id6661033548).

**[Documentation](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data)** · [中文](README.zh-CN.md)

## Installation

Requires Python 3.8 or newer.

```bash
python -m pip install asmagic
```

## Documentation

See the [asMagic GitBook guide](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data) for device setup, receiving examples, data formats and API documentation.

Start with the [quick start](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/quick-start).

## USB transport

Run the [USB chapter examples](examples/documentation/README.md). Each `_usb.py` file contains the exact code shown in its GitBook USB tab.

`asmagic usb list` discovers attached devices; `asmagic usb setup` configures
system USB support on a new host. See [USB setup and examples](docs/USB.md)
for Mac, Windows, Linux, Raspberry Pi and duplex communication.
Requires SDK 1.1.0+ and a USB-enabled iPhone build. See the [GitBook USB guide](https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/quick-start#usb-connection).

```bash
asmagic-test --all --transport usb --plot --images --report reports/usb.json
```

[Device checks and reports](docs/device-testing.md).

## Contributing

For development setup and checks, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE).
