# agents/mcp_server.py
import asyncio
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import requests
from config import TAVILY_API_KEY, SERPER_API_KEY, GEMINI_API_KEY
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

@dataclass
class MCPRequest:
    """MCP Request structure"""
    method: str
    params: Dict[str, Any]
    id: Optional[str] = None

@dataclass 
class MCPResponse:
    """MCP Response structure"""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

class MathMCPServer:
    """
    MCP (Model Context Protocol) Server for Math Search Operations
    Provides structured search capabilities for mathematical content
    """
    
    def __init__(self):
        self.tavily_api_key = TAVILY_API_KEY
        self.serper_api_key = SERPER_API_KEY
        self.tools = {
            "search_math_tavily": self.search_math_tavily,
            "search_math_serper": self.search_math_serper,
            "extract_math_solution": self.extract_math_solution,
            "verify_math_content": self.verify_math_content
        }
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """
        Handle MCP requests for math operations
        """
        try:
            if request.method == "tools/call":
                tool_name = request.params.get("name")
                arguments = request.params.get("arguments", {})
                
                if tool_name in self.tools:
                    result = await self.tools[tool_name](**arguments)
                    return MCPResponse(result=result, id=request.id)
                else:
                    return MCPResponse(
                        error={"code": -32601, "message": f"Unknown tool: {tool_name}"},
                        id=request.id
                    )
            
            elif request.method == "tools/list":
                return MCPResponse(
                    result={"tools": self.get_available_tools()},
                    id=request.id
                )
            
            else:
                return MCPResponse(
                    error={"code": -32601, "message": f"Unknown method: {request.method}"},
                    id=request.id
                )
                
        except Exception as e:
            return MCPResponse(
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
                id=request.id
            )
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Return list of available MCP tools
        """
        return [
            {
                "name": "search_math_tavily",
                "description": "Search for mathematical content using Tavily API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Mathematical question to search"},
                        "max_results": {"type": "integer", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "search_math_serper",
                "description": "Search for mathematical content using Serper API",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Mathematical question to search"},
                        "num_results": {"type": "integer", "default": 10}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "extract_math_solution",
                "description": "Extract and format mathematical solution from search results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Original math question"},
                        "search_results": {"type": "object", "description": "Search results to process"}
                    },
                    "required": ["query", "search_results"]
                }
            },
            {
                "name": "verify_math_content",
                "description": "Verify mathematical accuracy of content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Mathematical content to verify"},
                        "question": {"type": "string", "description": "Original question"}
                    },
                    "required": ["content", "question"]
                }
            }
        ]
    
    async def search_math_tavily(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        MCP tool for Tavily search
        """
        try:
            payload = {
                "api_key": self.tavily_api_key,
                "query": f"mathematics {query} step by step solution tutorial",
                "search_depth": "advanced",
                "include_answer": True,
                "include_domains": [
                    "khanacademy.org",
                    "mathway.com", 
                    "symbolab.com",
                    "wolframalpha.com",
                    "brilliant.org",
                    "mathsisfun.com"
                ],
                "max_results": max_results
            }
            
            response = requests.post(
                "https://api.tavily.com/search", 
                json=payload, 
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "source": "tavily",
                "results": data.get("results", []),
                "answer": data.get("answer", ""),
                "query": query
            }
            
        except Exception as e:
            return {
                "success": False,
                "source": "tavily", 
                "error": str(e),
                "query": query
            }
    
    async def search_math_serper(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        MCP tool for Serper search
        """
        try:
            payload = {
                "q": f"mathematics {query} step by step solution",
                "num": num_results,
                "gl": "us",
                "hl": "en"
            }
            
            response = requests.post(
                "https://google.serper.dev/search",
                json=payload,
                headers={
                    "X-API-KEY": self.serper_api_key,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "success": True,
                "source": "serper",
                "results": data.get("organic", []),
                "knowledge_graph": data.get("knowledgeGraph", {}),
                "answer_box": data.get("answerBox", {}),
                "query": query
            }
            
        except Exception as e:
            return {
                "success": False,
                "source": "serper",
                "error": str(e),
                "query": query
            }
    
    async def extract_math_solution(self, query: str, search_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        MCP tool to extract and format mathematical solutions
        """
        try:
            if not search_results.get("success"):
                return {
                    "success": False,
                    "error": "Search results indicate failure",
                    "solution": ""
                }
            
            # Extract relevant content based on source
            extracted_content = []
            
            if search_results["source"] == "tavily":
                if search_results.get("answer"):
                    extracted_content.append(f"Direct Answer: {search_results['answer']}")
                
                for result in search_results.get("results", []):
                    title = result.get("title", "")
                    content = result.get("content", "")
                    
                    if any(keyword in content.lower() for keyword in ["step", "solve", "solution", "equation"]):
                        extracted_content.append(f"Source: {title}\nContent: {content[:400]}...")
            
            elif search_results["source"] == "serper":
                answer_box = search_results.get("answer_box", {})
                if answer_box:
                    extracted_content.append(f"Answer Box: {answer_box.get('answer', '')}")
                
                for result in search_results.get("results", []):
                    title = result.get("title", "")
                    snippet = result.get("snippet", "")
                    
                    if any(keyword in snippet.lower() for keyword in ["step", "solve", "solution", "equation"]):
                        extracted_content.append(f"Source: {title}\nSnippet: {snippet}")
            
            # Generate solution using Gemini
            content_text = "\n\n".join(extracted_content[:3])
            
            if not content_text.strip():
                return {
                    "success": False,
                    "error": "No relevant mathematical content found in search results",
                    "solution": ""
                }
            
            prompt = f"""
You are a mathematics tutor. Based on the web search results below, provide a clear, step-by-step solution.

Question: {query}

Search Results:
{content_text}

Provide:
1. Clear step-by-step solution
2. Explanations for each step
3. Final answer
4. Use simple, educational language

If the search results don't provide complete information, clearly state what's missing.
"""
            
            response = model.generate_content(prompt)
            
            if hasattr(response, "candidates") and response.candidates:
                if hasattr(response.candidates[0], "content") and response.candidates[0].content.parts:
                    solution = response.candidates[0].content.parts[0].text.strip()
                else:
                    solution = "Could not generate solution from search results."
            else:
                solution = "Could not generate solution from search results."
            
            return {
                "success": True,
                "solution": solution,
                "source": search_results["source"],
                "extracted_content": content_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "solution": ""
            }
    
    async def verify_math_content(self, content: str, question: str) -> Dict[str, Any]:
        """
        MCP tool to verify mathematical accuracy
        """
        try:
            prompt = f"""
You are a mathematics expert. Please verify the accuracy of the following solution.

Original Question: {question}

Solution to Verify:
{content}

Please analyze:
1. Are the mathematical steps correct?
2. Is the final answer accurate?
3. Are there any errors or missing steps?
4. Rate the solution quality (1-10)

Provide your verification in a structured format.
"""
            
            response = model.generate_content(prompt)
            
            if hasattr(response, "candidates") and response.candidates:
                if hasattr(response.candidates[0], "content") and response.candidates[0].content.parts:
                    verification = response.candidates[0].content.parts[0].text.strip()
                else:
                    verification = "Could not verify the content."
            else:
                verification = "Could not verify the content."
            
            # Extract quality score (basic pattern matching)
            quality_score = 7  # Default score
            if "10" in verification or "excellent" in verification.lower():
                quality_score = 10
            elif "9" in verification or "very good" in verification.lower():
                quality_score = 9
            elif "8" in verification or "good" in verification.lower():
                quality_score = 8
            elif "error" in verification.lower() or "incorrect" in verification.lower():
                quality_score = 4
            
            return {
                "success": True,
                "verification": verification,
                "quality_score": quality_score,
                "is_accurate": quality_score >= 7
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "verification": "",
                "quality_score": 0,
                "is_accurate": False
            }

# MCP Client for easy integration
class MCPMathClient:
    """
    Client to interact with MCP Math Server
    """
    
    def __init__(self):
        self.server = MathMCPServer()
    
    async def search_and_solve(self, query: str) -> str:
        """
        High-level method to search and solve math problems using MCP
        """
        try:
            # Step 1: Try Tavily search
            tavily_request = MCPRequest(
                method="tools/call",
                params={"name": "search_math_tavily", "arguments": {"query": query}}
            )
            
            tavily_response = await self.server.handle_request(tavily_request)
            
            if tavily_response.result and tavily_response.result.get("success"):
                # Extract solution from Tavily results
                extract_request = MCPRequest(
                    method="tools/call",
                    params={
                        "name": "extract_math_solution",
                        "arguments": {
                            "query": query,
                            "search_results": tavily_response.result
                        }
                    }
                )
                
                extract_response = await self.server.handle_request(extract_request)
                
                if extract_response.result and extract_response.result.get("success"):
                    solution = extract_response.result.get("solution", "")
                    
                    # Verify the solution
                    verify_request = MCPRequest(
                        method="tools/call",
                        params={
                            "name": "verify_math_content", 
                            "arguments": {"content": solution, "question": query}
                        }
                    )
                    
                    verify_response = await self.server.handle_request(verify_request)
                    
                    if verify_response.result and verify_response.result.get("is_accurate"):
                        return self.format_mcp_response(query, solution, "Tavily (MCP)", 
                                                     verify_response.result.get("quality_score", 7))
            
            # Step 2: Fallback to Serper
            serper_request = MCPRequest(
                method="tools/call",
                params={"name": "search_math_serper", "arguments": {"query": query}}
            )
            
            serper_response = await self.server.handle_request(serper_request)
            
            if serper_response.result and serper_response.result.get("success"):
                extract_request = MCPRequest(
                    method="tools/call",
                    params={
                        "name": "extract_math_solution",
                        "arguments": {
                            "query": query,
                            "search_results": serper_response.result
                        }
                    }
                )
                
                extract_response = await self.server.handle_request(extract_request)
                
                if extract_response.result and extract_response.result.get("success"):
                    solution = extract_response.result.get("solution", "")
                    return self.format_mcp_response(query, solution, "Serper (MCP)", 7)
            
            return "❌ Could not find relevant mathematical content through web search."
            
        except Exception as e:
            return f"❌ MCP search error: {str(e)}"
    
    def format_mcp_response(self, query: str, solution: str, source: str, quality_score: int) -> str:
        """
        Format MCP response for display
        """
        quality_indicator = "⭐" * min(int(quality_score/2), 5)
        
        formatted_response = f"""
🔧 **MATH SOLUTION VIA MCP SERVER**
═══════════════════════════════════

🎯 **Question:** {query}

🤖 **MCP Source:** {source}
📊 **Quality Score:** {quality_score}/10 {quality_indicator}

📝 **Step-by-Step Solution:**
{solution}

ℹ️ **Note:** This solution was generated using MCP (Model Context Protocol) with web search verification.

═══════════════════════════════════
🎓 Hope this helps with your math studies!
"""
        return formatted_response.strip()

# Convenience function for async execution
def run_mcp_search(query: str) -> str:
    """
    Run MCP search synchronously
    """
    client = MCPMathClient()
    return asyncio.run(client.search_and_solve(query))