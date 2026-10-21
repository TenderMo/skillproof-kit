# Contributing

Start with an issue describing a reproducible problem or a concrete workflow that the tool should support. Include the command, Python version, operating system, expected behavior, and a small sanitized skill fixture.

For a pull request, explain the user-visible behavior, add a regression test when changing analysis or packaging, and update the relevant rule documentation. Avoid submitting credentials or private skill content.

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
skillproof check examples/skills --strict
```

Examples and generated docs should remain consistent. Use the commands in the README to regenerate the catalog and Mermaid graph when needed.
