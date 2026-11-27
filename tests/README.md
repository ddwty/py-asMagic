# SDK regression tests

Run `python -m pytest -q` from the SDK root. Tests use synthetic data and local TCP, HTTP or usbmux services; they require permission to bind loopback ports and do not establish physical USB behavior or tracking accuracy.

User-run code lives in [the GitBook chapter examples](../examples/documentation/README.md). Device diagnostics use `asmagic-test --all --transport usb --plot --images --report reports/usb.json`.

The example tests exercise receiver cleanup, timeouts, camera handling and both Network/USB code variants. The synchronization check also compares chapter/block coverage, exact code and recorded hashes with GitBook. CI checks out GitBook and runs that comparison explicitly.
