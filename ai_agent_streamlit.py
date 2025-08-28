import streamlit as st
import google.generativeai as genai
import json
import io
from datetime import datetime
import pandas as pd

# Configure the page
st.set_page_config(
    page_title="AI Assignment Grader",
    page_icon="🤖",
    layout="wide"
)

class AssignmentGrader:
    def __init__(self, api_key):
        #Initialize the grader with user-provided API key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def test_api_connection(self):
        #Test if the API key is valid
        try:
            # test prompt
            response = self.model.generate_content("Say 'API key is working correctly'")
            return True, response.text
        except Exception as e:
            return False, str(e)
    
    def extract_notebook_code(self, uploaded_file):
        #Extract Python code from uploaded Jupyter notebook
        try:
            # Read the uploaded file
            notebook_content = uploaded_file.read()
            notebook = json.loads(notebook_content)
            
            code_cells = []
            for cell in notebook['cells']:
                if cell['cell_type'] == 'code':
                    code = ''.join(cell['source'])
                    if code.strip():
                        code_cells.append(code)
            
            return '\n\n# --- Next Cell ---\n\n'.join(code_cells)
        
        except Exception as e:
            st.error(f"Error reading notebook: {e}")
            return None
    
    def grade_assignment(self, assignment_text, solution_code):
        #Grade the assignment using Google Gemini
        
        prompt = f"""You are an expert programming instructor. Grade this assignment carefully.

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

        try:
            with st.spinner('🧠 AI is grading your assignment...'):
                response = self.model.generate_content(prompt)
                return response.text
        
        except Exception as e:
            return f"Error calling Gemini API: {e}"

def show_api_key_setup():
    """Display API key setup instructions"""
    st.header("🔑 API Key Setup")
    st.markdown("""
    ### How to Get Your Google Gemini API Key:
    
    1. **Go to Google AI Studio**: Visit [https://aistudio.google.com/](https://aistudio.google.com/)
    
    2. **Sign in**: Use your Google account to sign in
    
    3. **Get API Key**:
       - Click on "Get API Key" in the left sidebar
       - Click "Create API Key"
       - Choose "Create API key in new project" (recommended for beginners)
       - Copy your API key
    
    4. **Important Notes**:
       - Keep your API key secure and don't share it publicly
       - The key starts with "AIza..." 
       - Free tier includes generous usage limits
       - You can monitor usage in the Google AI Studio dashboard
    
    ### Pricing Information:
    - **Free Tier**: 15 requests per minute, 1 million tokens per minute, 1500 requests per day
    - **Pay-as-you-go**: Very affordable rates for additional usage
    - Most classroom assignments will stay within free limits
    """)
    
    st.info("💡 **Tip**: Your API key is only stored in your browser session and is not saved anywhere on our servers!")

def parse_grading_results(results_text):
    #Parse the grading results into structured data
    lines = results_text.split('\n')
    parsed = {}
    
    for line in lines:
        line = line.strip()
        if line.startswith('SCORE:'):
            parsed['score'] = line.replace('SCORE:', '').strip()
        elif line.startswith('GRADE:'):
            parsed['grade'] = line.replace('GRADE:', '').strip()
        elif line.startswith('CORRECTNESS:'):
            parsed['correctness'] = line.replace('CORRECTNESS:', '').strip()
        elif line.startswith('CODE_QUALITY:'):
            parsed['code_quality'] = line.replace('CODE_QUALITY:', '').strip()
        elif line.startswith('COMPLETENESS:'):
            parsed['completeness'] = line.replace('COMPLETENESS:', '').strip()
        elif line.startswith('EFFICIENCY:'):
            parsed['efficiency'] = line.replace('EFFICIENCY:', '').strip()
        elif line.startswith('FEEDBACK:'):
            parsed['feedback'] = line.replace('FEEDBACK:', '').strip()
        elif line.startswith('SUGGESTIONS:'):
            parsed['suggestions'] = line.replace('SUGGESTIONS:', '').strip()
        elif line.startswith('STRENGTHS:'):
            parsed['strengths'] = line.replace('STRENGTHS:', '').strip()
        elif line.startswith('WEAKNESSES:'):
            parsed['weaknesses'] = line.replace('WEAKNESSES:', '').strip()
    
    return parsed

def main():
    # Title and description
    st.title("🤖 AI Assignment Grader")
    st.markdown("Upload your assignment requirements and student solution to get instant AI-powered grading!")
    
    # Check if API key is provided
    if 'api_key_validated' not in st.session_state:
        st.session_state.api_key_validated = False
    
    if 'grader' not in st.session_state:
        st.session_state.grader = None
    
    # API Key Setup Section
    if not st.session_state.api_key_validated:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🔑 Enter Your API Key")
            
            api_key = st.text_input(
                "Google Gemini API Key:",
                type="password",
                placeholder="AIza...",
                help="Your API key will not be stored and is only used for this session"
            )
            
            if st.button("✅ Validate API Key", type="primary"):
                if api_key:
                    with st.spinner("Testing API key..."):
                        try:
                            test_grader = AssignmentGrader(api_key)
                            is_valid, message = test_grader.test_api_connection()
                            
                            if is_valid:
                                st.success("✅ API Key is valid! You can now use the grader.")
                                st.session_state.api_key_validated = True
                                st.session_state.grader = test_grader
                                st.session_state.api_key = api_key
                                st.rerun()
                            else:
                                st.error(f"❌ Invalid API Key: {message}")
                        except Exception as e:
                            st.error(f"❌ Error testing API key: {str(e)}")
                else:
                    st.warning("Please enter your API key")
        
        with col2:
            show_api_key_setup()
        
        return  # Don't show the rest of the interface until API key is validated
    
    # Show current API key status
    st.success("🔑 API Key validated! Ready to grade assignments.")
    if st.button("🔄 Change API Key"):
        st.session_state.api_key_validated = False
        st.session_state.grader = None
        if 'api_key' in st.session_state:
            del st.session_state.api_key
        st.rerun()
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📚 Instructions")
        st.markdown("""
        1. **✅ API Key**: Already validated!
        2. **Upload Assignment**: Paste or upload the assignment requirements
        3. **Upload Solution**: Upload Python file (.py) or Jupyter notebook (.ipynb)
        4. **Click Grade**: Get instant detailed feedback!
        
        **Supported Formats:**
        - Python files (.py)
        - Jupyter notebooks (.ipynb)
        - Text paste
        """)
        
        st.header("📊 Grading Criteria")
        st.markdown("""
        - **Correctness (40%)**: Does it work?
        - **Code Quality (25%)**: Is it clean?
        - **Completeness (20%)**: All requirements?
        - **Efficiency (15%)**: Is it optimized?
        """)
        
        st.header("💰 API Usage")
        st.markdown("""
        - Free tier: 15 requests/min
        - Each grading = 1 request
        - Monitor usage in Google AI Studio
        """)
    
    # Main interface
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 Assignment Requirements")
        assignment_input_method = st.radio(
            "How do you want to provide the assignment?",
            ["Type/Paste Text", "Upload File"]
        )
        
        assignment_text = ""
        if assignment_input_method == "Type/Paste Text":
            assignment_text = st.text_area(
                "Paste the assignment requirements here:",
                height=300,
                placeholder="Example: Write a Python function that calculates the factorial of a number..."
            )
        else:
            assignment_file = st.file_uploader(
                "Upload assignment file",
                type=['txt', 'md'],
                key="assignment"
            )
            if assignment_file:
                assignment_text = str(assignment_file.read(), "utf-8")
                st.text_area("Assignment content:", assignment_text, height=200)
    
    with col2:
        st.header("💻 Student Solution")
        solution_input_method = st.radio(
            "How do you want to provide the solution?",
            ["Upload Python File", "Upload Jupyter Notebook", "Type/Paste Code"]
        )
        
        solution_code = ""
        if solution_input_method == "Type/Paste Code":
            solution_code = st.text_area(
                "Paste the Python code here:",
                height=300,
                placeholder="def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)"
            )
        elif solution_input_method == "Upload Python File": #python file
            solution_file = st.file_uploader(
                "Upload Python file (.py)",
                type=['py'],
                key="python_solution"
            )
            if solution_file:
                solution_code = str(solution_file.read(), "utf-8")
                st.code(solution_code, language='python')
        else:  # Jupyter Notebook
            notebook_file = st.file_uploader(
                "Upload Jupyter notebook (.ipynb)",
                type=['ipynb'],
                key="notebook_solution"
            )
            if notebook_file:
                solution_code = st.session_state.grader.extract_notebook_code(notebook_file)
                if solution_code:
                    st.code(solution_code, language='python')
    
    # Grade button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        grade_button = st.button("🎯 Grade Assignment", type="primary", use_container_width=True)
    
    # Grading results
    if grade_button:
        if not assignment_text.strip():
            st.error("Please provide assignment requirements!")
            return
        
        if not solution_code or not solution_code.strip():
            st.error("Please provide student solution!")
            return
        
        # Perform grading
        results = st.session_state.grader.grade_assignment(assignment_text, solution_code)
        
        if "Error" in results:
            st.error(results)
            return
        
        # Parse and display results
        parsed_results = parse_grading_results(results)
        
        st.markdown("---")
        st.header("📊 Grading Results")
        
        # Score display
        col1, col2, col3 = st.columns(3)
        with col1:
            score = parsed_results.get('score', 'N/A')
            st.metric("Overall Score", f"{score}/100")
        with col2:
            grade = parsed_results.get('grade', 'N/A')
            st.metric("Letter Grade", grade)
        with col3:
            st.metric("Timestamp", datetime.now().strftime("%H:%M:%S"))
        
        # Detailed breakdown
        st.subheader("📈 Detailed Breakdown")
        breakdown_col1, breakdown_col2 = st.columns(2)
        
        with breakdown_col1:
            if 'correctness' in parsed_results:
                st.write(f"**Correctness (40%):** {parsed_results['correctness']}")
            if 'code_quality' in parsed_results:
                st.write(f"**Code Quality (25%):** {parsed_results['code_quality']}")
        
        with breakdown_col2:
            if 'completeness' in parsed_results:
                st.write(f"**Completeness (20%):** {parsed_results['completeness']}")
            if 'efficiency' in parsed_results:
                st.write(f"**Efficiency (15%):** {parsed_results['efficiency']}")
        
        # Feedback sections
        if 'feedback' in parsed_results:
            st.subheader("💬 Detailed Feedback")
            st.write(parsed_results['feedback'])
        
        col1, col2 = st.columns(2)
        with col1:
            if 'strengths' in parsed_results:
                st.subheader("✅ Strengths")
                st.success(parsed_results['strengths'])
        
        with col2:
            if 'weaknesses' in parsed_results:
                st.subheader("⚠️ Areas for Improvement")
                st.warning(parsed_results['weaknesses'])
        
        if 'suggestions' in parsed_results:
            st.subheader("💡 Suggestions")
            st.info(parsed_results['suggestions'])
        
        # Download results
        st.markdown("---")
        st.subheader("💾 Save Results")
        
        # Create downloadable report
        report = f"""ASSIGNMENT GRADING REPORT
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

OVERALL SCORE: {parsed_results.get('score', 'N/A')}/100
GRADE: {parsed_results.get('grade', 'N/A')}

DETAILED BREAKDOWN:
- Correctness (40%): {parsed_results.get('correctness', 'N/A')}
- Code Quality (25%): {parsed_results.get('code_quality', 'N/A')}
- Completeness (20%): {parsed_results.get('completeness', 'N/A')}
- Efficiency (15%): {parsed_results.get('efficiency', 'N/A')}

FEEDBACK:
{parsed_results.get('feedback', 'N/A')}

STRENGTHS:
{parsed_results.get('strengths', 'N/A')}

WEAKNESSES:
{parsed_results.get('weaknesses', 'N/A')}

SUGGESTIONS:
{parsed_results.get('suggestions', 'N/A')}

ASSIGNMENT REQUIREMENTS:
{assignment_text}

STUDENT SOLUTION:
{solution_code}
"""
        
        st.download_button(
            label="📄 Download Detailed Report",
            data=report,
            file_name=f"grading_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()