import re
from typing import Dict, Any

def simplify_output(output: str) -> str:
    """
    Enhanced output guardrail that cleans, validates, and formats the response.
    This acts as the AI Gateway output validation layer.
    """
    
    if not output or len(output.strip()) == 0:
        return "❌ Sorry, I couldn't generate a proper explanation for this math question."
    
    # Step 1: Clean the output
    cleaned_output = clean_response_text(output)
    
    # Step 2: Validate content safety
    if not validate_output_safety(cleaned_output):
        return "❌ Response failed safety validation. Please try asking your question differently."
    
    # Step 3: Ensure educational appropriateness
    educational_output = ensure_educational_format(cleaned_output)
    
    # Step 4: Add student-friendly formatting
    final_output = add_student_formatting(educational_output)
    
    return final_output

def clean_response_text(text: str) -> str:
    """Clean and standardize the response text."""
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Remove triple line breaks
    text = re.sub(r'[ \t]+', ' ', text)  # Standardize spaces
    text = text.strip()
    
    # Fix common formatting issues
    text = re.sub(r'(\d)\s*\.\s*(\w)', r'\1. \2', text)  # Fix numbered list spacing
    text = re.sub(r'([a-z])\s*:\s*([A-Z])', r'\1: \2', text)  # Fix colon spacing
    
    # Remove debug information that shouldn't be shown to students
    debug_patterns = [
        r'DEBUG:.*?\n',
        r'Retrieved Answer:.*?\n',
        r'Match score:.*?\n',
        r'Explanation:\s*\n'
    ]
    
    for pattern in debug_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()

def validate_output_safety(text: str) -> bool:
    """
    Validate that the output is safe and appropriate for educational use.
    Part of AI Gateway output safety guardrails.
    """
    
    # Check for inappropriate content
    inappropriate_patterns = [
        r'(hack|cheat|plagiarize)',
        r'(inappropriate|explicit|adult)',
        r'(illegal|fraud|scam)',
        r'(violent|harmful|dangerous)'
    ]
    
    text_lower = text.lower()
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, text_lower):
            print(f"⚠️ Output safety guardrail: Detected inappropriate content: {pattern}")
            return False
    
    return True

def ensure_educational_format(text: str) -> str:
    """
    Ensure the output follows educational best practices.
    Part of AI Gateway content quality guardrails.
    """
    
    # Add structure if missing
    if not re.search(r'(step|Step|STEP)', text):
        if '1.' in text or '2.' in text:
            # Already has numbered format
            pass
        else:
            # Add basic structure
            text = f"Let me solve this step by step:\n\n{text}"
    
    # Ensure clear final answer section
    if not re.search(r'(final answer|Final Answer|answer is|Answer:)', text, re.IGNORECASE):
        # Try to identify answer from common patterns
        answer_patterns = [
            r'([a-z]\s*=\s*[^,\n]+)',
            r'(x\s*=\s*[^,\n]+)',
            r'(y\s*=\s*[^,\n]+)',
            r'(therefore[^.]*\.)',
            r'(the result is[^.]*\.)'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                answer = match.group(1).strip()
                if not text.endswith('\n'):
                    text += '\n'
                text += f"\n🎯 **Final Answer:** {answer}"
                break
    
    return text

def add_student_formatting(text: str) -> str:
    """
    Add student-friendly formatting and visual elements.
    This makes the math explanations more engaging and readable.
    """
    
    # Add emoji indicators for better visual structure
    text = re.sub(r'^(Step \d+)', r'📝 \1', text, flags=re.MULTILINE)
    text = re.sub(r'^(\d+\.)', r'📝 \1', text, flags=re.MULTILINE)
    
    # Highlight mathematical expressions
    text = re.sub(r'([a-z]\s*=\s*[^,\n\s]+)', r'**\1**', text)
    
    # Add section dividers for long explanations
    if len(text) > 500:
        if '**Final Answer:**' not in text and '🎯' not in text:
            # Try to identify the final answer and highlight it
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['therefore', 'so the answer', 'final answer', 'result is']):
                    lines[i] = f"🎯 {line}"
                    break
            text = '\n'.join(lines)
    
    # Ensure proper spacing
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def validate_mathematical_accuracy(response: str, expected_answer: str = None) -> Dict[str, Any]:
    """
    Advanced guardrail to validate mathematical accuracy.
    This would integrate with symbolic math libraries in production.
    """
    
    validation_result = {
        'is_mathematically_sound': True,
        'confidence': 0.8,
        'warnings': [],
        'suggestions': []
    }
    
    # Basic checks for mathematical notation
    if re.search(r'[a-z]\s*=\s*[a-z]', response):
        # Contains variable assignments - good sign
        validation_result['confidence'] += 0.1
    
    # Check for step-by-step structure
    if re.search(r'(step|Step|\d+\.)', response):
        validation_result['confidence'] += 0.1
        validation_result['suggestions'].append("Good step-by-step structure detected")
    else:
        validation_result['warnings'].append("Consider adding more step-by-step explanation")
    
    # Check for mathematical symbols and expressions
    math_symbols = ['=', '+', '-', '*', '/', '^', '√', '²', '³']
    symbol_count = sum(1 for symbol in math_symbols if symbol in response)
    
    if symbol_count == 0:
        validation_result['warnings'].append("No mathematical symbols detected - may need more detailed calculations")
        validation_result['confidence'] -= 0.2
    
    return validation_result

def format_error_message(error_type: str, user_query: str = "") -> str:
    """
    Format error messages in a student-friendly way.
    Part of the AI Gateway error handling system.
    """
    
    error_messages = {
        'no_match': """
🔍 **Question Not Found**

I couldn't find this specific question in my math knowledge base. 

💡 **Try asking about:**
- Solving equations (like x² + 5x + 6 = 0)
- Derivatives and integrals
- Algebraic expressions
- Geometry problems
- Basic arithmetic operations

📚 **Example questions I can help with:**
- "What is the derivative of x² + 3x?"
- "Solve the equation 2x + 5 = 11"
- "How do I factor x² - 9?"
""",
        
        'invalid_input': """
❌ **Invalid Question**

Please ask a mathematics-related question only.

✅ **Valid examples:**
- Solve x + 5 = 10
- What is the derivative of x²?
- How do I calculate the area of a circle?
- Factor x² - 4x + 3

❌ **Not valid:**
- General conversation
- Non-math subjects
- Personal questions
""",
        
        'low_confidence': """
🤔 **Similar Question Found (Low Confidence)**

I found a somewhat related question, but I'm not confident it matches what you're asking.

💭 **Suggestion:** Try rephrasing your question or asking about a more specific math topic.

📚 **My knowledge base covers:**
- Algebra and equations
- Calculus (derivatives, integrals)
- Geometry and trigonometry
- Basic arithmetic operations
"""
    }
    
    return error_messages.get(error_type, "❌ An unexpected error occurred. Please try again.")