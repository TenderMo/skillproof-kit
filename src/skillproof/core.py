"""Check skill files as data; never execute their instructions or scripts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import os
import re
import string
from urllib.parse import unquote, urlsplit
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

import yaml

IGNORED = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".pytest_cache"}
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LINK_START = re.compile(r"!?\[[^\]\n]*\]\([ \t]*")
LINK_END = re.compile(
    r'''(?:[ \t]+(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\((?:\\.|[^)\\])*\)))?[ \t]*\)'''
)
MARKDOWN_ESCAPE = re.compile(r"\\([" + re.escape(string.punctuation) + r"])")


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate fields rather than silently accepting the last value."""


def _mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


@dataclass
class Finding:
    rule: str
    severity: str
    path: str
    line: int
    message: str


@dataclass
class Skill:
    file: Path
    root: Path
    metadata: dict = field(default_factory=dict)
    body: str = ""
    findings: list[Finding] = field(default_factory=list)

    def add(self, rule, severity, message, path=None, line=1):
        self.findings.append(Finding(rule, severity, str(path or self.file), line, message))


def valid_name(value):
    return isinstance(value, str) and 1 <= len(value) <= 64 and bool(NAME.fullmatch(value))


def discover(path: Path) -> list[Path]:
    path = path.absolute()
    if path.is_symlink():
        raise ValueError(f"Select a real directory or file instead of a symlink: {path}")
    if not path.exists():
        raise ValueError(f"Path does not exist: {path}")
    if path.is_file():
        if path.name != "SKILL.md":
            raise ValueError("Expected a SKILL.md file or a directory")
        return [path]
    found = []
    def onerror(error):
        raise error
    for base, dirs, files in os.walk(path, followlinks=False, onerror=onerror):
        dirs[:] = sorted(d for d in dirs if d not in IGNORED and not (Path(base) / d).is_symlink())
        if "SKILL.md" in files:
            found.append(Path(base) / "SKILL.md")
    if not found:
        raise ValueError(f"No SKILL.md files found under {path}")
    return sorted(found)


def inventory(root: Path):
    """Return regular files and rejected symlinks, including directory symlinks."""
    files, links = [], []
    def onerror(error):
        raise error
    for base, dirs, names in os.walk(root, followlinks=False, onerror=onerror):
        for directory in list(dirs):
            child = Path(base) / directory
            if child.is_symlink():
                links.append(child)
                dirs.remove(directory)
            elif directory in IGNORED:
                dirs.remove(directory)
        for name in names:
            child = Path(base) / name
            if child.is_symlink():
                links.append(child)
            elif not child.is_file():
                raise ValueError(f"Unsupported file type: {child}")
            else:
                files.append(child)
    return sorted(files), sorted(links)


def sensitive(path: Path) -> bool:
    lower = path.name.lower()
    return (lower == ".env" or lower.startswith(".env.")
            or lower in {"credentials.json", "id_rsa", "id_ed25519"}
            or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"})


def inline_link_destinations(content):
    """Read single-line destinations without truncating balanced parentheses."""
    for match in LINK_START.finditer(content):
        start = match.end()
        if start >= len(content):
            continue
        if content[start] == "<":
            angle = re.match(r"<((?:\\.|[^<>\\])*)>", content[start:])
            if angle is None:
                continue
            href = angle.group(1)
            end = start + angle.end()
        else:
            end, depth = start, 0
            while end < len(content):
                char = content[end]
                if char == "\\" and end + 1 < len(content) and content[end + 1] in string.punctuation:
                    end += 2
                    continue
                if char.isspace() or (char == ")" and depth == 0):
                    break
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                end += 1
            if depth or end == start:
                continue
            href = content[start:end]
        if LINK_END.match(content, end):
            yield MARKDOWN_ESCAPE.sub(r"\1", href)


def markdown_links(text):
    """Read inline links outside fenced code; reference-style links are out of scope."""
    fence = None
    for line, content in enumerate(text.splitlines(), 1):
        mark = re.match(r"^\s*(`{3,}|~{3,})(.*)$", content)
        if mark:
            token = mark.group(1)
            if fence is None:
                fence = token
            elif (token[0] == fence[0] and len(token) >= len(fence)
                  and not mark.group(2).strip(" \t")):
                fence = None
            continue
        if fence:
            continue
        for href in inline_link_destinations(content):
            yield line, href


def local_target(source: Path, href: str, root: Path):
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    decoded = unquote(parsed.path)
    if "\\" in decoded:
        raise ValueError("Use forward slashes in Markdown resource paths")
    target = (source.parent / decoded).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("Resource path leaves the skill directory")
    return target


def inspect_skill(file: Path) -> Skill:
    skill = Skill(file=file, root=file.parent)
    if file.is_symlink():
        skill.add("SP011", "error", "SKILL.md must be a regular file")
        return skill
    try:
        text = file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        skill.add("SP001", "error", f"Cannot read UTF-8 skill: {error}")
        return skill
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        skill.add("SP001", "error", "Start SKILL.md with YAML frontmatter delimited by ---")
        return skill
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        skill.add("SP001", "error", "Close the YAML frontmatter with ---")
        return skill
    try:
        metadata = yaml.load("\n".join(lines[1:end]), Loader=UniqueLoader)
        if not isinstance(metadata, dict):
            raise ValueError("Frontmatter must be a mapping")
        skill.metadata = metadata
    except (yaml.YAMLError, ValueError, RecursionError) as error:
        skill.add("SP002", "error", f"Invalid frontmatter: {error}")
        return skill
    name = metadata.get("name")
    if not valid_name(name):
        skill.add("SP003", "error", "name must be 1-64 lowercase ASCII letters/digits with single internal hyphens")
    elif name != file.parent.name:
        skill.add("SP004", "error", f"name '{name}' must match folder '{file.parent.name}'")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024:
        skill.add("SP005", "error", "description must be a non-empty string of at most 1024 characters")
    elif len(description.strip()) < 20:
        skill.add("SP101", "warning", "Describe both the capability and when the assistant should use it")
    if "compatibility" in metadata:
        value = metadata["compatibility"]
        if not isinstance(value, str) or not value.strip() or len(value) > 500:
            skill.add("SP006", "error", "compatibility must be a non-empty string of at most 500 characters")
    if "metadata" in metadata:
        value = metadata["metadata"]
        if not isinstance(value, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in value.items()):
            skill.add("SP006", "error", "metadata must map strings to strings; quote numeric versions")
    if "license" in metadata and not isinstance(metadata["license"], str):
        skill.add("SP006", "error", "license must be a string")
    # Host-specific fields are preserved, including Claude Code's list-valued allowed-tools.
    skill.body = "\n".join(lines[end + 1:]).strip()
    if not skill.body:
        skill.add("SP007", "error", "Add Markdown instructions after the frontmatter", line=end + 2)
    elif len(lines[end + 1:]) > 500:
        skill.add("SP102", "warning", "Move task-specific details into references; body exceeds 500 lines")
    for number, line in enumerate(lines[end + 1:], end + 2):
        if re.search(r"\b(TODO|FIXME|TBD)\b|\[INSERT\b", line):
            skill.add("SP103", "warning", "Review an unfinished placeholder", line=number)
    files, links = inventory(file.parent)
    for link in links:
        skill.add("SP011", "error", "Symlinked resources cannot be included in a portable release", path=link)
    for resource in files:
        if sensitive(resource):
            skill.add("SP012", "error", "Remove a potentially sensitive file before packaging", path=resource)
        if resource.suffix.lower() != ".md":
            continue
        try:
            content = resource.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            skill.add("SP008", "error", f"Cannot read Markdown resource: {error}", path=resource)
            continue
        for number, href in markdown_links(content):
            try:
                target = local_target(resource, href, file.parent)
                if target is not None and not target.exists():
                    skill.add("SP009", "error", f"Missing local resource: {href}", path=resource, line=number)
                elif target is not None and any(part in IGNORED for part in target.relative_to(file.parent.resolve()).parts):
                    skill.add("SP010", "error", f"Resource is excluded from release: {href}", path=resource, line=number)
            except ValueError as error:
                skill.add("SP010", "error", f"{href}: {error}", path=resource, line=number)
    return skill


def inspect(path: Path):
    skills = [inspect_skill(file) for file in discover(path)]
    seen = {}
    for skill in skills:
        name = skill.metadata.get("name")
        if isinstance(name, str):
            if name in seen:
                skill.add("SP013", "warning", f"Duplicate skill name also found at {seen[name]}")
            seen[name] = skill.file
    return skills


def findings(skills):
    return [finding for skill in skills for finding in skill.findings]


def failed(skills, strict=False):
    return any(f.severity == "error" or strict for f in findings(skills))


def report(skills, format="text"):
    items = findings(skills)
    errors = sum(f.severity == "error" for f in items)
    warnings = sum(f.severity == "warning" for f in items)
    if format == "json":
        return json.dumps({"schema_version": "1", "skills": len(skills), "errors": errors,
                           "warnings": warnings, "findings": [asdict(f) for f in items]}, ensure_ascii=False, indent=2) + "\n"
    summary = f"{len(skills)} skill(s), {errors} error(s), {warnings} warning(s)"
    if format == "markdown":
        rows = ["# SkillProof report", "", summary, ""]
        for f in items:
            rows.append(f"- **{f.severity.upper()} {f.rule}** `{f.path}:{f.line}` — {f.message}")
        return "\n".join(rows) + "\n"
    return "\n".join([summary] + [f"{f.path}:{f.line}: {f.severity} {f.rule} {f.message}" for f in items]) + "\n"


def cell(value):
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def catalog(skills):
    rows = ["# Skills catalog", "", "Generated from SKILL.md metadata by SkillProof Kit.", "",
            "| Skill | Use case | License |", "| --- | --- | --- |"]
    for skill in skills:
        meta = skill.metadata
        rows.append(f"| {cell(meta.get('name', skill.root.name))} | {cell(meta.get('description', ''))} | {cell(meta.get('license', 'Unspecified'))} |")
    return "\n".join(rows) + "\n"


def diagram(skills):
    rows = ["flowchart LR", '    kit["Skill collection"]']
    for index, skill in enumerate(skills):
        label = str(skill.metadata.get("name", skill.root.name))
        # Encode label punctuation as Mermaid entity codes, retaining international text.
        label = "".join(char if char.isalnum() or char in " -_./" else f"#{ord(char)};" for char in label)
        rows.extend([f'    s{index}["{label}"]', f"    kit --> s{index}"])
        files, _ = inventory(skill.root)
        for resource_index, resource in enumerate(f for f in files if f != skill.file):
            resource_label = resource.relative_to(skill.root).as_posix()
            resource_label = "".join(char if char.isalnum() or char in " -_./" else f"#{ord(char)};" for char in resource_label)
            rows.extend([f'    r{index}_{resource_index}["{resource_label}"]', f"    s{index} --> r{index}_{resource_index}"])
    return "\n".join(rows) + "\n"


def pack(skill: Skill, output: Path, strict=False):
    if failed([skill], strict):
        raise ValueError("Release blocked by findings; run skillproof check for details")
    if output.suffix.lower() != ".zip":
        raise ValueError("Release output must end in .zip")
    if output.resolve().is_relative_to(skill.root.resolve()):
        raise ValueError("Place the release archive outside the skill directory")
    files, links = inventory(skill.root)
    if links:
        raise ValueError("Release contains symlinks")
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also refuses to replace an existing archive.
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for resource in files:
            relative = Path(skill.root.name) / resource.relative_to(skill.root)
            info = ZipInfo(relative.as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            mode = 0o755 if resource.stat().st_mode & 0o111 else 0o644
            info.external_attr = (0o100000 | mode) << 16
            archive.writestr(info, resource.read_bytes())
