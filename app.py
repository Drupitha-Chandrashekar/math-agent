import streamlit as st
from ai_gateway import MathAgentGateway, GatewayRequest
import time
from feedback_handler import FeedbackHandler, Feedback

# Initialize feedback handler
if 'feedback_handler' not in st.session_state:
    st.session_state.feedback_handler = FeedbackHandler()

# Set up Streamlit page configuration
st.set_page_config(
    page_title="Math Tutor with AI Gateway", 
    layout="centered",
    page_icon="📘"
)

# Initialize the AI Gateway (only once using session state)
if 'gateway' not in st.session_state:
    st.session_state.gateway = MathAgentGateway()
    st.session_state.request_history = []

# Title and description
st.title("📘 Math Tutor with AI Gateway")
st.markdown("Ask any mathematics question and get step-by-step explanations!")

# Sidebar with metrics and information
with st.sidebar:
    st.header("🛡 AI Gateway Status")
    
    # Get and display metrics
    metrics = st.session_state.gateway.get_metrics()
    
    st.metric("Total Requests", metrics['total_requests'])
    st.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
    st.metric("Blocked Requests", metrics['blocked_requests'])
    
    if metrics['total_requests'] > 0:
        st.metric("Avg Processing Time", f"{metrics['average_processing_time']:.3f}s")
    
    # Feedback statistics
    fb_stats = st.session_state.feedback_handler.get_feedback_stats()
    st.metric("Total Feedback", fb_stats['total_feedback'])
    st.metric("Avg Feedback Rating", f"{fb_stats['average_rating']:.1f}/5")
    
    # Recent logs
    if st.button("Show Recent Logs"):
        recent_logs = st.session_state.gateway.get_recent_logs(5)
        if recent_logs:
            st.subheader("Recent Requests")
            for i, log in enumerate(reversed(recent_logs), 1):
                with st.expander(f"Request {i}: {log['user_query'][:30]}..."):
                    st.write(f"*Success:* {'✅' if log['success'] else '❌'}")
                    st.write(f"*Processing Time:* {log['processing_time']:.3f}s")
                    st.write(f"*Guardrails Passed:* {log['guardrails_passed']}")
                    st.write(f"*Guardrails Failed:* {log['guardrails_failed']}")
    
    if st.button("Reset Gateway Metrics"):
        st.session_state.gateway.reset_metrics()
        st.success("Metrics reset!")
        st.rerun()

# Main interface
st.header("Ask Your Math Question")

# Input field
user_question = st.text_input(
    "Enter your mathematics question:",
    placeholder="e.g., Solve x^2 - 5x + 6 = 0"
)

# Submit button and processing
if st.button("🔍 Get Solution", type="primary") and user_question:
    
    # Show processing status
    with st.spinner("🤖 Processing through AI Gateway..."):
        
        # Create gateway request
        request = GatewayRequest(user_query=user_question)
        
        # Process through gateway
        start_time = time.time()
        response = st.session_state.gateway.process_request(request)
        processing_time = time.time() - start_time
        
        # Store in history
        st.session_state.request_history.append({
            'question': user_question,
            'response': response,
            'timestamp': time.time()
        })
    
    # Display results
    st.markdown("---")
    
    # Success/failure indicator
    if response.success:
        st.success(f"✅ Solution found! (Confidence: {response.confidence:.2f})")
    else:
        st.error("❌ Request blocked or failed")
    
    # Main response
    st.markdown("### 📝 Solution:")
    st.markdown(response.content)
    
    # Feedback section
    st.markdown("---")
    st.subheader("📢 Feedback on This Solution")
    
    with st.form(key='feedback_form'):
        rating = st.slider("Rate this solution (1-5 stars)", 1, 5, 3)
        feedback_text = st.text_area("Your feedback (optional)", 
                                   placeholder="Was this helpful? Any corrections needed?")
        correction = st.text_area("Suggested correction (optional)", 
                                 placeholder="If the answer was wrong, what should it be?")
        
        submitted = st.form_submit_button("Submit Feedback")
        
        if submitted:
            feedback = Feedback(
                question=user_question,
                original_response=response.content,
                feedback_rating=rating,
                feedback_text=feedback_text,
                suggested_correction=correction
            )
            st.session_state.feedback_handler.add_feedback(feedback)
            st.success("Thank you for your feedback! It will help improve the system.")
    
    # Gateway information in expandable section
    with st.expander("🛡 AI Gateway Details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Processing Time", f"{response.processing_time:.3f}s")
            st.metric("Confidence Score", f"{response.confidence:.2f}")
        
        with col2:
            st.metric("Guardrails Run", len(response.guardrail_results))
            passed_guardrails = len([r for r in response.guardrail_results if r.passed])
            st.metric("Guardrails Passed", f"{passed_guardrails}/{len(response.guardrail_results)}")
        
        # Detailed guardrail results
        if response.guardrail_results:
            st.subheader("Guardrail Results:")
            for result in response.guardrail_results:
                status_icon = "✅" if result.passed else "❌"
                action_color = {
                    "allow": "green",
                    "block": "red", 
                    "warn": "orange",
                    "modify": "blue"
                }.get(result.action.value, "gray")
                
                st.markdown(f"""
                {status_icon} *Action:* :{action_color}[{result.action.value.upper()}] 
                *Confidence:* {result.confidence:.2f} 
                *Message:* {result.message}
                """)

# Chat history section
if st.session_state.request_history:
    st.markdown("---")
    st.header("📚 Recent Questions")
    
    # Show last 5 questions
    recent_questions = st.session_state.request_history[-5:]
    
    for i, item in enumerate(reversed(recent_questions), 1):
        with st.expander(f"Question {i}: {item['question'][:50]}..."):
            st.markdown(f"*Question:* {item['question']}")
            st.markdown("*Solution:*")
            st.markdown(item['response'].content)
            st.caption(f"Processed at: {time.ctime(item['timestamp'])}")

# Instructions and examples
with st.expander("💡 How to use this Math Tutor"):
    st.markdown("""
    ### ✅ *Good Examples:*
    - Solve x² - 5x + 6 = 0
    - What is the derivative of x² + 3x + 2?
    - How do I factor x² - 9?
    - Calculate the integral of 2x + 1
    - Find the area of a circle with radius 5
    
    ### ❌ *Invalid Examples:*
    - How are you?
    - What's the weather like?
    - Tell me a joke
    - What is Python programming?
    
    ### 🛡 *AI Gateway Features:*
    - *Input Validation:* Ensures only math-related questions are processed
    - *Knowledge Base Search:* Finds relevant solutions from the math database
    - *Web Search Fallback:* Uses MCP and web search when KB doesn't have answers
    - *Output Safety:* Validates responses for educational appropriateness  
    - *Performance Monitoring:* Tracks success rates and processing times
    - *Human Feedback:* Your ratings and corrections help improve the system
    """)

# Footer
st.markdown("---")
st.markdown(
    "🤖 Powered by AI Gateway with integrated guardrails for safe and effective math tutoring"
)

# Debug mode (only show in development)
if st.checkbox("🔧 Debug Mode"):
    st.subheader("Debug Information")
    
    if user_question:
        st.code(f"User Query: {user_question}")
        
    st.code(f"Gateway Metrics: {st.session_state.gateway.get_metrics()}")
    
    if st.session_state.request_history:
        latest_response = st.session_state.request_history[-1]['response']
        st.code(f"Latest Response Object: {latest_response}")
    
    # Show feedback data in debug mode
    st.subheader("Feedback Data")
    all_feedback = st.session_state.feedback_handler.get_all_feedback()
    if all_feedback:
        for fb in all_feedback[-5:]:  # Show last 5 feedback items
            with st.expander(f"Feedback on: {fb.question[:50]}..."):
                st.write(f"Rating: {'⭐' * fb.feedback_rating}")
                if fb.feedback_text:
                    st.write(f"Feedback: {fb.feedback_text}")
                if fb.suggested_correction:
                    st.write(f"Suggested Correction: {fb.suggested_correction}")
    else:
        st.write("No feedback collected yet")