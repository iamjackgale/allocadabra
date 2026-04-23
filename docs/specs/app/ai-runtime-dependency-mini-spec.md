| Metadata | Value |
|---|---|
| created | 2026-04-23 12:18:43 BST |
| last_updated | 2026-04-23 12:18:43 BST |

# AI Runtime Dependency Mini Spec

## Target Files

- `pyproject.toml`
- `uv.lock`

## Requested Owner

- Orchestrator/dependency owner approves and integrates shared dependency changes.
- AI/Perplexity Agent consumes the dependency after it lands.

## Proposed Change

Add the Perplexity Python SDK dependency:

```toml
dependencies = [
  "perplexityai",
]
```

Then regenerate `uv.lock`.

## Reason

The AI provider is implemented against the required Perplexity SDK. Dependency files are shared cross-agent territory and sit outside AI/Perplexity Agent ownership.

Until this dependency lands, configured provider calls can only return a recoverable package-not-installed error.

## Interface/Contract Impact

- Enables `app.ai.provider.PerplexityProvider` to import the SDK at runtime.
- Does not change AI prompt contracts, metadata schemas, storage contracts, or frontend call shapes.
- Keeps V1 aligned with local Python/Streamlit execution.

## Risks And Dependencies

- SDK import path and API shape must be validated by the AI/Perplexity Agent after installation.
- Live provider verification still requires `PERPLEXITY_API_KEY`.
- Future SDK API drift should be caught by AI validation tests or smoke checks.
