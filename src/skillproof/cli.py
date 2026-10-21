"""Command-line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from . import __version__
from .core import catalog, diagram, failed, inspect, pack, report, valid_name


TEMPLATES = {
    "basic": ("Carry out the named workflow when the user requests this specific task.",
              "# Workflow\n\nIdentify the requested deliverable, apply the relevant project conventions, and verify the result.\n"),
    "docs": ("Write or update README files, tutorials, and API documentation when a project needs onboarding or usage guidance.",
             "# Write project documentation\n\nRead the implementation and existing examples before describing behavior. Lead with the user outcome. Include prerequisites, a runnable example, expected output, and troubleshooting for demonstrated failure cases. Keep links relative inside the skill bundle. Verify commands when the environment supports them, and identify examples that were not run.\n"),
    "diagram": ("Draw architecture, workflow, and dependency diagrams in Mermaid when users need to explain components, handoffs, or resource relationships.",
                "# Draw a technical diagram\n\nDerive components and edges from source files or user-provided facts. Choose a flowchart for processes, a sequence diagram for interactions, or a component graph for architecture. Label edges with their meaning. Save editable Mermaid source and include a short caption. Distinguish proposed components from implemented ones. Use SVG export only when a renderer is available.\n"),
}


def write_result(content, output):
    if output:
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    else:
        sys.stdout.write(content)


def parser():
    root = argparse.ArgumentParser(prog="skillproof", description="Check, document, visualize, and package Agent Skills.")
    root.add_argument("--version", action="version", version=__version__)
    sub = root.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="Check one skill or a collection")
    check.add_argument("path", nargs="?", type=Path, default=Path("."))
    check.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    check.add_argument("--output", type=Path)
    check.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    for name, help_text in [("docs", "Generate a Markdown skills catalog"), ("diagram", "Generate an editable Mermaid resource graph")]:
        command = sub.add_parser(name, help=help_text)
        command.add_argument("path", type=Path)
        command.add_argument("--output", type=Path)
    create = sub.add_parser("init", help="Create a skill without overwriting existing files")
    create.add_argument("name")
    create.add_argument("--dir", type=Path, default=Path("skills"))
    create.add_argument("--template", choices=sorted(TEMPLATES), default="basic")
    bundle = sub.add_parser("pack", help="Validate and create a local release ZIP")
    bundle.add_argument("path", type=Path)
    bundle.add_argument("--output", type=Path, required=True)
    bundle.add_argument("--strict", action="store_true")
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            if not valid_name(args.name):
                raise ValueError("Use 1-64 lowercase letters/digits with single internal hyphens")
            target = args.dir / args.name
            target.mkdir(parents=True, exist_ok=False)
            description, body = TEMPLATES[args.template]
            (target / "SKILL.md").write_text(f"---\nname: {args.name}\ndescription: {description}\n---\n\n{body}", encoding="utf-8")
            print(f"Created {target / 'SKILL.md'}")
            return 0
        skills = inspect(args.path)
        if args.command == "check":
            write_result(report(skills, args.format), args.output)
            return 1 if failed(skills, args.strict) else 0
        if args.command == "pack":
            root = args.path.parent if args.path.is_file() else args.path
            if len(skills) != 1 or skills[0].root.resolve() != root.resolve():
                raise ValueError("pack accepts one skill directory or its SKILL.md, not a collection")
            if failed(skills, args.strict):
                sys.stderr.write(report(skills))
                return 1
            pack(skills[0], args.output, args.strict)
            print(f"Created {args.output}")
            return 0
        if failed(skills):
            sys.stderr.write(report(skills))
            return 1
        content = catalog(skills) if args.command == "docs" else diagram(skills)
        write_result(content, args.output)
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(f"skillproof: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
