| Metadata | Value |
|---|---|
| created | 2026-04-24 13:48:34 BST |
| last_updated | 2026-04-24 13:48:34 BST |
| prompt_used | 2026-04-25 07:45:43 BST |

# Frontend Agent Brief 3

Verify frontend AI chat wiring, visible Review context handoff, local smoke paths, and live end-to-end readiness for tasks `112`, `113`, `105`, and `119`.

## Runtime Paths

- Standard app: `http://localhost:8501`
- Synthetic Review fixture: `http://localhost:8501/?alloca_dev_review_fixture=1`
- Frontend-only Review fixture without live Perplexity: `http://localhost:8501/?alloca_dev_review_fixture=frontend-check&alloca_dev_no_ai_env=1`
- Missing-key Configuration path: `http://localhost:8501/?alloca_dev_no_ai_env=1`

