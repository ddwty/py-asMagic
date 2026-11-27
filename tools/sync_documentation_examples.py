"""Import GitBook chapter code verbatim; --check rejects example drift."""
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
PYTHON_BLOCK = re.compile(r"^```(?:python|py)[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)


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


def catalog():
    data = json.loads((SOURCE / 'catalog.json').read_text(encoding='utf-8'))
    paths = [entry['file'] for entry in data['examples']]
    discovered = {p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*.py')}
    if len(paths) != len(set(paths)) or set(paths) != discovered:
        raise ValueError('catalog.json must list every example exactly once')
    groups = [group['id'] for group in data['groups']]
    pages = [group['page'] for group in data['groups']]
    if (len(set(groups)) != len(groups) or len(set(pages)) != len(pages)
            or any(entry['group'] not in groups for entry in data['examples'])):
        raise ValueError('Duplicate chapter mappings or unknown example groups')
    all_scripts = {p.relative_to(ROOT / 'examples').as_posix() for p in (ROOT / 'examples').rglob('*.py')}
    if all_scripts != {'documentation/' + path for path in paths}:
        raise ValueError('Keep all user-run examples in the mapped documentation directory')
    return data


def documents():
    """Generate local reference pages from the exact GitBook code copies."""
    data = catalog()
    rows = []
    readme = ['# GitBook examples', '',
              'These files contain the exact Python code shown in the corresponding GitBook chapters, including each Network and USB tab. Files ending in `_usb.py` use USB.', '',
              'Install this checkout with `python -m pip install -e .`. Run scripts from the SDK directory; edit the connection and model settings at the top when needed. Start the matching output in asMagic first.', '',
              'For USB, connect a data cable, unlock and trust the computer, and keep asMagic in the foreground. Use `asmagic usb list` to find a device; replace `"usb"` with `"usb:DEVICE_UDID"` when several are attached.', '',
              '```bash',
              'python examples/documentation/imu/01_all_sensors_usb.py',
              'python examples/documentation/camera/01_preview_usb.py',
              'python examples/documentation/hand/03_optional_skeleton_usb.py',
              '```', '',
              'Body examples select ARKit or MediaPipe with `MODEL`; match the app setting.', '',
              '## Chapters and files', '',
              '| GitBook chapter | Local file | Connection | Type |', '|---|---|---|---|']
    base = 'https://doc.ancoraspring.com/asmagic/python-sdk/receiving-streamed-data/'
    for group in data['groups']:
        url = base + group['page'][:-3]
        entries = [e for e in data['examples'] if e['group'] == group['id']]
        page = ['# ' + group['title'], '',
                'Code copied verbatim from [the GitBook chapter](' + url + '). See that chapter for setup, data formats and limitations.', '']
        for entry in entries:
            code = (SOURCE / entry['file']).read_text(encoding='utf-8')
            ast.parse(code, filename=entry['file'])
            label = entry['transport'].upper() if entry['transport'] == 'usb' else entry['transport'].capitalize()
            page += ['## ' + entry['title'] + ' (' + label + ')', '',
                     'Source: [' + entry['file'] + '](../../examples/documentation/' + entry['file'] + ')', '']
            if entry['kind'] == 'script':
                page += ['```bash', 'python examples/documentation/' + entry['file'], '```', '']
            else:
                page += ['Fragment: use `data` from the camera receiving loop.', '']
            page += ['```python\n' + code + '```', '']
            readme.append('| [{}]({}) | [{}]({}) | {} | {} |'.format(
                group['title'], url, entry['file'], entry['file'], label, entry['kind']))
        rows.append('| [{}]({}.md) | {} |'.format(group['title'], group['id'], len(entries)))
        yield DESTINATION / (group['id'] + '.md'), '\n'.join(page)
    readme += ['', '## Device checks', '',
               'The installed diagnostic command checks all supported typed streams, including USB Watch relay and both grippers. It prompts for each app feature and saves a JSON report. Skip channels without the required hardware.', '',
               '```bash', 'asmagic-test --all --transport usb --plot --images --report reports/usb.json',
               'asmagic-test --list --transport usb', '```', '',
               'Watch relay requires Watch → iPhone HTTP on port 18002, then iPhone → computer USB. The legacy combined face/hand decoder is available in the SDK; current apps send face and hands independently.', '',
               'SDK regression tests live in `tests/`; they use synthetic inputs and local transports. They do not establish physical USB behavior or tracking accuracy.', '',
               '## Keep the code identical', '',
               'GitBook is the authority for these examples. After changing chapter code, import it and run the drift check:', '',
               '```bash', 'python tools/sync_documentation_examples.py --gitbook ../gitbook',
               'python tools/sync_documentation_examples.py --check --gitbook ../gitbook', '```', '',
               'The catalog records the chapter, Python block number, transport and SHA-256 of each file. Add or remove mappings deliberately when chapter blocks change. Do not create independent example implementations.', '']
    yield SOURCE / 'README.md', '\n'.join(readme)
    yield ROOT / 'examples' / 'README.md', '# Examples\n\n[Chapter-by-chapter files, USB scripts and device checks](documentation/README.md).\n'
    index = ['# GitBook examples', '',
             '[Local files and USB testing](../../examples/documentation/README.md). Every Python block in the mapped GitBook chapters has an identical local file.', '',
             '| Chapter | Python blocks |', '|---|---:|'] + rows + ['',
             '[Data format and API](api-reference.md) · [Joint catalog](joint-catalog.md)', '']
    yield DESTINATION / 'index.md', '\n'.join(index)
    yield DESTINATION / 'joint-catalog.md', joint_catalog()
    summary = ['# Table of contents', '', '* [GitBook examples](index.md)',
               '* [Data Format and API](api-reference.md)', '* [Joint catalog](joint-catalog.md)']
    summary += ['* [{}]({}.md)'.format(g['title'], g['id']) for g in data['groups']]
    yield DESTINATION / 'SUMMARY.md', '\n'.join(summary) + '\n'


def gitbook_sources(root, data):
    """Refuse incomplete mappings instead of silently losing chapter examples."""
    folder = root / 'asMagic/doc/receiving-streamed-data'
    pages = {p.name for p in folder.glob('*.md') if PYTHON_BLOCK.search(p.read_text(encoding='utf-8'))}
    mapped = {group['page'] for group in data['groups']}
    if pages != mapped:
        raise ValueError('GitBook Python chapter inventory differs: ' + str(sorted(pages ^ mapped)))
    result = {}
    for group in data['groups']:
        content = (folder / group['page']).read_text(encoding='utf-8')
        blocks = PYTHON_BLOCK.findall(content)
        entries = [e for e in data['examples'] if e['group'] == group['id']]
        if sorted(e['block'] for e in entries) != list(range(1, len(blocks) + 1)):
            raise ValueError('GitBook block inventory differs: ' + group['page'])
        for entry in entries:
            code = blocks[entry['block'] - 1]
            ast.parse(code, filename=entry['file'])
            result[entry['file']] = code
    return result


def main(argv=None):
    import hashlib
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check without modifying files')
    parser.add_argument('--gitbook', type=Path, help='GitBook checkout to import or compare')
    args = parser.parse_args(argv)
    try:
        data = catalog()
        gitbook = args.gitbook
        if gitbook is None and (ROOT.parent / 'gitbook/asMagic/doc').is_dir():
            gitbook = ROOT.parent / 'gitbook'
        originals = gitbook_sources(gitbook, data) if gitbook is not None else {}
        stale = []
        for entry in data['examples']:
            path = SOURCE / entry['file']
            code = path.read_text(encoding='utf-8')
            expected = originals.get(entry['file'], code)
            digest = hashlib.sha256(expected.encode()).hexdigest()
            if args.check:
                if code != expected or entry['sha256'] != digest:
                    stale.append(str(path))
            elif originals:
                path.write_text(expected, encoding='utf-8')
                entry['sha256'] = digest
            elif entry['sha256'] != digest:
                raise ValueError('Source hash changed; import from GitBook: ' + entry['file'])
        if not args.check and originals:
            (SOURCE / 'catalog.json').write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        outputs = list(documents())
        for path, content in outputs:
            if args.check:
                if not path.is_file() or path.read_text(encoding='utf-8') != content:
                    stale.append(str(path))
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding='utf-8')
        if stale:
            print('Examples differ from GitBook or generated references:', *stale, sep='\n')
            return 1
        print('{} {} examples ({} USB), {} local reference files{}'.format(
            'Verified' if args.check else 'Synchronized', len(data['examples']),
            sum(e['transport'] == 'usb' for e in data['examples']), len(outputs),
            '; compared with GitBook' if originals else '; recorded GitBook hashes checked'))
        return 0
    except (ValueError, OSError, SyntaxError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
