# AI Assignment Grader (OpenAI + Gemini) — CLI & Streamlit Web App

Grade student programming assignments using either **OpenAI** or **Google Gemini**.  
This repo contains **two ways** to run the grader:

1. **Command-line tool** (reads assignment + .ipynb/.py and prints a rubric-based evaluation)
2. **Streamlit web app** (browser UI; can use **server-side secrets** so users don’t need their own key)

> ✅ Secrets-safe: local `.env` for CLI, **Streamlit Secrets** for the web app (never commit real keys).  
> ✅ Provider switch: **OpenAI** or **Gemini**.  
> ✅ Works with **Jupyter notebooks** (extracts code cells) or plain **Python files**.

---

## Features

- 📥 Reads assignment brief from `assignment.txt`.
- 📓 Extracts code from **Jupyter notebooks** (`solution.ipynb`) or reads a `.py` solution.
- 🔁 Choose provider at runtime: **OpenAI** (`gpt-4o-mini` default) or **Gemini** (`gemini-1.5-flash` default).
- 📝 Saves results to `grading_results.txt` with a timestamp.
- 🔒 Secrets never committed: `.env` ignored; `.env.example` included.

---

## Folder Structure (example)

```
├─ ai_agent_test.py # CLI script (supports OpenAI + Gemini)
├─ streamlit_app.py # Streamlit app entry (rename if your app file differs)
├─ app/ # (optional) shared modules
├─ .env.example # template for local secrets (NO real keys)
├─ .gitignore # ignore rules (includes .env)
└─ requirements.txt
```

**requirements.txt** should include at least:

```
streamlit
google-generativeai
openai>=1.0.0
python-dotenv
```

### 2) Configure API keys (choose what you use)

**CLI (local dev)**: create a local .env (do not commit it). A sample .env.example is provided.

## .env (local only; never commit)

OPENAI_API_KEY=sk-... # for OpenAI provider
GEMINI_API_KEY=AIza... # for Gemini provider

**Streamlit Cloud (web app)**: set secrets in the app’s Settings

```
# .env (local only; never commit)
OPENAI_API_KEY=sk-...         # for OpenAI provider
GEMINI_API_KEY=AIza...        # for Gemini provider
```

**Windows (PowerShell) alternative:**

```powershell
setx OPENAI_API_KEY "sk-..."
setx GEMINI_API_KEY "AIza..."
# restart terminal/IDE so Python can read them
```

## Usage

### Grade with **OpenAI**

```bash
python ai_agent_test.py --provider openai --assignment assignment.txt --notebook solution.ipynb
# or if you have a .py file instead of a notebook:
python ai_agent_test.py --provider openai --pyfile solution.py
```

### Grade with **Gemini**

```bash
python ai_agent_test.py --provider gemini --assignment assignment.txt --notebook solution.ipynb
# or:
python ai_agent_test.py --provider gemini --pyfile solution.py
```

### Optional flags

- `--openai-model gpt-4o-mini` (default)
- `--gemini-model gemini-1.5-flash` (default)
- `--out grading_results.txt` (change output file path)

Example:

```bash
python grader.py --provider openai --assignment data/assign1.txt --pyfile submissions/alice.py --out out/alice.txt
```

---

## What the tool sends to the model

The grader builds a single prompt that contains:

- The **assignment requirements** (full text of `assignment.txt`).
- The **student code** (extracted from `solution.ipynb` or from `solution.py`).

## The model responds with a rubric‑based evaluation, including total score, letter grade, and section scores for **Correctness**, **Code Quality**, **Completeness**, and **Efficiency**, plus free‑text feedback and suggestions.
