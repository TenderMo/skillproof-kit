# Maintainer guide

## Daily maintenance

Inspect new issues and failing CI, reproduce a concrete problem, then make a focused change. Run the relevant regression test and the suite before proposing a merge. Update the affected documentation and changelog when public behavior changes. If there is no useful change, record that no action is needed rather than creating cosmetic commits.

Useful work includes fixing false positives, supporting real skill bundles, improving error messages, keeping example commands runnable, and responding to reproducible reports. Review rule changes against both the shared specification and host documentation.

## Release checklist

1. Update `pyproject.toml` and `skillproof/__init__.py` to the same version.
2. Run the unit tests and strict checks on `examples/skills`.
3. Regenerate the catalog and resource graph when examples change.
4. Build a wheel and source distribution with `python -m build`.
5. Install the wheel in a clean environment and run the quick-start commands.
6. Add release notes describing user-visible behavior and known limits.
7. Publish artifacts to the intended repository after verifying them. PyPI publishing requires a separately configured package identity and trusted publishing or credentials.

The included CI workflow builds package artifacts. It does not publish to PyPI or create GitHub releases.

## Roadmap

Proposed v0.2 work, to prioritize with user feedback:

- Configurable rule severity and suppressions with reasons.
- More complete Markdown link parsing.
- Separate host metadata profiles with versioned source references.
- SARIF output for GitHub code scanning.
- Behavioral evaluation fixtures that exercise skills inside their target hosts.

## Open-source support application

Keep application preparation in a private maintainer workspace. Useful evidence includes the public repository, role/permissions, release history, resolved issues, substantive PRs, and examples of users relying on the project. Record actual observations rather than projected adoption.

The official [Codex for Open Source page](https://developers.openai.com/community/codex-for-oss) describes six months of ChatGPT Pro with Codex for selected maintainers. The [program terms](https://learn.chatgpt.com/docs/codex-for-oss-terms) mention usage, ecosystem importance, active maintenance, and maintainer role among review factors. A newly created repository by itself does not establish eligibility. Check the current form and terms before applying.
