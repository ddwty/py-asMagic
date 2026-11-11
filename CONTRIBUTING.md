# Contributing

Bug reports and focused pull requests are welcome. Use [GitHub Issues](https://github.com/ddwty/py-asMagic/issues) for reproducible SDK problems and feature requests.

## Development setup

```bash
git clone https://github.com/ddwty/py-asMagic.git
cd py-asMagic
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Windows, activate with `.venv\Scripts\activate` in Command Prompt or `.\.venv\Scripts\Activate.ps1` in PowerShell.

## Checks

Run from the repository root:

```bash
python -m pytest -q
python tools/sync_documentation_examples.py --check
python tools/check_repository.py
python -m build
python -m twine check dist/*
```

The tests use local TCP and HTTP servers, synthetic messages, and checked-in fixtures. They need loopback networking but no iPhone, Watch or companion app. Plotting tests select a headless backend. For device checks, use `asmagic-test --list` and report which app feature and output were enabled.

## Changes

- Preserve public imports, field meanings and Protobuf field numbers. Document intentional API changes in `CHANGELOG.md` and the upgrade guide.
- Add a focused regression test for behavior changes. Use synthetic values rather than device recordings.
- Keep examples runnable with editable settings at the top, bounded waits where a window needs updates, and deterministic receiver cleanup.
- Include Python, OS, SDK and app versions in bug reports, along with a minimal script and the relevant traceback. Remove private addresses and personal data from attachments.

Documentation examples live in `examples/documentation/`; their titles and notes are in `catalog.json`. After editing them, run `python tools/sync_documentation_examples.py` to update the corresponding Markdown pages. Detailed body, hand and face guides are also maintained in this repository.

## Protocol changes

The `.proto` files in `asmagic/proto/schemas/` are the checked-in protocol snapshots. Update their SHA-256 entries in `asmagic/proto/schema_sources.json` when changing them. Never reuse a field number for a different meaning.

To regenerate bindings, install a Protobuf compiler (`protoc`) or `grpcio-tools`, then run:

```bash
python tools/generate_protos.py
python tools/generate_protos.py --check
python -m pytest -q
```

Commit schema changes together with generated bindings and relevant fixture updates. Do not edit `*_pb2.py` manually. The generator uses a private descriptor pool so legacy bindings can coexist with this package.

See [release instructions](docs/releasing.md) for packaging and version updates.
