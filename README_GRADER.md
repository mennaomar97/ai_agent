# AI Assignment Grader (OpenAI + Gemini)

A command‑line tool that grades student programming assignments using either **OpenAI** or **Google Gemini**.  
It reads the assignment requirements and a student solution (**.ipynb** or **.py**), sends them to the selected provider, and saves a structured textual evaluation.

> ✅ Secrets-safe: uses environment variables / `.env` locally (never commit real keys).  
> ✅ Provider switch: `--provider openai` or `--provider gemini`.  
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
your-repo/
├─ ai_agent_test.py                 # main script (supports OpenAI + Gemini)
├─ .env.example              # template for local secrets (NO real keys)
├─ .gitignore                # ignore rules (includes .env)
└─ requirements.txt
```

## Setup

### 1) Python deps

```bash
pip install -r requirements.txt
```

**requirements.txt** should include at least:

```
google-generativeai
openai>=1.0.0
python-dotenv
```

### 2) Configure API keys (choose what you use)

Create a local **`.env`** (do **not** commit it). A sample `.env.example` is provided.

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

The model responds with a rubric‑based evaluation, including total score, letter grade, and section scores for **Correctness**, **Code Quality**, **Completeness**, and **Efficiency**, plus free‑text feedback and suggestions.

> If you want **strict JSON** output instead of free text, we can modify the prompt and add lightweight parsing—ask and we’ll include it.

---
