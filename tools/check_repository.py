"""Check publication boundaries, local Markdown links and package versions."""
import ast
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = {".github", "asmagic", "docs", "examples", "tests", "tools"}
ROOT_FILES = {
    ".gitattributes", ".gitignore", "CHANGELOG.md", "CONTRIBUTING.md", "LICENSE",
    "MANIFEST.in", "README.md", "README.zh-CN.md", "pyproject.toml",
}
IGNORED = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache",
           ".mypy_cache", ".tox", ".nox", "build", "dist", "reports", "htmlcov"}
SENSITIVE = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b"
    r"|\bpypi-[A-Za-z0-9_-]{40,}\b|\bAKIA[0-9A-Z]{16}\b"
)
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^\)\n]+)\)")


def publication_files():
    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=str(ROOT), check=True, stdout=subprocess.PIPE,
        )
        return [ROOT / name for name in result.stdout.decode("utf-8").split("\0") if name]
    return [p for p in ROOT.rglob("*") if p.is_file()
            and not any(part in IGNORED or part.endswith(".egg-info")
                        for part in p.relative_to(ROOT).parts)]


def main():
    errors = []
    files = publication_files()
    for path in files:
        relative = path.relative_to(ROOT)
        if relative.parts[0] not in DIRECTORIES and relative.as_posix() not in ROOT_FILES:
            errors.append("Unexpected publication path: " + relative.as_posix())
        if path.is_symlink() or not path.is_file():
            errors.append("Not a regular file: " + relative.as_posix())
            continue
        if (any(p in IGNORED or p.endswith(".egg-info") for p in relative.parts)
                or path.name.startswith(".env") or path.name in {".DS_Store", ".pypirc"}
                or path.suffix.lower() in {".pyc", ".pyo", ".pem", ".key", ".log", ".mp4", ".mov"}):
            errors.append("Local or generated file: " + relative.as_posix())
        if path.stat().st_size > 2 * 1024 * 1024:
            errors.append("Review large file: " + relative.as_posix())
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if SENSITIVE.search(content):
            errors.append("Credential-shaped content: " + relative.as_posix())
        if path != Path(__file__).resolve() and re.search(r"/(?:Users|home)/", content):
            errors.append("Developer-specific absolute path: " + relative.as_posix())
        if path.suffix == ".md":
            prose = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
            for destination in LINK.findall(prose):
                destination = destination.split(' "', 1)[0].strip("<>")
                parsed = urlsplit(destination)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                target = (path.parent / unquote(parsed.path)).resolve()
                try:
                    target.relative_to(ROOT)
                except ValueError:
                    errors.append("Link leaves repository in " + relative.as_posix())
                    continue
                if not target.exists():
                    errors.append("Broken link in {}: {}".format(relative.as_posix(), destination))
    metadata = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version = "([^"]+)"$', metadata, re.MULTILINE).group(1)
    package_ast = ast.parse((ROOT / "asmagic/__init__.py").read_text(encoding="utf-8"))
    package_version = next(ast.literal_eval(n.value) for n in package_ast.body
                           if isinstance(n, ast.Assign)
                           and any(isinstance(t, ast.Name) and t.id == "__version__" for t in n.targets))
    if version != package_version:
        errors.append("Package and metadata versions differ")
    if "https://github.com/ddwty/py-asMagic" not in metadata:
        errors.append("Package repository URL is missing")
    if errors:
        print("\n".join(sorted(set(errors))))
        return 1
    print("Checked {} publication files, local Markdown links and version {}".format(len(files), version))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
