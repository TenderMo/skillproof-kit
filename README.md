# SkillProof Kit

**Check, document, visualize, and package Agent Skills for AI coding assistants.**

[简体中文](README.zh-CN.md) · [CLI guide](docs/usage.md) · [Rules](docs/rules.md) · [Architecture](docs/architecture.md)

SkillProof Kit catches broken skill metadata, missing local resources, and unfinished scaffolds before you share a skill. It generates a Markdown catalog, an editable Mermaid resource graph, and a validated ZIP for distribution.

Designed for authors working with Codex, Claude Code, and other assistants that read `SKILL.md`. The checker validates the shared file structure and selected metadata rules. Host-specific fields are preserved.

## Quick start

Requires Python 3.11 or newer. Run these commands from the project checkout:

```sh
python -m pip install .
skillproof check examples/skills --strict
skillproof docs examples/skills --output reports/catalog.md
skillproof diagram examples/skills --output reports/skills.mmd
skillproof pack examples/skills/write-project-docs --output dist/write-project-docs.zip
```

The example collection should produce:

```text
2 skill(s), 0 error(s), 0 warning(s)
```

Create a new skill:

```sh
skillproof init write-api-docs --template docs --dir skills
skillproof check skills --format json --output reports/check.json
```

Installation from a source checkout is supported in this release. A PyPI release has not been published.

## What it does

| Command | Result | Typical use |
| --- | --- | --- |
| `check` | Text, JSON, or Markdown findings | Local review and CI gates |
| `init` | A new `SKILL.md` from a basic, docs, or diagram template | Start an authoring workflow |
| `docs` | Markdown skills catalog | Document a team's available skills |
| `diagram` | Mermaid graph of skills and their bundled files | Explain and inspect bundle structure |
| `pack` | Validated local ZIP | Prepare a downloadable skill release |

```mermaid
flowchart LR
    source[SKILL.md and resources] --> checker[Static checks]
    checker --> findings[Text / JSON / Markdown report]
    checker --> catalog[Skills catalog]
    checker --> graph[Mermaid resource graph]
    checker --> archive[Validated release ZIP]
```

## Writing documentation and drawing diagrams

The [documentation skill](examples/skills/write-project-docs/SKILL.md) helps a coding assistant write README files, tutorials, and CLI guides grounded in the implementation. The [diagram skill](examples/skills/draw-system-diagrams/SKILL.md) helps it explain architecture, workflows, and interactions using editable Mermaid.

SkillProof manages their structure and release packaging. Its `docs` command generates a metadata catalog; its `diagram` command generates a resource inventory graph. Generating narrative project documentation or inferring architecture from arbitrary source code is work performed by the assistant using the example skills.

## CI

The repository includes a [test workflow](.github/workflows/ci.yml) for Linux, Windows, and macOS on Python 3.11 and 3.14. It runs unit tests, checks the example skills, builds the Python package, and uploads the package artifacts. Workflow execution results are visible in GitHub Actions after the repository is pushed.

For another repository, install this project from its checkout and run:

```sh
skillproof check .agents/skills --strict
skillproof check .claude/skills --format markdown --output reports/skills.md
```

Each command expects an existing skill directory. Exit codes: `0` passed, `1` findings exceeded the selected threshold, `2` command or filesystem error.

## Check coverage

Checks include YAML syntax and duplicate keys, names and directory matching, descriptions, selected optional field types, empty instructions, local inline Markdown links, symlinked resources, common sensitive filenames, duplicate collection names, and unfinished placeholders.

The checks are static. They do not evaluate an assistant's task success, execute bundled scripts, validate host tool permissions, or establish that a bundle is secure. The link parser covers common inline links outside fenced code; reference-style links and anchor correctness are outside this release's scope. See [rules and boundaries](docs/rules.md).

## Development

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python -m pip install build
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for bug reports and pull requests, and [the maintainer guide](docs/maintaining.md) for release and maintenance procedures.

## Sources

The implementation was informed by the [Agent Skills specification](https://agentskills.io/specification), [Codex skills documentation](https://learn.chatgpt.com/docs/build-skills), and [Claude Code skills documentation](https://code.claude.com/docs/en/skills), checked on 2026-10-21. This is an independent community project.

## License

[MIT](LICENSE).
