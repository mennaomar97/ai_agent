import streamlit as st
import json
import os
import time
from datetime import datetime

# Providers
import google.generativeai as genai
from openai import OpenAI, OpenAIError

# ----------------------------
# Streamlit page config
# ----------------------------
st.set_page_config(
    page_title="AI Assignment Grader",
    page_icon="🧪",
    layout="centered"
)

st.title("🧪 AI Assignment Grader")
st.caption("Grade assignments using OpenAI or Google Gemini — without exposing your API key to users.")

# ----------------------------
# Helper: prompt builder
# ----------------------------
def build_prompt(assignment_text: str, solution_code: str) -> str:
    return f'''You are an expert programming instructor. Grade this assignment carefully.

ASSIGNMENT REQUIREMENTS:
{assignment_text}

STUDENT'S PYTHON SOLUTION:
{solution_code}

Evaluate based on:
1. Correctness (40%) - Does the code solve the problem correctly?
2. Code Quality (25%) - Is it readable, well-structured, follows best practices?
3. Completeness (20%) - Are all requirements addressed?
4. Efficiency (15%) - Is the solution reasonably efficient?

Provide your response in this EXACT format:
SCORE: [number 0-100]
GRADE: [A/B/C/D/F]
CORRECTNESS: [score/40] - [brief explanation]
CODE_QUALITY: [score/25] - [brief explanation]
COMPLETENESS: [score/20] - [brief explanation]
EFFICIENCY: [score/15] - [brief explanation]
FEEDBACK: [detailed feedback about what works and what doesn't]
SUGGESTIONS: [specific improvements needed]
STRENGTHS: [what the student did well]
WEAKNESSES: [areas that need improvement]'''

# ----------------------------
# Helpers: file reading/extraction
# ----------------------------
def read_text_file(uploaded) -> str | None:
    try:
        data = uploaded.read()
        # Try utf-8 then fallback to latin-1
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None

def extract_notebook_code(uploaded_ipynb) -> str | None:
    try:
        raw = uploaded_ipynb.read()
        nb = json.loads(raw.decode("utf-8"))
        cells = []
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                src = cell.get("source", [])
                code = "".join(src)
                if code.strip():
                    cells.append(code)
        if not cells:
            return ""
        return "\n\n# --- Next Cell ---\n\n".join(cells)
    except Exception as e:
        st.error(f"Error parsing notebook: {e}")
        return None

# ----------------------------
# Providers
# ----------------------------
class GeminiGrader:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def grade(self, prompt: str) -> str:
        resp = self.model.generate_content(prompt)
        return resp.text

class OpenAIGrader:
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def grade(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=900,
        )
        return resp.choices[0].message.content

# ----------------------------
# Rate limiting (per session)
# ----------------------------
MAX_GRADES_PER_SESSION = 20
MIN_SECONDS_BETWEEN_CALLS = 5

if "grades_count" not in st.session_state:
    st.session_state.grades_count = 0
if "last_call_ts" not in st.session_state:
    st.session_state.last_call_ts = 0.0

def allow_call() -> bool:
    now = time.time()
    if st.session_state.grades_count >= MAX_GRADES_PER_SESSION:
        st.error("Daily limit reached. Please try again tomorrow.")
        return False
    if now - st.session_state.last_call_ts < MIN_SECONDS_BETWEEN_CALLS:
        st.warning("Please wait a few seconds before the next grading.")
        return False
    st.session_state.grades_count += 1
    st.session_state.last_call_ts = now
    return True

# ----------------------------
# UI: provider + key source
# ----------------------------
with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("Provider", ["OpenAI", "Gemini"], index=0)
    use_app_key = st.toggle("🔒 Use app's secured API key", value=True, help="Uses Streamlit Secrets on the server. Your key is never exposed.")
    openai_model = st.text_input("OpenAI model", "gpt-4o-mini", disabled=(provider != "OpenAI"))
    gemini_model = st.text_input("Gemini model", "gemini-1.5-flash", disabled=(provider != "Gemini"))

    user_key = None
    if not use_app_key:
        ph = "sk-..." if provider == "OpenAI" else "AIza..."
        user_key = st.text_input(f"{provider} API Key", type="password", placeholder=ph)

def build_grader() -> tuple[object, str] | tuple[None, str]:
    try:
        if provider == "OpenAI":
            api_key = (st.secrets.get("OPENAI_API_KEY") if use_app_key else (user_key or ""))
            if not api_key:
                return None, "OPENAI_API_KEY is not configured. Add it to Streamlit Secrets or input your own."
            return OpenAIGrader(api_key, model_name=openai_model), ""
        else:
            api_key = (st.secrets.get("GEMINI_API_KEY") if use_app_key else (user_key or ""))
            if not api_key:
                return None, "GEMINI_API_KEY is not configured. Add it to Streamlit Secrets or input your own."
            return GeminiGrader(api_key, model_name=gemini_model), ""
    except Exception as e:
        return None, f"Error initializing provider: {e}"

# ----------------------------
# Inputs
# ----------------------------
st.subheader("1) Assignment Requirements")
assign_mode = st.radio("How do you want to provide the assignment?", ["Paste text", "Upload .txt"], horizontal=True)
assignment_text = ""
if assign_mode == "Paste text":
    assignment_text = st.text_area("Paste the assignment brief:", height=180, placeholder="Describe the requirements, rubric, constraints, etc.")
else:
    up_assign = st.file_uploader("Upload assignment.txt", type=["txt"], accept_multiple_files=False)
    if up_assign is not None:
        assignment_text = read_text_file(up_assign) or ""

st.subheader("2) Student Solution")
sol_file = st.file_uploader("Upload student's solution (.ipynb or .py)", type=["ipynb", "py"], accept_multiple_files=False)
solution_code = ""
if sol_file is not None:
    if sol_file.name.lower().endswith(".ipynb"):
        solution_code = extract_notebook_code(sol_file) or ""
    else:
        solution_code = read_text_file(sol_file) or ""

st.divider()
grade_btn = st.button("🚀 Grade Assignment", type="primary", use_container_width=True)

# ----------------------------
# Action
# ----------------------------
if grade_btn:
    if not assignment_text.strip():
        st.warning("Please provide the assignment requirements.")
        st.stop()
    if not solution_code.strip():
        st.warning("Please upload a .ipynb or .py with student code.")
        st.stop()

    grader, err = build_grader()
    if grader is None:
        st.error(err)
        st.stop()

    if not allow_call():
        st.stop()

    prompt = build_prompt(assignment_text, solution_code)
    with st.spinner("Grading in progress..."):
        try:
            results = grader.grade(prompt)
        except OpenAIError as oe:
            st.error(f"OpenAI error: {oe}")
            st.stop()
        except Exception as e:
            st.error(f"Provider error: {e}")
            st.stop()

    st.success("✅ Grading complete")
    st.text_area("Results", value=results, height=400)

    # Save results in session (NOT the key)
    if "results_history" not in st.session_state:
        st.session_state.results_history = []
    st.session_state.results_history.append({
        "ts": datetime.utcnow().isoformat() + "Z",
        "provider": provider,
        "model": openai_model if provider == "OpenAI" else gemini_model,
        "lengths": {"assignment_chars": len(assignment_text), "solution_chars": len(solution_code)},
    })

    with st.expander("Session usage info"):
        st.write(st.session_state.results_history)
