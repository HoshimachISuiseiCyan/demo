# Denpa AI Learning System (MVP)

基于 Transformer/LLM 的智能学习系统后端，包含三个核心模块：

1. 知识抽取（Knowledge Extraction）
2. 客观题生成（Question Generation，单选题）
3. 学习评估（Learning Evaluation，自适应掌握度）

## 1. 项目结构

```text
app/
  ai_modules/
    knowledge_extractor.py
    question_generator.py
    evaluator.py
  services/
    embedding_service.py
    llm_service.py
    vector_store.py
  models/
    database.py
    schemas.py
  routes/
    api.py
  utils/
    text_splitter.py
  dependencies.py
  config.py
  main.py
frontend/
  index.html
requirements.txt
.env.example
```

## 2. 快速启动

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

建议在 `.env` 中至少设置：

- `LLM_API_KEY`
- `EMBEDDING_PROVIDER=sentence_transformer`（默认）

启动服务：

```bash
uvicorn app.main:app --reload
```

接口文档：

- `http://127.0.0.1:8000/docs`

前端页面：

- 直接打开 `frontend/index.html`

## 3. API

- `POST /upload`：上传文本并抽取知识点
- `GET /questions?user_id=xxx&limit=5`：获取自适应题目
- `POST /answer`：提交答案并更新掌握度

## 4. 关键设计点

- AI 模块与路由/UI 解耦，可独立替换
- Embedding 服务可切换为 Sentence-BERT、API 或兜底实现
- 向量层默认 FAISS，不可用时降级为内存向量库
- 掌握度更新规则严格按需求：
  - 正确：`mastery += (1 - mastery) * 0.3`
  - 错误：`mastery *= 0.7`

## 5. 后续扩展建议

1. 增加本地 Transformer 推理服务（替换 LLMService）
2. 引入 RAG 检索链路（知识点 + 题目联合召回）
3. 增加更多题型（判断题、多选题）
4. 引入 fine-tuning pipeline（离线数据回流）

