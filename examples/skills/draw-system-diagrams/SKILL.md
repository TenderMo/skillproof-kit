---
name: draw-system-diagrams
description: Create editable Mermaid architecture diagrams, process flowcharts, sequence diagrams, and dependency graphs when users need to explain how a software system works.
license: MIT
---

# Draw system diagrams

Identify the components, data, and interactions that the requested diagram must explain. Derive relationships from source files or facts supplied by the user. Label proposed components as planned.

Choose a flowchart for decisions and processes, a sequence diagram for ordered interactions, or a graph for architecture and dependencies. Label edges when their direction alone is ambiguous. Keep each diagram focused on one question; split dense diagrams by subsystem.

Use [references/mermaid-example.md](references/mermaid-example.md) for a small editable example. Return Mermaid source with a caption describing the diagram's scope. If an available renderer exports SVG or PNG, inspect that output for clipped labels and confusing crossings before delivery. Report rendering as unverified when no renderer is available.
