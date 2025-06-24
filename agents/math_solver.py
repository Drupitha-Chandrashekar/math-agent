from config import GEMINI_API_KEY, QDRANT_COLLECTION_NAME
from guardrails.input_guardrail import is_valid_math_input
from guardrails.output_guardrail import simplify_output
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from agents.mcp_server import run_mcp_search
from agents.web_search import perform_web_search
from feedback_handler import FeedbackHandler  # Import the feedback handler

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Load sentence transformer model for embeddings
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Qdrant client
retriever = QdrantClient("localhost", port=6333)

# Initialize feedback handler
feedback_handler = FeedbackHandler()

def explain_math_solution(user_query: str):
    """
    Main function that integrates knowledge base, MCP, and web search with fallback logic.
    Now incorporates feedback from previous similar questions.
    """
    
    # Step 1: Input Guardrail - Validate if input is math-related
    print("🔍 Checking input guardrail...")
    if not is_valid_math_input(user_query):
        return "❌ Invalid input: Please ask a mathematics-related question only."
    
    print("✅ Input guardrail passed - Valid math question detected")
    
    # Step 1.5: Check for similar feedback
    similar_feedback = feedback_handler.get_feedback_for_question(user_query)
    feedback_context = ""
    
    if similar_feedback:
        print(f"ℹ️ Found {len(similar_feedback)} similar feedback items")
        # Create context from feedback
        feedback_context = "\n".join(
            f"Previous feedback on similar question '{fb.question}':\n"
            f"Rating: {fb.feedback_rating}/5\n"
            f"Feedback: {fb.feedback_text or 'No additional comments'}\n"
            f"Suggested correction: {fb.suggested_correction or 'None'}\n"
            for fb in similar_feedback[:3]  # Limit to top 3 most relevant
        )
    
    # Step 2: Generate embedding for semantic search
    try:
        query_vector = embedding_model.encode(user_query).tolist()
        print("✅ Query vector generated successfully")
    except Exception as e:
        return f"❌ Error generating embedding: {e}"
    
    # Step 3: Perform semantic search in knowledge base
    try:
        results = retriever.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=1
        )
        print(f"✅ Knowledge base search completed - Found {len(results)} results")
    except Exception as e:
        return f"❌ Failed to search knowledge base: {e}"
    
    # Step 4: Check if relevant results found in knowledge base
    if results and len(results) > 0 and results[0].score >= 0.6:  # Threshold for relevance
        print("📚 Found in knowledge base - generating explanation")
        payload = results[0].payload
        question = payload.get("question", "")
        answer = payload.get("answer", "")
        steps = payload.get("steps", "")
        
        # Generate step-by-step explanation using Gemini
        prompt = f"""You are a helpful math tutor explaining to a student. 
        
Please provide a clear, step-by-step explanation for this math problem:

Question: {question}
User's Query: {user_query}
Known Answer: {answer}
Additional Steps: {steps}

{feedback_context if feedback_context else ''}

Please format your response as follows:
1. Start with "Let me solve this step by step:"
2. Break down the solution into numbered steps
3. Use simple language appropriate for students
4. Show all calculations clearly
5. End with a clear final answer
6. If there was previous feedback, incorporate those suggestions

Make sure each step is easy to understand and follow."""
        
        try:
            response = model.generate_content(prompt)
            
            # Extract explanation safely
            if hasattr(response, "candidates") and response.candidates:
                if hasattr(response.candidates[0], "content") and response.candidates[0].content.parts:
                    explanation = response.candidates[0].content.parts[0].text.strip()
                else:
                    explanation = "⚠ Could not generate explanation - no content parts found."
            elif hasattr(response, "text"):
                explanation = response.text.strip()
            else:
                explanation = "⚠ Could not generate explanation - unexpected response format."
                
            print("✅ Explanation generated successfully")
            
            final_response = format_student_response(
                question, 
                answer, 
                explanation, 
                results[0].score,
                source="Knowledge Base"
            )
            return simplify_output(final_response)
            
        except Exception as e:
            print(f"❌ Error generating explanation: {e}")
            # Fall through to MCP/web search if KB explanation fails
    
    # Step 5: If not in knowledge base, try MCP server first
    print("🔍 Not found in KB, trying MCP server...")
    mcp_response = run_mcp_search(user_query)
    
    if "❌" not in mcp_response and "error" not in mcp_response.lower():
        print("✅ Found solution via MCP")
        return mcp_response
    
    # Step 6: If MCP fails, fall back to direct web search
    print("🔍 MCP failed, falling back to web search...")
    web_response = perform_web_search(user_query)
    
    if "❌" not in web_response and "error" not in web_response.lower():
        print("✅ Found solution via web search")
        return web_response
    
    # Step 7: Final fallback if all methods fail
    return "❌ Could not find a solution to this math problem. Please try rephrasing or ask a different question."

def format_student_response(question: str, answer: str, explanation: str, match_score: float, source: str) -> str:
    """
    Format the response in a student-friendly way with clear structure.
    """
    formatted_response = f"""
📚 *MATH PROBLEM SOLUTION* | Source: {source}
═══════════════════════════

🎯 *Question:* {question}

✅ *Final Answer:* {answer}

📝 *Step-by-Step Explanation:*
{explanation}

💡 *Confidence Score:* {match_score:.2f} (Higher is better)

═══════════════════════════
🎓 Hope this helps with your math studies!
"""
    return formatted_response.strip()

# Debug function remains the same
def debug_knowledge_base_search(user_query: str):
    """Debug function to check knowledge base search results"""
    try:
        query_vector = embedding_model.encode(user_query).tolist()
        results = retriever.search(
            collection_name=QDRANT_COLLECTION_NAME,
            query_vector=query_vector,
            limit=3
        )
        
        print(f"\n🔍 DEBUG: Knowledge Base Search Results for '{user_query}'")
        print("=" * 60)
        
        if not results:
            print("❌ No results found")
            return
            
        for i, result in enumerate(results, 1):
            print(f"\nResult {i}:")
            print(f"  Score: {result.score:.4f}")
            print(f"  Question: {result.payload.get('question', 'N/A')}")
            print(f"  Answer: {result.payload.get('answer', 'N/A')}")
            print(f"  Steps: {result.payload.get('steps', 'N/A')[:100]}...")
            
    except Exception as e:
        print(f"❌ Debug search failed: {e}")