# Mermaid workflow example

Use explicit node IDs and short labels. Edge labels should describe the relationship.

```mermaid
flowchart LR
    author[Skill author] -->|edits| source[SKILL.md and resources]
    source -->|checked by| checker[SkillProof]
    checker -->|findings| report[Quality report]
    checker -->|valid bundle| archive[Release ZIP]
```

This graph explains the path from an authored skill to the report and release archive. It makes no claim about a particular host's runtime behavior.
