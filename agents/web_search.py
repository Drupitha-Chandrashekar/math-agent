# agents/web_search.py
import requests
import json
import time
from typing import Dict, List, Optional, Any
from config import TAVILY_API_KEY, SERPER_API_KEY, GEMINI_API_KEY
import google.generativeai as genai
from guardrails.input_guardrail import is_valid_math_input
from guardrails.output_guardrail import simplify_output, format_error_message

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

class WebSearchAgent:
    """
    Web Search Agent that uses both Tavily and Serper APIs
    for math-related queries when knowledge base doesn't have answers
    """
    
    def __init__(self):
        self.tavily_api_key = TAVILY_API_KEY
        self.serper_api_key = SERPER_API_KEY
        self.tavily_url = "https://api.tavily.com/search"
        self.serper_url = "https://google.serper.dev/search"
        
    def search_with_tavily(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search using Tavily API - specialized for research
        """
        try:
            payload = {
                "api_key": self.tavily_api_key,
                "query": f"mathematics {query} step by step solution",
                "search_depth": "advanced",
                "include_answer": True,
                "include_domains": [
                    "khanacademy.org",
                    "mathway.com", 
                    "symbolab.com",
                    "wolframalpha.com",
                    "brilliant.org",
                    "mathsisfun.com",
                    "stackoverflow.com"
                ],
                "max_results": max_results
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.tavily_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Tavily search completed - Found {len(data.get('results', []))} results")
            
            return {
                "success": True,
                "results": data.get("results", []),
                "answer": data.get("answer", ""),
                "source": "tavily"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Tavily search failed: {e}")
            return {"success": False, "error": str(e), "source": "tavily"}
        except Exception as e:
            print(f"❌ Tavily search error: {e}")
            return {"success": False, "error": str(e), "source": "tavily"}
    
    def search_with_serper(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        Search using Serper API - Google search results
        """
        try:
            payload = {
                "q": f"mathematics {query} step by step solution tutorial",
                "num": num_results,
                "gl": "us",
                "hl": "en"
            }
            
            headers = {
                "X-API-KEY": self.serper_api_key,
                "Content-Type": "application/json"
            }
            
            response = requests.post(self.serper_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"✅ Serper search completed - Found {len(data.get('organic', []))} results")
            
            return {
                "success": True,
                "results": data.get("organic", []),
                "knowledge_graph": data.get("knowledgeGraph", {}),
                "answer_box": data.get("answerBox", {}),
                "source": "serper"
            }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Serper search failed: {e}")
            return {"success": False, "error": str(e), "source": "serper"}
        except Exception as e:
            print(f"❌ Serper search error: {e}")
            return {"success": False, "error": str(e), "source": "serper"}
    
    def extract_math_content(self, search_results: Dict[str, Any]) -> str:
        """
        Extract mathematical content from search results
        """
        extracted_content = []
        
        if search_results["source"] == "tavily":
            # Extract from Tavily results
            if search_results.get("answer"):
                extracted_content.append(f"Direct Answer: {search_results['answer']}")
            
            for result in search_results.get("results", []):
                title = result.get("title", "")
                content = result.get("content", "")
                url = result.get("url", "")
                
                if any(keyword in content.lower() for keyword in ["step", "solve", "solution", "equation", "formula"]):
                    extracted_content.append(f"Source: {title}\nContent: {content[:300]}...\nURL: {url}")
        
        elif search_results["source"] == "serper":
            # Extract from Serper results
            answer_box = search_results.get("answer_box", {})
            if answer_box:
                extracted_content.append(f"Answer Box: {answer_box.get('answer', '')}")
            
            knowledge_graph = search_results.get("knowledge_graph", {})
            if knowledge_graph:
                extracted_content.append(f"Knowledge Graph: {knowledge_graph.get('description', '')}")
            
            for result in search_results.get("results", []):
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                link = result.get("link", "")
                
                if any(keyword in snippet.lower() for keyword in ["step", "solve", "solution", "equation", "formula"]):
                    extracted_content.append(f"Source: {title}\nSnippet: {snippet}\nURL: {link}")
        
        return "\n\n".join(extracted_content[:3])  # Limit to top 3 most relevant
    
    def generate_solution_from_search(self, query: str, search_content: str) -> str:
        """
        Generate step-by-step solution using search results and Gemini
        """
        prompt = f"""
You are a helpful math tutor. Based on the web search results below, provide a clear, step-by-step solution to the following math question.

Question: {query}

Web Search Results:
{search_content}

Please provide:
1. A clear step-by-step solution
2. Explanations for each step
3. The final answer
4. Use simple language suitable for students

Format your response with clear steps, mathematical notation, and educational explanations.
If the search results don't contain enough information to solve the problem completely, clearly state what information is missing.
"""
        
        try:
            response = model.generate_content(prompt)
            
            if hasattr(response, "candidates") and response.candidates:
                if hasattr(response.candidates[0], "content") and response.candidates[0].content.parts:
                    solution = response.candidates[0].content.parts[0].text.strip()
                else:
                    solution = "⚠️ Could not generate solution from search results."
            elif hasattr(response, "text"):
                solution = response.text.strip()
            else:
                solution = "⚠️ Could not generate solution from search results."
            
            return solution
            
        except Exception as e:
            print(f"❌ Error generating solution: {e}")
            return f"❌ Could not generate solution due to error: {e}"
    
    def search_and_solve(self, query: str) -> str:
        """
        Main method to search web and generate math solution
        """
        print(f"🔍 Starting web search for: {query}")
        
        # Step 1: Validate input
        if not is_valid_math_input(query):
            return "❌ Invalid input: Please ask a mathematics-related question only."
        
        # Step 2: Try Tavily first (better for academic content)
        tavily_results = self.search_with_tavily(query)
        
        if tavily_results["success"] and tavily_results["results"]:
            print("✅ Using Tavily search results")
            search_content = self.extract_math_content(tavily_results)
            
            if search_content.strip():
                solution = self.generate_solution_from_search(query, search_content)
                formatted_solution = self.format_web_search_response(query, solution, "Tavily")
                return simplify_output(formatted_solution)
        
        # Step 3: Fallback to Serper if Tavily fails
        print("🔄 Falling back to Serper search...")
        serper_results = self.search_with_serper(query)
        
        if serper_results["success"] and serper_results["results"]:
            print("✅ Using Serper search results")
            search_content = self.extract_math_content(serper_results)
            
            if search_content.strip():
                solution = self.generate_solution_from_search(query, search_content)
                formatted_solution = self.format_web_search_response(query, solution, "Serper")
                return simplify_output(formatted_solution)
        
        # Step 4: No useful results found
        return format_error_message("no_web_results", query)
    
    def format_web_search_response(self, query: str, solution: str, source: str) -> str:
        """
        Format the web search response in a student-friendly way
        """
        formatted_response = f"""
🌐 **MATH SOLUTION FROM WEB SEARCH**
═══════════════════════════════════

🎯 **Question:** {query}

📡 **Search Source:** {source} (Web Search)

📝 **Step-by-Step Solution:**
{solution}

ℹ️ **Note:** This solution was generated from web search results. Please verify the steps and calculations.

═══════════════════════════════════
🎓 Hope this helps with your math studies!
"""
        return formatted_response.strip()

# Utility function for easy integration
def perform_web_search(query: str) -> str:
    """
    Convenience function to perform web search
    """
    web_agent = WebSearchAgent()
    return web_agent.search_and_solve(query)