from config import GEMINI_API_KEY
import google.generativeai as genai
import re

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

def is_valid_math_input(text: str) -> bool:
    """
    Enhanced input guardrail that validates if input is math-related.
    This acts as the first layer of AI Gateway input validation.
    """
    
    # Step 1: Basic text validation
    if not text or len(text.strip()) < 2:
        print("❌ Input guardrail: Text too short or empty")
        return False
    
    # Step 2: Check for obvious non-math patterns
    non_math_patterns = [
        r'^(hi|hello|hey|how are you|what\'s up|good morning|good afternoon)',
        r'(weather|news|sports|politics|food|music|movie)',
        r'^(thank you|thanks|bye|goodbye|see you)',
        r'(tell me a joke|story|poem)',
    ]
    
    text_lower = text.lower().strip()
    
    for pattern in non_math_patterns:
        if re.search(pattern, text_lower):
            print(f"❌ Input guardrail: Detected non-math pattern: {pattern}")
            return False
    
    # Step 3: Check for math-related keywords (positive indicators)
    math_keywords = [
        'solve', 'equation', 'derivative', 'integral', 'limit', 'function',
        'calculate', 'find', 'simplify', 'expand', 'factor', 'graph',
        'algebra', 'calculus', 'geometry', 'trigonometry', 'statistics',
        'polynomial', 'logarithm', 'exponential', 'matrix', 'vector',
        'theorem', 'proof', 'formula', 'inequality', 'system'
    ]
    
    # Check for mathematical symbols
    math_symbols = ['+', '-', '*', '/', '=', '^', '√', '∫', '∂', 'x', 'y', 'z']
    
    has_math_keyword = any(keyword in text_lower for keyword in math_keywords)
    has_math_symbol = any(symbol in text for symbol in math_symbols)
    
    # If we found clear math indicators, it's likely valid
    if has_math_keyword or has_math_symbol:
        print("✅ Input guardrail: Math keywords/symbols detected")
        return True
    
    # Step 4: Use Gemini as final validator for edge cases
    prompt = f"""
You are a strict math question classifier for an educational system.

Analyze this input and determine if it's a mathematics-related question or request.

Input: "{text}"

Consider it valid ONLY if it's asking about:
- Solving equations or mathematical problems
- Mathematical concepts, theories, or explanations
- Calculations, derivatives, integrals, etc.
- Geometry, algebra, calculus, statistics, etc.
- Mathematical proofs or formulas

Consider it INVALID if it's:
- General conversation (greetings, how are you, etc.)
- Non-math subjects (weather, news, sports, etc.)
- Personal questions or casual chat
- Requests for stories, jokes, or non-educational content

Respond with exactly 'VALID' or 'INVALID' - nothing else."""

    try:
        response = model.generate_content(prompt)
        answer = response.text.strip().upper()
        print(f"🤖 Input guardrail Gemini response: {answer}")
        
        # Extract the decision
        is_valid = "VALID" in answer and "INVALID" not in answer
        
        if is_valid:
            print("✅ Input guardrail: Gemini classified as valid math question")
        else:
            print("❌ Input guardrail: Gemini classified as invalid/non-math")
            
        return is_valid
        
    except Exception as e:
        print(f"⚠️ Input guardrail error with Gemini: {e}")
        # Fallback: if Gemini fails, be permissive for math-like content
        return has_math_keyword or has_math_symbol

def validate_math_content_safety(text: str) -> bool:
    """
    Additional safety guardrail to ensure math content is appropriate.
    This is part of the AI Gateway safety layer.
    """
    
    # Check for inappropriate content that might be disguised as math
    inappropriate_patterns = [
        r'(hack|cheat|exploit|bypass)',
        r'(illegal|fraud|scam)',
        r'(violent|harmful|dangerous)',
        r'(explicit|inappropriate|adult)'
    ]
    
    text_lower = text.lower()
    
    for pattern in inappropriate_patterns:
        if re.search(pattern, text_lower):
            print(f"⚠️ Safety guardrail: Detected inappropriate pattern: {pattern}")
            return False
    
    return True

def comprehensive_input_validation(text: str) -> dict:
    """
    Comprehensive input validation that returns detailed results.
    This provides full AI Gateway input guardrail functionality.
    """
    
    validation_result = {
        'is_valid': False,
        'is_math_related': False,
        'is_safe': False,
        'confidence_score': 0.0,
        'reason': ''
    }
    
    # Check safety first
    validation_result['is_safe'] = validate_math_content_safety(text)
    if not validation_result['is_safe']:
        validation_result['reason'] = 'Content failed safety validation'
        return validation_result
    
    # Check if math-related
    validation_result['is_math_related'] = is_valid_math_input(text)
    if not validation_result['is_math_related']:
        validation_result['reason'] = 'Input is not mathematics-related'
        return validation_result
    
    # If we reach here, input is valid
    validation_result['is_valid'] = True
    validation_result['confidence_score'] = 0.95  # High confidence for passed validation
    validation_result['reason'] = 'Input passed all validation checks'
    
    return validation_result