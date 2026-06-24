import subprocess

print("🚀 启动 Denpa...")

subprocess.Popen("cd denpa-ui && npm run dev", shell=True)
subprocess.Popen("uvicorn app.main:app --reload", shell=True)

input("按回车退出...")