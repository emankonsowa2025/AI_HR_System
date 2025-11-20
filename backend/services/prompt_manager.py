"""Manages chat prompts and conversation flows for skill assessment."""

from typing import Dict, List
import random

class PromptManager:
    def __init__(self):
        self.assessment_prompts = {
            "initial": [
                "Welcome! I can help you explore career opportunities or prepare for interviews. Would you like to:\n1. Analyze your skills for job matching\n2. Practice interview questions\n3. Get advice about a specific role",
                "Hi! I'm here to assist with your career development. What would you like to focus on?\n1. Skill assessment and job matching\n2. Technical interview preparation\n3. Career path advice"
            ],
            "skills_gathering": [
                "What technical skills and technologies are you most experienced with? List them in order of expertise.",
                "Tell me about your main technical skills. Include both programming languages and tools you're comfortable with.",
                "What are your top 3-5 technical skills? Include any frameworks or specialized tools you use."
            ],
            "experience_probe": [
                "For {skill}, could you give me a brief example of how you've used it in a project?",
                "Regarding {skill}, what's the most challenging problem you've solved with it?",
                "How long have you worked with {skill}, and what's your most significant achievement using it?"
            ],
            "role_interest": [
                "What kinds of roles interest you the most? (e.g., backend, frontend, full-stack, data engineering)",
                "Are there specific types of companies or industries you're targeting?",
                "What's your ideal next role? Consider both technical focus and company type."
            ]
        }
        
        self.follow_up_questions = {
            "python": [
                "Have you worked with any Python web frameworks like Django or FastAPI?",
                "What's your experience with Python for data analysis or machine learning?",
                "Have you contributed to any open source Python projects?"
            ],
            "javascript": [
                "Which modern JavaScript frameworks are you most comfortable with?",
                "Have you worked with Node.js on the backend?",
                "What's your experience with modern JavaScript features (ES6+)?"
            ],
            "data": [
                "What databases have you worked with extensively?",
                "Have you built data pipelines or ETL processes?",
                "What's your experience with big data technologies?"
            ]
        }
    
    def get_initial_prompt(self) -> str:
        """Get a random initial greeting and assessment prompt."""
        return random.choice(self.assessment_prompts["initial"])
    
    def get_skills_prompt(self) -> str:
        """Get a random prompt for gathering skills."""
        return random.choice(self.assessment_prompts["skills_gathering"])
    
    def get_experience_prompt(self, skill: str) -> str:
        """Get a random prompt to probe experience with a specific skill."""
        template = random.choice(self.assessment_prompts["experience_probe"])
        return template.format(skill=skill)
    
    def get_follow_up_questions(self, skill: str) -> List[str]:
        """Get relevant follow-up questions based on a skill."""
        # Normalize skill to category
        skill_lower = skill.lower()
        if "python" in skill_lower:
            return self.follow_up_questions["python"]
        elif any(js in skill_lower for js in ["javascript", "js", "node", "react", "angular"]):
            return self.follow_up_questions["javascript"]
        elif any(data in skill_lower for data in ["sql", "database", "etl", "hadoop", "spark"]):
            return self.follow_up_questions["data"]
        return []
    
    def get_role_interest_prompt(self) -> str:
        """Get a random prompt about role interests."""
        return random.choice(self.assessment_prompts["role_interest"])

# Global instance
prompt_manager = PromptManager()