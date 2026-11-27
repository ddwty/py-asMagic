"""GitBook is the source of every user-run chapter example."""
import importlib.util
from pathlib import Path
import shutil

import pytest


ROOT = Path(__file__).resolve().parents[1]


def synchronizer():
    spec = importlib.util.spec_from_file_location("gitbook_example_sync", ROOT / "tools/sync_documentation_examples.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_recorded_gitbook_block_matches_local_code_and_reference():
    assert synchronizer().main(["--check"]) == 0


@pytest.mark.parametrize("change", ["code", "block", "chapter"])
def test_gitbook_drift_fails_without_overwriting_examples(tmp_path, capsys, change):
    original = ROOT.parent / "gitbook/asMagic/doc/receiving-streamed-data"
    if not original.is_dir():
        pytest.skip("GitBook checkout is not present; CI performs the external comparison explicitly")
    folder = tmp_path / "asMagic/doc/receiving-streamed-data"
    folder.mkdir(parents=True)
    for page in original.glob("*.md"):
        shutil.copyfile(page, folder / page.name)
    page = folder / "imu-data-receiving-examples.md"
    if change == "code":
        page.write_text(page.read_text().replace('"usb"', '"usb:changed-device"', 1))
    elif change == "block":
        page.write_text(page.read_text() + '\n```python\nprint("new block")\n```\n')
    else:
        (folder / "new-receiver.md").write_text('# New receiver\n\n```python\nprint("new chapter")\n```\n')
    example = ROOT / "examples/documentation/imu/01_all_sensors_usb.py"
    before = example.read_bytes()
    assert synchronizer().main(["--check", "--gitbook", str(tmp_path)]) == 1
    assert example.read_bytes() == before
    output = capsys.readouterr()
    assert "differ" in output.out + output.err
