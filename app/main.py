from dotenv import load_dotenv
load_dotenv()  # 👈 必须放在最最最上面

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import api_router
from app.db import init_db


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import api_router
from app.db import init_db



# ========================
# 创建应用
# ========================
app = FastAPI(
    title="Denpa AI Learning System",
    description="自动知识抽取 + 出题 + 自适应学习系统",
    version="1.0.0",
)

# ========================
# CORS
# ========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================
# 启动初始化
# ========================
@app.on_event("startup")
def on_startup():
    print("🚀 正在初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成")

    # 👇 新增：验证AI配置
    import os
    print("🤖 当前LLM配置：")
    print("MODEL:", os.getenv("LLM_MODEL"))
    print("BASE_URL:", os.getenv("LLM_BASE_URL"))
    print("API_KEY:", "已设置" if os.getenv("LLM_API_KEY") else "❌未设置")


# ========================
# 根路径
# ========================
@app.get("/")
def root():
    return {
        "message": "Denpa API is running 🚀",
        "docs": "/docs",
    }


# ========================
# 健康检查
# ========================
@app.get("/health")
def health():
    return {"status": "ok"}


# ========================
# 注册路由
# ========================
app.include_router(api_router)


# ========================
# 本地运行
# ========================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )