import os
import sys
import json
import argparse
from datetime import datetime

from dotenv import load_dotenv

# Providers
import google.generativeai as genai
from openai import OpenAI, OpenAIError

# ----------------------------
# Utilities
# ----------------------------
def extract_notebook_code(notebook_path: str):
    """Extract Python code from a Jupyter notebook."""
    try:
        with open(notebook_path, "r", encoding="utf-8") as f:
            nb = json.load(f)
        cells = []
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                code = "".join(cell.get("source", []))
                if code.strip():
                    cells.append(code)
        return "\n\n# --- Next Cell ---\n\n".join(cells)
    except Exception as e:
        print(f"Error reading notebook: {e}")
        return None

def read_text_file(path: str):
    """Read a plain text file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {path}: {e}")
        return None

def save_results(results: str, output_file: str):
    """Save grading results to a file with timestamp."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("ASSIGNMENT GRADING RESULTS\n")
        f.write(f"Generated on: {ts}\n")
        f.write("=" * 50 + "\n\n")
        f.write(results)
    print(f"Results saved to: {output_file}")

# ----------------------------
# Prompt
# ----------------------------
def build_prompt(assignment_text: str, solution_code: str) -> str:
    return f"""You are an expert programming instructor. Grade this assignment carefully.

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
WEAKNESSES: [areas that need improvement]"""

# ----------------------------
# Provider adapters
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
        # New OpenAI SDK (>=1.0.0) style
        resp = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=700,
        )
        return resp.choices[0].message.content

# ----------------------------
# Main orchestration
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="AI Assignment Grader (Gemini/OpenAI)")
    parser.add_argument("--provider", choices=["gemini", "openai"], default="openai",
                        help="Which provider to use (default: openai)")
    parser.add_argument("--assignment", default="assignment.txt", help="Path to assignment description")
    parser.add_argument("--notebook", default="solution.ipynb", help="Path to student's Jupyter notebook")
    parser.add_argument("--pyfile",   default="solution.py",     help="Path to student's Python file (fallback)")
    parser.add_argument("--out",      default="grading_results.txt", help="Output file")
    parser.add_argument("--openai-model", default="gpt-4o-mini", help="OpenAI model to use")
    parser.add_argument("--gemini-model", default="gemini-1.5-flash", help="Gemini model to use")
    args = parser.parse_args()

    # Load env
    load_dotenv()

    # Pick provider
    if args.provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("ERROR: OPENAI_API_KEY not set (in .env or environment).")
            sys.exit(1)
        grader = OpenAIGrader(api_key, model_name=args.openai_model)
        print("Using OpenAI provider:", args.openai_model)
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY not set (in .env or environment).")
            sys.exit(1)
        grader = GeminiGrader(api_key, model_name=args.gemini_model)
        print("Using Gemini provider:", args.gemini_model)

    # Read assignment
    print("Reading assignment requirements...")
    assignment_text = read_text_file(args.assignment)
    if not assignment_text:
        print("Could not read assignment file!")
        sys.exit(1)

    # Read student solution (ipynb preferred; fall back to .py)
    print("Reading student solution...")
    if os.path.exists(args.notebook):
        solution_code = extract_notebook_code(args.notebook)
        print(f"Extracted code from notebook: {args.notebook}")
    elif os.path.exists(args.pyfile):
        solution_code = read_text_file(args.pyfile)
        print(f"Read Python file: {args.pyfile}")
    else:
        print("No solution file found! Provide a .ipynb or .py.")
        sys.exit(1)

    if not solution_code:
        print("Could not read solution code!")
        sys.exit(1)

    # Build prompt & grade
    prompt = build_prompt(assignment_text, solution_code)
    print("Sending to AI for grading...")
    try:
        results = grader.grade(prompt)
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Provider error: {e}")
        sys.exit(1)

    # Show + save
    print("\n" + "-" * 40)
    print("GRADING RESULTS:")
    print("-" * 40)
    print(results)
    save_results(results, args.out)
    print(f"\n✅ Grading complete! Results saved to {args.out}")

if __name__ == "__main__":
    # Ensure Windows console prints UTF-8 nicely
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
