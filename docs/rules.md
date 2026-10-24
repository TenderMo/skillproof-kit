# Rules and boundaries

The rule set combines shared skill metadata constraints with explicit release conventions. Host extension fields are accepted; this tool is a practical linter rather than a full host schema validator.

| Rule | Level | Check |
| --- | --- | --- |
| SP001 | Error | UTF-8 readability and opening/closing YAML delimiters |
| SP002 | Error | Safe YAML mapping, string keys, no duplicate fields |
| SP003 | Error | Name: 1–64 lowercase ASCII letters/digits with single internal hyphens |
| SP004 | Error | Name matches the containing folder |
| SP005 | Error | Nonempty string description, at most 1,024 characters |
| SP006 | Error | Types for license, compatibility, and string-to-string metadata |
| SP007 | Error | Nonempty Markdown instructions |
| SP008 | Error | Bundled Markdown is readable as UTF-8 |
| SP009 | Error | Inline local resource link exists |
| SP010 | Error | Linked resource stays inside the bundle and is not in an excluded folder |
| SP011 | Error | Portable bundles contain regular files, with no resource symlinks |
| SP012 | Error | Common sensitive filenames are absent |
| SP013 | Warning | Duplicate skill names within a scanned collection |
| SP101 | Warning | Description shorter than 20 characters deserves trigger review |
| SP102 | Warning | Instructions exceed 500 lines |
| SP103 | Warning | Body contains TODO, FIXME, TBD, or an INSERT placeholder |

The 20-character and 500-line thresholds are SkillProof heuristics. They do not establish whether the skill's instructions are effective. SP103 can flag intentional examples; review findings before enabling strict mode on an existing collection.

The sensitive filename list covers `.env`, `.env.*`, `credentials.json`, `id_rsa`, `id_ed25519`, and files ending in `.pem`, `.key`, `.p12`, or `.pfx`. It is a filename heuristic, not a content-based secret scanner. Even `.env.example` is flagged in this release; use a differently named sample or leave it out of the skill bundle.

Markdown checking covers common inline links and images outside fenced code blocks, including percent-decoded paths. External links are not fetched. Reference-style links, code-formatted paths, headings/anchors, raw HTML links, and the full CommonMark grammar are outside its scope.

Single-line link destinations support balanced nested parentheses, Markdown backslash escapes, angle brackets, and optional quoted or parenthesized titles. Missing-resource findings preserve the complete decoded destination. This example checks the file named `guide(v2).md`:

```markdown
[Guide](references/guide(v2).md)
```

See [CommonMark's link destination examples](https://spec.commonmark.org/0.31.2/#example-496).

A closing code fence can have only spaces or tabs after its markers. A fence-like line with trailing text, such as a language name inside a Markdown example, remains literal code; links after the actual closing fence are checked normally. See [CommonMark's fenced code block rules](https://spec.commonmark.org/0.31.2/#fenced-code-blocks).

Claude Code and other hosts add fields to shared metadata. Unknown fields and host-specific `allowed-tools` forms are preserved without validation. Host permission enforcement, script correctness, behavioral evaluation, and malicious-instruction detection require separate review.

The core field rules are based on the [Agent Skills specification](https://agentskills.io/specification). Codex can follow symlinked skills for local discovery; SkillProof deliberately rejects bundled resource symlinks to make its ZIP releases portable. See [Codex's current discovery behavior](https://learn.chatgpt.com/docs/build-skills).
