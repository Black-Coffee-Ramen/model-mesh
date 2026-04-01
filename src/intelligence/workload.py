import re
from typing import List, Dict, Any

class WorkloadClassifier:
    def __init__(self):
        # Category keywords
        self.categories = {
            "coding": ["code", "python", "javascript", "script", "function", "bug", "debug", "api"],
            "reasoning": ["analyze", "evaluate", "logically", "think", "step-by-step", "complex", "strategy"],
            "extraction": ["extract", "json", "entities", "format", "structured", "parse"],
            "long-form": ["write", "article", "essay", "story", "comprehensive", "draft"],
            "simple": ["hello", "how are you", "who are you", "tell me a joke"]
        }

    def classify(self, messages: List[Dict[str, str]]) -> str:
        """Classify a set of messages into a workload category."""
        content = " ".join([m.get("content", "").lower() for m in messages])
        
        # Simple scoring based on keywords
        scores = {cat: 0 for cat in self.categories}
        for cat, keywords in self.categories.items():
            for kw in keywords:
                if kw in content:
                    scores[cat] += 1
        
        # Heuristic: longest message check
        total_len = len(content)
        if total_len > 4000:
            scores["long-form"] += 2
        
        # Pick category with highest score
        best_cat = max(scores, key=scores.get)
        if scores[best_cat] == 0:
            return "general"
        return best_cat

workload_classifier = WorkloadClassifier()
