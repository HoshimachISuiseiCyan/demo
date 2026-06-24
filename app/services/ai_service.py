# app/services/ai_service.py

import json

class AIService:
    def generate_questions(self, text: str):
        # 👉 这里可以换成本地模型 or API
        lines = text.split("\n")
        questions = []

        for i, line in enumerate(lines[:5]):
            questions.append({
                "question": f"{line} 的正确理解是？",
                "options": [
                    "A. 正确理解",
                    "B. 错误1",
                    "C. 错误2",
                    "D. 错误3"
                ],
                "answer": "A",
                "knowledge": line
            })

        return questions