@echo off
call .venv\Scripts\activate

echo 启动后端...
start cmd /k uvicorn app.main:app --reload

echo 启动前端...
cd frontend
start cmd /k npm run dev

pause