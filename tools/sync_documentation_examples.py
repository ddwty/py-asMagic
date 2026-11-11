"""Copy standalone example sources into Markdown; --check detects any drift."""
import argparse
import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT / "examples" / "documentation"
DESTINATION = ROOT / "docs" / "examples"
PYTHON_BLOCK = re.compile(r"```(?:python|py)\n(.*?)```", re.DOTALL)


def joint_catalog():
    enums = ast.parse((ROOT / "asmagic" / "joints.py").read_text(encoding="utf-8"))
    accessors = ast.parse((ROOT / "asmagic" / "tracking_types.py").read_text(encoding="utf-8"))
    page = ["# Joint names, enums and typed attributes", "",
            "Select one person from `frame.people`, then use the paths below to read their joints. Rows match `person.skeleton()` for each model; use `layout=\"common\"` for the twelve shared rows.", "",
            "Left and right refer to the person's own body. Missing joints return `None`; unavailable array values keep their rows with NaN and a false validity flag.", "",
            "[Body examples](body.md) · [Hand examples](hand.md) · [Data format and API](api-reference.md)", ""]
    from asmagic.body_tracking import (ARKIT_JOINT_NAMES, COMMON_BODY_JOINT_NAMES,
                                       MEDIAPIPE_JOINT_NAMES)
    def location(name):
        special = {"root": "Body root", "hips": "Pelvis", "mouth_left": "Left mouth corner",
                   "mouth_right": "Right mouth corner", "left_index": "Left index-finger landmark", "right_index": "Right index-finger landmark",
                   "left_thumb": "Left thumb landmark", "right_thumb": "Right thumb landmark",
                   "left_pinky": "Left little-finger landmark",
                   "right_pinky": "Right little-finger landmark", "left_foot_index": "Left forefoot landmark",
                   "right_foot_index": "Right forefoot landmark"}
        if name in special:
            return special[name]
        words = name.replace("_", " ").replace("hand mid", "middle finger").replace("hand pinky", "little finger")
        words = words.replace("hand index", "index finger").replace("hand ring", "ring finger").replace("hand thumb", "thumb")
        return words.capitalize()
    page.extend(["## Common body: twelve fixed rows", "", "| Row | Read with | Location |", "|---:|---|---|"])
    page.extend("| {} | `person.joints.{}` | {} |".format(row, name, location(name))
                for row, name in enumerate(COMMON_BODY_JOINT_NAMES))
    page.extend(["", "## MediaPipe: 33 landmarks", "",
                 "Rows match the default 33-joint skeleton array. All positions are preserved, including low-score estimates; joint rotations are unavailable.", "",
                 "| Row | Read with | Location |", "|---:|---|---|"])
    page.extend("| {} | `person.joints.{}` | {} |".format(row, name, location(name))
                for row, name in enumerate(MEDIAPIPE_JOINT_NAMES))
    page.extend(["", "## ARKit: 91 joints", "",
                 "Rows match the default 91-joint skeleton array. Some joint transforms are estimated; check the joint's tracked flag when direct observation matters. Numbered finger, spine and neck points follow ARKit's skeleton segments; they are not additional people or detection scores.", "",
                 "| Row | Read with | Location |", "|---:|---|---|"])
    page.extend("| {} | `person.joints.{}` | {} |".format(row, name, location(name))
                for row, name in enumerate(ARKIT_JOINT_NAMES))
    page.append("")
    for enum_name, accessor_name, target, label in (
            ("HandJointName", "HandJoints", "hand.joints", "2D hand: 21 joints"),):
        definition = next(node for node in enums.body if isinstance(node, ast.ClassDef) and node.name == enum_name)
        names = [(node.targets[0].id, ast.literal_eval(node.value)) for node in definition.body
                 if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)]
        accessors_definition = next(node for node in accessors.body
                                    if isinstance(node, ast.ClassDef) and node.name == accessor_name)
        attributes = {node.value.args[0].attr: node.targets[0].id for node in accessors_definition.body
                      if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)}
        if set(attributes) != {name for name, _ in names}:
            raise ValueError("Typed joint accessors do not match " + enum_name)
        page.extend(["## " + label, "", "| Row | Enum | Wire name | Typed access |", "|---:|---|---|---|"])
        page.extend("| {} | `{}.{}` | `{}` | `{}.{}` |".format(row, enum_name, name, wire, target, attributes[name])
                    for row, (name, wire) in enumerate(names))
        page.append("")
    return "\n".join(page)


def documents():
    catalog = json.loads((SOURCE / "catalog.json").read_text(encoding="utf-8"))
    groups = catalog["groups"]
    entries = catalog["examples"]
    known_groups = {group["id"] for group in groups}
    paths = [entry["file"] for entry in entries]
    if len(paths) != len(set(paths)) or any(entry["group"] not in known_groups for entry in entries):
        raise ValueError("Duplicate example paths or unknown groups in catalog.json")
    discovered = {path.relative_to(SOURCE).as_posix() for path in SOURCE.rglob("*.py")}
    if set(paths) != discovered:
        raise ValueError("catalog.json does not match the standalone Python files")

    rows = ["| Documentation page | Files | Examples |", "|---|---|---:|"]
    for group in groups:
        selected = [entry for entry in entries if entry["group"] == group["id"]]
        rows.append("| [{title}]({id}.md) | [{id}/](../../examples/documentation/{id}/) | {count} |".format(
            count=len(selected), **group))
        page = ["# " + group["title"], "", group["intro"], "",
                "[All examples](index.md) · [Data format and API](api-reference.md)", ""]
        if group["id"] != "camera":
            page.extend(["Replace `IPHONE_IP` with your iPhone's IP and start the matching App output. "
                         "For Watch, enter your computer's IP on Watch. Ctrl-C stops receiving.", ""])
        for number, entry in enumerate(selected, 1):
            script = "examples/documentation/" + entry["file"]
            code = (SOURCE / entry["file"]).read_text(encoding="utf-8").rstrip()
            if "```" in code:
                raise ValueError("An example contains a Markdown fence")
            heading = "## " + entry["title"] if group["id"] == "camera" else "## Example {}: {}".format(number, entry["title"])
            page.extend([heading, "", entry["note"], "",
                         "Source: [{}](../../{})".format(entry["file"], script), "",
                         "Run from the SDK project directory:", "", "```bash", "python " + script, "```", "",
                         "```python", code, "```", ""])
        yield DESTINATION / (group["id"] + ".md"), "\n".join(page)

    index = """# Runnable documentation examples

Each documentation example has its own independent `.py` file in `examples/documentation/`.
The Python code blocks on these pages are copied verbatim from those files. They import the installed SDK
directly, without `_common.py`, CLI arguments, a test runner or fixtures.
Basic loops use `receive()`, which waits for a valid frame. Use `receive(timeout=...)` for timeouts.

## Install the local SDK

From the project directory containing `pyproject.toml`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows, activate with `.venv\\Scripts\\activate`. Python 3.8+ is supported.
The default installation includes Matplotlib for skeleton plots and PyAV for HEVC images, along with every other runtime dependency.
Users do not need to choose extras. Displaying a skeleton remains an API choice, off by default.
These examples target SDK 1.0.2 or newer. Install it with `python -m pip install --upgrade "asmagic>=1.0.2"`.

## Run each example yourself

1. Open the feature being tested in the App and start its data output.
2. For ZeroMQ examples, replace `IPHONE_IP = "192.168.1.100"` with the iPhone address on the same LAN.
3. For Watch, start the Python receiver and set the Watch destination to this computer's LAN IP and listening port.
4. Run the corresponding file from the project directory; Ctrl-C stops receiving.

```bash
python examples/documentation/ar/01_continuous.py
python examples/documentation/body/04_optional_skeleton.py
python examples/documentation/hand/03_optional_skeleton.py
```

Camera features can need separate sessions; test one feature at a time. These scripts never mark a real App
test as passed. Check the printed values and compare plots with your actual actions.

## Choose whether to display a skeleton

Body, upper-body, hand and face/hand pages include a complete optional plotting example.
Set `SHOW_SKELETON = True` to display the figure or `False` to receive only.
The standard examples receive with receive(); no window is created when SHOW_SKELETON=False.
Use `PLOT_OPTIONS` to set labels, drawing frequency and stale-data timeout;
3D body plots support body or world coordinates. Plots run on the main thread.
`CameraFrame.color_bytes` returns encoded JPEG/HEVC data. Use `data.show_image()` to display an upright camera image.

## Pages and files

""" + "\n".join(rows) + """

See [Data Format and API](api-reference.md) for method signatures, return values, units and missing-data behavior.
The [joint catalog](joint-catalog.md) lists the available body/hand joints, Python paths and array rows.
Legacy pages are compatibility examples for old publishers with known ports, not current App features.

## Keep documentation and executable code identical

The source of each Python block is its standalone file; its title and notes are in
`examples/documentation/catalog.json`. After editing a file or note:

```bash
python tools/sync_documentation_examples.py
python tools/sync_documentation_examples.py --check
```

The first command updates Markdown pages. The second verifies that synchronized code and tables match their
source files. All inputs and generated pages are contained in this repository.
The separate `examples/test_app_streams.py` guided diagnostic tool remains available; it is not required for these examples.
"""
    yield DESTINATION / "index.md", index
    yield DESTINATION / "joint-catalog.md", joint_catalog()
    summary = ["# Table of contents", "", "* [Runnable documentation examples](index.md)",
               "* [Data Format and API](api-reference.md)", "* [Joint catalog](joint-catalog.md)"]
    summary.extend("* [{title}]({id}.md)".format(**group) for group in groups)
    yield DESTINATION / "SUMMARY.md", "\n".join(summary) + "\n"

    readme = ["# Runnable examples", "",
              "Each script imports the installed SDK directly and can be run independently.",
              "Edit the IP address and display settings at the top, then run it from the repository root.",
              "For Watch, configure the device to send to your computer's address.", "",
              "[Setup and guides](../../docs/examples/index.md) · [Data format and API](../../docs/examples/api-reference.md)", "",
              "| File | Example |", "|---|---|"]
    readme.extend("| [{file}]({file}) | {title} |".format(**entry) for entry in entries)
    readme.extend(["", "Set `SHOW_SKELETON = True/False` to toggle tracking plots. `frame.show_images()` displays color and depth by default; pass `show_depth=False` or `show_color=False` to disable either view.",
                   "Run `python tools/sync_documentation_examples.py --check` to check that documentation and source code match.", ""])
    yield SOURCE / "README.md", "\n".join(readme)
    camera_preview = SOURCE / "camera" / "01_preview.py"
    if camera_preview.is_file():
        yield ROOT / "examples" / "camera_only.py", camera_preview.read_text(encoding="utf-8")

    mapping = json.loads((ROOT / "tools" / "sdk_examples.json").read_text(encoding="utf-8"))
    for relative, files in mapping.items():
        path = ROOT / relative
        content = path.read_text(encoding="utf-8")
        if len(PYTHON_BLOCK.findall(content)) != len(files):
            raise ValueError("SDK guide block count differs from manifest: " + relative)
        sources = iter(files)

        def block(match):
            name = next(sources)
            code = (SOURCE / name).read_text(encoding="utf-8").rstrip()
            ast.parse(code, filename=name)
            return "```python\n" + code + "\n```"

        yield path, PYTHON_BLOCK.sub(block, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without editing Markdown")
    args = parser.parse_args()
    stale = []
    count = 0
    outputs = list(documents())
    for path, content in outputs:
        count += 1
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    if stale:
        print("Out-of-date documentation:", *stale, sep="\n")
        return 1
    print("{} {} documentation files".format("Verified" if args.check else "Updated", count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
