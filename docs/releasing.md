# Releases

The distribution name on PyPI is `asmagic`; the source repository is [ddwty/py-asMagic](https://github.com/ddwty/py-asMagic). GitHub publication and PyPI uploads are separate operations.

## Prepare a version

1. Update `version` in `pyproject.toml` and `__version__` in `asmagic/__init__.py` together.
2. Add the user-facing changes to `CHANGELOG.md` and update affected examples and documentation.
3. Run the checks in [CONTRIBUTING.md](../CONTRIBUTING.md), including schema regeneration checks when a protocol changes.
4. For transport or device-facing changes, run the relevant `asmagic-test` checks with the supported app version. Record the device, app version and feature tested.

## Build and inspect

Start with an empty `dist/` directory so older artifacts cannot be uploaded by mistake.

```bash
python -m build
python -m twine check dist/*
```

The wheel contains the SDK, generated bindings, schema snapshots, provenance metadata and type marker. The source distribution also includes documentation, examples, tests and maintenance tools. Check the archive contents and install the wheel in a fresh environment outside the checkout:

```bash
python -m venv /tmp/asmagic-wheel-check
/tmp/asmagic-wheel-check/bin/python -m pip install dist/asmagic-<version>-py3-none-any.whl
cd /tmp
/tmp/asmagic-wheel-check/bin/python -c "import asmagic; print(asmagic.__version__)"
/tmp/asmagic-wheel-check/bin/asmagic-test --list
```

Replace `<version>` with the prepared version. On Windows, use a temporary directory and the virtual environment's `Scripts` directory.

## Publish

Use credentials from the maintainer's local authentication configuration or a secure CI secret store. Never put tokens in source files, URLs or commits. PyPI versions are immutable: a corrected distribution needs a new version number.

After validation, upload the two explicit artifacts for the prepared version with `python -m twine upload`, then create the corresponding Git tag and release notes. Verify installation from PyPI in a clean environment. This repository's CI builds and validates packages; it does not upload them.
