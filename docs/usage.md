# CLI guide

Run `skillproof --help` or `skillproof COMMAND --help` for exact arguments. All checks operate locally and require no model API key.

## Check a skill or collection

```sh
skillproof check examples/skills
skillproof check examples/skills/write-project-docs/SKILL.md
skillproof check examples/skills --strict
skillproof check examples/skills --format json --output reports/check.json
skillproof check examples/skills --format markdown --output reports/check.md
```

Discovery recursively searches for `SKILL.md`, including host folders such as `.agents/skills` and `.claude/skills`. It skips `.git`, `.venv`, `venv`, `node_modules`, `__pycache__`, `dist`, `build`, and `.pytest_cache`. Symlinked directories are not traversed. Selecting a symlink as the root input is rejected.

Errors fail the check. Warnings fail only with `--strict`. A path containing no skills returns exit code `2`; it does not count as a passing collection. JSON output has `schema_version`, skill and finding counts, and a `findings` array with `rule`, `severity`, `path`, `line`, and `message` fields.

## Initialize

```sh
skillproof init write-api-docs --template docs --dir skills
skillproof init draw-workflows --template diagram --dir skills
skillproof init review-config --template basic --dir skills
```

Each command creates `DIR/NAME/SKILL.md`. Existing directories are refused. Edit the generated instructions to fit the actual task before sharing the skill.

## Generate documentation

```sh
skillproof docs examples/skills --output reports/catalog.md
```

The catalog contains each skill's name, description, and declared license. Omitting `--output` writes to standard output. Existing output files are replaced, so select an output path intended for generated content.

## Generate a resource diagram

```sh
skillproof diagram examples/skills --output reports/skills.mmd
```

The generated Mermaid source connects each skill to its bundled files. It represents containment, not execution or verified runtime dependencies. Paste the source inside a fenced `mermaid` block to preview it on GitHub. A generated example is included as [resources.mmd](resources.mmd).

## Prepare a release

```sh
skillproof pack examples/skills/write-project-docs --strict --output dist/write-project-docs.zip
```

`pack` accepts one skill folder or its `SKILL.md`. It runs the checker first, blocks errors, and optionally blocks warnings. The ZIP contains a top-level folder named after the skill and the regular files beneath it, excluding the discovery cache/build folders. Symlinks and common sensitive filenames block packaging. Choose a new archive path outside the skill directory; existing archives are refused.

Sorted entries and fixed ZIP timestamps produce repeatable bytes for unchanged content and executable modes on the same platform/toolchain. Cross-platform file modes can differ. `pack` prepares a local archive; publishing it to GitHub or a package registry is a separate step.

## Use examples with coding assistants

Copy an example skill's entire folder into the target project's skill directory. For current Codex repository discovery, use `.agents/skills`; for Claude Code, use `.claude/skills`. Keep its `references/` directory alongside `SKILL.md`. Follow the host's current documentation for discovery and invocation:

- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)

This release verifies files and packaging locally. Interactive behavior in the two hosts has not been exercised as part of the initial implementation.
