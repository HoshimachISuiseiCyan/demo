from fastapi import APIRouter
from pydantic import BaseModel
from app.core.services import get_llm_service

router = APIRouter(prefix="/ai", tags=["AI"])

llm = get_llm_service()


# ========================
# 请求结构
# ========================
class GenerateRequest(BaseModel):
    text: str
    mode: str = "exam"  # exam / expand


# ========================
# 出题接口
# ========================
@router.post("/generate")
def generate_questions(req: GenerateRequest):
    text = req.text
    mode = req.mode

    # 🎯 不同模式 Prompt
    if mode == "exam":
        system_prompt = "你是一个严谨的考试出题专家"
        user_prompt = f"""
根据以下学习内容出5道选择题：

要求：
- 题目必须严格基于原文
- 不允许扩展知识点
- 每题4个选项
- 只有1个正确答案
- 干扰项必须“看起来合理”
- 返回 JSON

格式：
{{
  "questions":[
    {{
      "stem":"题目",
      "options":["A","B","C","D"],
      "answer":"正确选项",
      "explanation":"解析"
    }}
  ]
}}

内容：
{text}
"""
    else:
        system_prompt = "你是一个教学能力很强的AI老师"
        user_prompt = f"""
根据以下内容出5道题，可以适当扩展知识点：

要求：
- 强调理解和应用
- 允许举例、类比
- 干扰项具有迷惑性
- 返回 JSON

格式同上

内容：
{text}
"""

    try:
        result = llm.generate_json(system_prompt, user_prompt)

        questions = result.get("questions", [])

        # 🔥 转成前端需要格式
        formatted = []
        for q in questions:
            formatted.append({
                "id": f"q-{hash(q['stem'])}",
                "source": text[:20],
                "stem": q["stem"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": q.get("explanation", "")
            })

        return {
            "questions": formatted
        }

    except Exception as e:
        print("❌ LLM出错:", e)
        return {
            "questions": [],
            "error": str(e)
        }