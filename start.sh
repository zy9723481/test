#!/bin/bash

# 启动后端服务
echo "启动后端服务..."
cd backend
python app.py &
BACKEND_PID=$!
sleep 2

# 启动前端服务
echo "启动前端服务..."
cd ../frontend
python -m http.server 8000 &
FRONTEND_PID=$!
sleep 2

echo "服务启动完成！"
echo "后端服务运行在: http://localhost:5000"
echo "前端服务运行在: http://localhost:8000"
echo "登录页面: http://localhost:8000/index.html"

echo "按 Ctrl+C 停止所有服务"

# 等待用户输入
read -r

# 停止服务
echo "停止服务..."
kill $BACKEND_PID
kill $FRONTEND_PID
echo "服务已停止"
