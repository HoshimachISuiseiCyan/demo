# app/services/recommender.py

def recommend(questions, attempts):
    # 优先错题
    for q in questions:
        for a in attempts:
            if a.question_id == q.id and not a.is_correct:
                return q

    # 未做题
    for q in questions:
        if not any(a.question_id == q.id for a in attempts):
            return q

    # 随机
    return questions[0] if questions else None