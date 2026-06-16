# Branch Context

## Current Branch Chain

The actual branch chain is:

```text
uat
  └─ fix/actualizacion_herramientas_claude
       └─ fix/codex
            └─ feature/runtime-agentico
```

After the runtime implementation reaches a stable first milestone, create the
capabilities branch from `feature/runtime-agentico`:

```text
uat
  └─ fix/actualizacion_herramientas_claude
       └─ fix/codex
            └─ feature/runtime-agentico
                 └─ feature/capabilities_skills_mcp
```

## Important Clarification

`fix/codex` was **not** created directly from `uat`.

It was created from the branch that was active at the time:

```text
fix/actualizacion_herramientas_claude
```

That branch was already based on `origin/uat`, so `fix/codex` indirectly includes `uat` plus the changes from `fix/actualizacion_herramientas_claude`.

## Relevant Commits

At the time this note was created:

```text
origin/uat                         8eef03d
fix/actualizacion_herramientas_claude c00244d
fix/codex                          1b7d634
feature/runtime-agentico           1b7d634
```

`fix/codex` contains the preserved stabilization/debugging/planning work:

```text
1b7d634 chore: preserve codex stabilization work
```

`feature/runtime-agentico` was created from `fix/codex` and is the working branch for the runtime architecture implementation.

## Intended Workflow

Use `feature/runtime-agentico` for the runtime implementation work.

Use `fix/codex` as the preserved base containing the pending stabilization changes.

Use `feature/capabilities_skills_mcp` later for the skills/MCP capability layer,
created from `feature/runtime-agentico` after the runtime primitives are stable.

When preparing a PR, be aware that the feature branch includes:

1. `uat`
2. changes from `fix/actualizacion_herramientas_claude`
3. the `fix/codex` stabilization commit
4. runtime implementation commits from `feature/runtime-agentico`

Do not assume `feature/runtime-agentico` is based directly on `uat`.

Do not create `feature/capabilities_skills_mcp` from `uat` or `fix/codex`; it
must be based on `feature/runtime-agentico` so it inherits the runtime
primitives.

## Local Untracked Files

`.vscode/` was intentionally left uncommitted because it contains local IDE/MCP/debugger configuration.
