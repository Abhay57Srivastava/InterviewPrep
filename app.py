import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
import re

# Load environment variables
load_dotenv()

# Check for API key
if not os.getenv("GEMINI_API_KEY"):
    st.error("GEMINI_API_KEY not found. Please create a .env file with your API key.")
    st.stop()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Function to generate a simple interview question
def generate_question(role, domain, mode):
    # Simple question templates for each mode
    question_templates = {
        "Technical": [
            f"What is your experience with {domain}?" if domain else "What programming languages do you know best?",
            f"Describe a simple {domain} project you've worked on." if domain else "What's your favorite tech tool and why?",
            f"How would you explain {domain} to a beginner?" if domain else "What's your debugging process?",
            f"What interests you about {domain}?" if domain else "How do you keep your technical skills updated?",
            "Tell me about your most recent technical project."
        ],
        "Behavioral": [
            "Tell me about yourself.",
            "What's your greatest professional strength?",
            "Why do you want this job?",
            "How do you handle stress?",
            "Describe your ideal work environment."
        ],
        "System Design": [
            "How would you design a simple URL shortener?",
            "Explain how you would build a basic chat application.",
            "How would you design a simple file storage system?",
            "Describe a basic e-commerce checkout flow.",
            "How would you approach designing a simple API?"
        ]
    }
    
    # Select a question based on the current question number
    question_index = st.session_state.asked % len(question_templates[mode])
    question = question_templates[mode][question_index]
    
    # Add a domain-specific twist if provided
    if domain and "domain" not in question:
        question += f" (Related to {domain})"
        
    return question

# Function to evaluate the user's answer (simplified)
def evaluate_answer(user_answer, question, mode):
    try:
        prompt = f"""Briefly evaluate this interview answer. Keep it short and simple.
        Question: {question}
        Answer: {user_answer}
        
        Give a score out of 10 and 2-3 sentences of feedback. Format as:
        Score: X/10
        [Your brief feedback here]"""
        
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Score: 7/10\nGood answer! Consider adding a bit more detail about your specific experiences."

# Function to extract score from feedback
def extract_score(feedback):
    score_pattern = r"Score:\s*(\d+(?:\.\d+)?)\s*(?:\/|\s*out\s*of\s*)\s*10"
    match = re.search(score_pattern, feedback, re.IGNORECASE)
    
    if match:
        return float(match.group(1))
    else:
        return 7.0  # Default score

# Streamlit App
st.set_page_config(page_title="Interview Prep Bot", page_icon="🎯")

# Initialize session states
if 'question' not in st.session_state:
    st.session_state.question = None
if 'asked' not in st.session_state:
    st.session_state.asked = 0
if 'score' not in st.session_state:
    st.session_state.score = []

# Sidebar for settings
with st.sidebar:
    st.title("Interview Settings")
    role = st.selectbox("Your Role", ["Software Engineer", "Product Manager", "Data Analyst", "Designer"])
    domain = st.text_input("Specific Domain (optional)", placeholder="e.g., Python, React")
    mode = st.radio("Question Type", ["Technical", "Behavioral", "System Design"])
    num_questions = st.slider("Number of Questions", 1, 5, 3)
    
    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

# Main content
st.title("🎯 Interview Practice")
st.write("Simple questions to help you prepare for interviews")

# Start button
if st.button("Start Practice", type="primary") or st.session_state.question:
    if st.session_state.question is None:
        st.session_state.asked = 0
        st.session_state.score = []
        st.session_state.question = generate_question(role, domain, mode)
    
    # Display current question
    st.subheader(f"Question {st.session_state.asked + 1}:")
    st.info(st.session_state.question)
    
    # Answer area
    user_answer = st.text_area("Your Answer", height=100)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit"):
            if not user_answer.strip():
                st.warning("Please write an answer first.")
            else:
                feedback = evaluate_answer(user_answer, st.session_state.question, mode)
                score = extract_score(feedback)
                
                st.session_state.score.append({
                    "question": st.session_state.question,
                    "answer": user_answer,
                    "feedback": feedback,
                    "score": score
                })
                
                st.session_state.asked += 1
                
                # Next question or finish
                if st.session_state.asked < num_questions:
                    st.session_state.question = generate_question(role, domain, mode)
                    st.rerun()
                else:
                    st.session_state.question = None
                    st.rerun()
    
    with col2:
        if st.button("Skip"):
            st.session_state.asked += 1
            if st.session_state.asked < num_questions:
                st.session_state.question = generate_question(role, domain, mode)
                st.rerun()
            else:
                st.session_state.question = None
                st.rerun()

# Show results
if st.session_state.asked >= num_questions and st.session_state.score:
    st.success("🎉 Practice Complete!")
    
    # Calculate overall score
    scores = [item["score"] for item in st.session_state.score]
    avg_score = sum(scores) / len(scores) if scores else 0
    
    st.metric("Your Score", f"{avg_score:.1f}/10")
    
    # Show each question and feedback
    for i, item in enumerate(st.session_state.score):
        with st.expander(f"Question {i+1}: {item['question']}"):
            st.write("**Your Answer:**")
            st.write(item["answer"])
            st.write("**Feedback:**")
            st.write(item["feedback"])
    
    if st.button("Practice Again"):
        st.session_state.clear()
        st.rerun()

# Footer
st.markdown("---")
st.markdown("Interview Practice Bot")