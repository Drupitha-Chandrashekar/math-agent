"""
Feedback handling system for the Math AI Agent
Stores and processes human feedback to improve responses
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import json
import os
from datetime import datetime
import hashlib

@dataclass
class Feedback:
    """Structure for storing feedback data"""
    question: str
    original_response: str
    feedback_rating: int  # 1-5 scale
    feedback_text: Optional[str] = None
    suggested_correction: Optional[str] = None
    timestamp: float = None
    feedback_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()
        if self.feedback_id is None:
            self.feedback_id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Generate a unique ID for this feedback"""
        hash_input = f"{self.question}{self.timestamp}{self.feedback_rating}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        """Convert feedback to dictionary for storage"""
        return {
            'question': self.question,
            'original_response': self.original_response,
            'feedback_rating': self.feedback_rating,
            'feedback_text': self.feedback_text,
            'suggested_correction': self.suggested_correction,
            'timestamp': self.timestamp,
            'feedback_id': self.feedback_id
        }

class FeedbackHandler:
    """Handles storage and processing of human feedback"""
    
    def __init__(self, storage_file: str = "feedback_data.json"):
        self.storage_file = storage_file
        self.feedback_data = []
        self._load_feedback()
    
    def _load_feedback(self):
        """Load feedback data from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_data = [Feedback(**item) for item in data]
            except Exception as e:
                print(f"Error loading feedback data: {e}")
                self.feedback_data = []
    
    def _save_feedback(self):
        """Save feedback data to storage file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump([fb.to_dict() for fb in self.feedback_data], f, indent=2)
        except Exception as e:
            print(f"Error saving feedback data: {e}")
    
    def add_feedback(self, feedback: Feedback):
        """Add new feedback to the system"""
        self.feedback_data.append(feedback)
        self._save_feedback()
    
    def get_feedback_for_question(self, question: str, threshold: float = 0.7) -> List[Feedback]:
        """
        Get feedback for similar questions using simple similarity threshold
        In production, you'd want to use embeddings for semantic similarity
        """
        # Simple implementation - in production use embeddings/semantic search
        return [
            fb for fb in self.feedback_data 
            if self._simple_similarity(fb.question, question) >= threshold
        ]
    
    def _simple_similarity(self, str1: str, str2: str) -> float:
        """Basic string similarity (replace with proper NLP similarity in production)"""
        set1 = set(str1.lower().split())
        set2 = set(str2.lower().split())
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        return len(intersection) / len(union) if union else 0
    
    def get_all_feedback(self) -> List[Feedback]:
        """Get all feedback data"""
        return self.feedback_data
    
    def get_average_rating(self) -> float:
        """Calculate average feedback rating"""
        if not self.feedback_data:
            return 0.0
        return sum(fb.feedback_rating for fb in self.feedback_data) / len(self.feedback_data)
    
    def get_feedback_stats(self) -> Dict:
        """Get statistics about feedback"""
        return {
            'total_feedback': len(self.feedback_data),
            'average_rating': self.get_average_rating(),
            'positive_feedback': len([fb for fb in self.feedback_data if fb.feedback_rating >= 4]),
            'negative_feedback': len([fb for fb in self.feedback_data if fb.feedback_rating <= 2])
        }

# Example usage
if __name__ == "__main__":
    handler = FeedbackHandler()
    
    # Add sample feedback
    sample_fb = Feedback(
        question="Solve x^2 - 5x + 6 = 0",
        original_response="The solution is x=2 and x=3",
        feedback_rating=5,
        feedback_text="Great explanation!"
    )
    handler.add_feedback(sample_fb)
    
    print(f"Average rating: {handler.get_average_rating()}")