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

Documentation examples in `examples/documentation/` must be byte-for-byte copies of the corresponding GitBook Python blocks, including Network and USB variants. `catalog.json` maps every file to its chapter and block and records its SHA-256. Do not add independent wrappers or divergent examples.

After an authorized GitBook code change, import the chapter code and verify it:

```bash
python tools/sync_documentation_examples.py --gitbook ../gitbook
python tools/sync_documentation_examples.py --check --gitbook ../gitbook
```

Import only copies GitBook code into the SDK; it never overwrites authored GitBook pages. Update catalog mappings deliberately when blocks or chapters are added or removed. CI checks against the recorded GitBook hashes and generated local references. A local check automatically compares with the sibling GitBook checkout when present; `--gitbook` selects another checkout.

Keep user-run examples in `examples/documentation/` and automated synthetic/local-transport regression tests in `tests/`. Device diagnostics use the installed `asmagic-test` command; they do not need example wrappers.

Retired or replaced scripts are preserved in the developer-only `tools/retired-examples.md` archive. Its manifest records their baseline, original path, hash and reason; `tools/check_repository.py` validates those records. The archive is not an active example directory.

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
