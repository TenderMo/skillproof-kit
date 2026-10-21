# Architecture

SkillProof Kit is a local Python CLI with a small static analysis core. PyYAML is its only runtime dependency. No network calls or model inference occur during checks, catalog generation, graph generation, or packaging.

```mermaid
flowchart TB
    user[Author / GitHub Actions] --> cli[cli.py: arguments and exit codes]
    cli --> discovery[core.py: discover SKILL.md files]
    discovery --> parse[Safe YAML parsing and metadata validation]
    parse --> resources[Inspect bundled Markdown and files]
    resources --> model[Skill and Finding data models]
    model --> report[Text / JSON / Markdown findings]
    model --> docs[Markdown catalog]
    model --> graph[Mermaid containment graph]
    model --> gate{Release check passed?}
    gate -->|yes| zip[Sorted ZIP entries with fixed timestamps]
    gate -->|no| stop[Nonzero exit code and findings]
```

## Modules

`cli.py` handles commands, templates, output files, and exit codes. `core.py` discovers skills, parses metadata, produces findings, and writes derived outputs. Neither module executes scripts found in a skill.

Each `Skill` stores its source path, metadata, Markdown instructions, and findings. Each `Finding` stores a stable rule code, severity, path, line, and explanation. The JSON report publishes these fields under schema version `1`.

The resource graph shows files included in each skill's inspected inventory. The release path uses the same inventory and rejects symlinks. Python source distributions include examples, documentation, tests, and workflow definitions through `MANIFEST.in`.

## Extension points

Add a rule inside `inspect_skill`, document its code, and add a behavioral regression test. Host-specific schema profiles and configurable thresholds are planned extensions; they are not part of v0.1.0.
