#!/bin/bash

# 杀死所有旧服务
pkill -f "python3 app.py" 2>/dev/null
pkill -f "http.server" 2>/dev/null
sleep 2

# 设置环境变量
export DB_HOST='101.42.35.88'
export DB_USER='xiaoshouxitong'
export DB_PASSWORD='55p3knrBYPs8XJew'
export DB_NAME='xiaoshouxitong'
export SECRET_KEY='dev_key'
export HOST='0.0.0.0'
export PORT='5000'

# 进入正确目录
cd /root/.jenkins/workspace/backend

# 启动后端（永久运行）
nohup python3 app.py > /dev/null 2>&1 &
disown
sleep 3

# 启动前端
cd ../frontend
nohup python3 -m http.server 8000 > /dev/null 2>&1 &
disown
sleep 2

# 查看结果
echo "====================================="
netstat -tulnp | grep -E "5000|8000"
echo "====================================="
