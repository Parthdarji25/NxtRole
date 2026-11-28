# Test fixtures

| File | What it is |
|---|---|
| `resume_synthetic_2026-11-28.txt` | **Synthetic.** An invented person, companies and college, written on 2026-11-28 to test reading resumes and hiding identity. Not a real resume. |
| `ai/*.json` | Real answers from Groq to requests made from the synthetic resume, with identity already removed. Each file name gives the prompt, model and date. Made with `uv run python -m tests.record_ai`. |

Never put a real person's resume or contact details here (golden rule 1, `docs/TESTING.md` section 4).
