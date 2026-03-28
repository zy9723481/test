@echo off

rem 启动后端服务
echo 启动后端服务...
cd backend
start "Backend Server" python app.py
sleep 2

rem 启动前端服务
echo 启动前端服务...
cd ../frontend
start "Frontend Server" python -m http.server 8000
sleep 2

echo 服务启动完成！
echo 后端服务运行在: http://localhost:5000
echo 前端服务运行在: http://localhost:8000
echo 登录页面: http://localhost:8000/index.html

echo 按任意键停止所有服务
pause

rem 停止服务
echo 停止服务...
taskkill /F /IM python.exe /T
echo 服务已停止
