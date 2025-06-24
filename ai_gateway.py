"""
AI Gateway Integration for Math Routing Agent
This implements the AI Gateway pattern with comprehensive guardrails
as described in Portkey AI Gateway architecture.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import time
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GuardrailAction(Enum):
    """Actions that can be taken based on guardrail results"""
    ALLOW = "allow"
    BLOCK = "block"
    MODIFY = "modify"
    WARN = "warn"
    LOG = "log"

@dataclass
class GuardrailResult:
    """Result from a guardrail check"""
    passed: bool
    action: GuardrailAction
    confidence: float
    message: str
    metadata: Dict[str, Any] = None

@dataclass
class GatewayRequest:
    """Request structure for AI Gateway"""
    user_query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: float = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}

@dataclass
class GatewayResponse:
    """Response structure from AI Gateway"""
    content: str
    success: bool
    confidence: float
    processing_time: float
    guardrail_results: List[GuardrailResult]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class MathAgentGateway:
    """
    AI Gateway implementation for Math Routing Agent
    Based on Portkey AI Gateway architecture with integrated guardrails
    """
    
    def __init__(self):
        self.input_guardrails = []
        self.output_guardrails = []
        self.request_log = []
        self.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'successful_requests': 0,
            'average_processing_time': 0.0
        }
        
        # Initialize guardrails
        self._initialize_guardrails()
    
    def _initialize_guardrails(self):
        """Initialize all guardrails for the math agent"""
        
        # Input Guardrails
        try:
            from guardrails.input_guardrail import is_valid_math_input, comprehensive_input_validation
            self.input_guardrails = [
                {
                    'name': 'math_content_validator',
                    'function': is_valid_math_input,
                    'action': GuardrailAction.BLOCK,
                    'priority': 1
                },
                {
                    'name': 'comprehensive_validator',
                    'function': comprehensive_input_validation,
                    'action': GuardrailAction.BLOCK,
                    'priority': 2
                }
            ]
        except ImportError:
            logger.warning("Input guardrail modules not found, using default validation")
            self.input_guardrails = []
        
        # Output Guardrails
        try:
            from guardrails.output_guardrail import validate_output_safety, validate_mathematical_accuracy
            self.output_guardrails = [
                {
                    'name': 'safety_validator',
                    'function': validate_output_safety,
                    'action': GuardrailAction.BLOCK,
                    'priority': 1
                },
                {
                    'name': 'accuracy_validator', 
                    'function': validate_mathematical_accuracy,
                    'action': GuardrailAction.WARN,
                    'priority': 2
                }
            ]
        except ImportError:
            logger.warning("Output guardrail modules not found, using default validation")
            self.output_guardrails = []
    
    def process_request(self, request: GatewayRequest) -> GatewayResponse:
        """
        Main gateway processing function with full guardrail integration
        This follows the AI Gateway pattern: Input Validation -> Processing -> Output Validation
        """
        
        start_time = time.time()
        guardrail_results = []
        
        try:
            # Step 1: Input Guardrails
            logger.info(f"Processing request: {request.user_query[:50]}...")
            
            input_validation = self._run_input_guardrails(request)
            guardrail_results.extend(input_validation)
            
            # Check if any input guardrail blocked the request
            if any(result.action == GuardrailAction.BLOCK for result in input_validation):
                blocked_result = next(result for result in input_validation if result.action == GuardrailAction.BLOCK)
                
                self.metrics['blocked_requests'] += 1
                self.metrics['total_requests'] += 1
                
                return GatewayResponse(
                    content=blocked_result.message,
                    success=False,
                    confidence=0.0,
                    processing_time=time.time() - start_time,
                    guardrail_results=guardrail_results,
                    metadata={'blocked_by': blocked_result.message}
                )
            
            # Step 2: Core Processing (Math Agent)
            logger.info("Input guardrails passed, processing with math agent...")
            
            # Local import to avoid unresolved import error if math_solver.py is missing
            try:
                from agents.math_solver import explain_math_solution
            except ImportError:
                def explain_math_solution(query):
                    return "❌ Math solver module not found. Please ensure math_solver.py exists."
            
            agent_response = explain_math_solution(request.user_query)
            
            # Step 3: Output Guardrails
            output_validation = self._run_output_guardrails(agent_response)
            guardrail_results.extend(output_validation)
            
            # Check if output needs modification or blocking
            final_response = agent_response
            confidence = 0.9
            
            for result in output_validation:
                if result.action == GuardrailAction.BLOCK:
                    final_response = "❌ Response blocked by safety guardrails. Please try rephrasing your question."
                    confidence = 0.0
                    break
                elif result.action == GuardrailAction.MODIFY:
                    # Apply modifications if needed
                    final_response = self._apply_output_modifications(final_response, result)
                elif result.action == GuardrailAction.WARN:
                    confidence = min(confidence, result.confidence)
            
            # Step 4: Apply final output guardrail
            try:
                from guardrails.output_guardrail import simplify_output
                final_response = simplify_output(final_response)
            except ImportError:
                logger.warning("Output simplification module not found, using original response")
            
            # Update metrics
            self.metrics['successful_requests'] += 1
            self.metrics['total_requests'] += 1
            
            processing_time = time.time() - start_time
            self._update_average_processing_time(processing_time)
            
            # Log request
            self._log_request(request, final_response, processing_time, guardrail_results)
            
            logger.info(f"Request processed successfully in {processing_time:.3f}s")
            
            return GatewayResponse(
                content=final_response,
                success=True,
                confidence=confidence,
                processing_time=processing_time,
                guardrail_results=guardrail_results,
                metadata={
                    'agent_used': 'math_solver',
                    'input_guardrails_passed': len([r for r in input_validation if r.passed]),
                    'output_guardrails_passed': len([r for r in output_validation if r.passed]),
                    'total_guardrails_run': len(guardrail_results)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            
            self.metrics['total_requests'] += 1
            processing_time = time.time() - start_time
            
            return GatewayResponse(
                content=f"❌ An error occurred while processing your math question: {str(e)}",
                success=False,
                confidence=0.0,
                processing_time=processing_time,
                guardrail_results=guardrail_results,
                metadata={'error': str(e)}
            )
    
    def _run_input_guardrails(self, request: GatewayRequest) -> List[GuardrailResult]:
        """Run all input guardrails and return results"""
        
        results = []
        
        for guardrail in sorted(self.input_guardrails, key=lambda x: x['priority']):
            try:
                logger.info(f"Running input guardrail: {guardrail['name']}")
                
                if guardrail['name'] == 'comprehensive_validator':
                    # This returns a dict, handle differently
                    validation_result = guardrail['function'](request.user_query)
                    
                    result = GuardrailResult(
                        passed=validation_result['is_valid'],
                        action=GuardrailAction.BLOCK if not validation_result['is_valid'] else GuardrailAction.ALLOW,
                        confidence=validation_result['confidence_score'],
                        message=validation_result['reason'] if not validation_result['is_valid'] else "Input validation passed",
                        metadata=validation_result
                    )
                else:
                    # Boolean return function
                    passed = guardrail['function'](request.user_query)
                    
                    result = GuardrailResult(
                        passed=passed,
                        action=GuardrailAction.BLOCK if not passed else GuardrailAction.ALLOW,
                        confidence=0.9 if passed else 0.1,
                        message="❌ Invalid input: Please ask a mathematics-related question only." if not passed else "Input validation passed",
                        metadata={'guardrail': guardrail['name']}
                    )
                
                results.append(result)
                logger.info(f"Guardrail {guardrail['name']}: {'PASSED' if result.passed else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"Error in input guardrail {guardrail['name']}: {str(e)}")
                results.append(GuardrailResult(
                    passed=False,
                    action=GuardrailAction.BLOCK,
                    confidence=0.0,
                    message=f"Guardrail error: {str(e)}",
                    metadata={'error': str(e), 'guardrail': guardrail['name']}
                ))
        
        return results
    
    def _run_output_guardrails(self, response: str) -> List[GuardrailResult]:
        """Run all output guardrails and return results"""
        
        results = []
        
        for guardrail in sorted(self.output_guardrails, key=lambda x: x['priority']):
            try:
                logger.info(f"Running output guardrail: {guardrail['name']}")
                
                if guardrail['name'] == 'accuracy_validator':
                    # This returns a dict
                    validation_result = guardrail['function'](response)
                    
                    result = GuardrailResult(
                        passed=validation_result['is_mathematically_sound'],
                        action=GuardrailAction.WARN if not validation_result['is_mathematically_sound'] else GuardrailAction.ALLOW,
                        confidence=validation_result['confidence'],
                        message=f"Mathematical accuracy check: {'PASSED' if validation_result['is_mathematically_sound'] else 'WARNINGS'}",
                        metadata=validation_result
                    )
                else:
                    # Boolean return function
                    passed = guardrail['function'](response)
                    
                    result = GuardrailResult(
                        passed=passed,
                        action=GuardrailAction.BLOCK if not passed else GuardrailAction.ALLOW,
                        confidence=0.9 if passed else 0.1,
                        message="Output safety check: PASSED" if passed else "❌ Output failed safety validation",
                        metadata={'guardrail': guardrail['name']}
                    )
                
                results.append(result)
                logger.info(f"Output guardrail {guardrail['name']}: {'PASSED' if result.passed else 'FAILED'}")
                
            except Exception as e:
                logger.error(f"Error in output guardrail {guardrail['name']}: {str(e)}")
                results.append(GuardrailResult(
                    passed=False,
                    action=GuardrailAction.WARN,  # Less strict for output errors
                    confidence=0.5,
                    message=f"Output guardrail error: {str(e)}",
                    metadata={'error': str(e), 'guardrail': guardrail['name']}
                ))
        
        return results
    
    def _apply_output_modifications(self, response: str, guardrail_result: GuardrailResult) -> str:
        """Apply modifications to output based on guardrail results"""
        
        try:
            from guardrails.output_guardrail import simplify_output
            return simplify_output(response)
        except ImportError:
            return response
    
    def _update_average_processing_time(self, processing_time: float):
        """Update the running average of processing times"""
        
        total_requests = self.metrics['total_requests']
        current_avg = self.metrics['average_processing_time']
        
        # Calculate new average
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.metrics['average_processing_time'] = new_avg
    
    def _log_request(self, request: GatewayRequest, response: str, processing_time: float, guardrail_results: List[GuardrailResult]):
        """Log request details for monitoring and debugging"""
        
        log_entry = {
            'timestamp': request.timestamp,
            'user_query': request.user_query,
            'response_length': len(response),
            'processing_time': processing_time,
            'guardrails_passed': len([r for r in guardrail_results if r.passed]),
            'guardrails_failed': len([r for r in guardrail_results if not r.passed]),
            'success': '❌' not in response and 'error' not in response.lower()
        }
        
        self.request_log.append(log_entry)
        
        # Keep only last 100 requests to prevent memory issues
        if len(self.request_log) > 100:
            self.request_log = self.request_log[-100:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway performance metrics"""
        
        return {
            **self.metrics,
            'success_rate': (self.metrics['successful_requests'] / max(self.metrics['total_requests'], 1)) * 100,
            'block_rate': (self.metrics['blocked_requests'] / max(self.metrics['total_requests'], 1)) * 100,
            'recent_requests': len(self.request_log)
        }
    
    def get_recent_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent request logs"""
        
        return self.request_log[-limit:] if self.request_log else []
    
    def reset_metrics(self):
        """Reset all metrics and logs"""
        
        self.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'successful_requests': 0,
            'average_processing_time': 0.0
        }
        self.request_log = []
        logger.info("Gateway metrics and logs reset")

# Usage example and testing functions
def test_gateway():
    """Test function to verify gateway functionality"""
    
    gateway = MathAgentGateway()
    
    test_queries = [
        "Solve x^2 - 5x + 6 = 0",
        "What is the derivative of x^2 + 3x + 2?",
        "How are you?",  # Should be blocked
        "Calculate 2 + 2",
    ]
    
    print("🧪 Testing AI Gateway...")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        
        request = GatewayRequest(user_query=query)
        response = gateway.process_request(request)
        
        print(f"✅ Success: {response.success}")
        print(f"🎯 Confidence: {response.confidence:.2f}")
        print(f"⏱ Time: {response.processing_time:.3f}s")
        print(f"🛡 Guardrails: {len(response.guardrail_results)} run")
        print(f"📝 Response: {response.content[:100]}...")
        print("-" * 30)
    
    print(f"\n📊 Final Metrics:")
    metrics = gateway.get_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_gateway()