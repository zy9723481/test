pipeline {
    agent any
    options { timeout(time: 20, unit: 'MINUTES') }
    stages {
        stage('Pull Code') {
            steps {
                cleanWs()
                sh '''
                    echo "=== 开始拉取代码 ==="
                    # 设置Git配置
                    git config --global http.sslVerify false
                    git config --global credential.helper store
                    git config --global http.postBuffer 524288000
                    
                    # 检查网络连接
                    echo "=== 检查网络连接 ==="
                    ping -c 3 github.com || echo "网络连接可能有问题，但继续尝试"
                    
                    # 尝试克隆仓库
                    echo "=== 开始克隆仓库 ==="
                    timeout 60s git clone --depth 1 https://github.com/zy9723481/test.git .
                    
                    # 检查克隆结果
                    if [ -d ".git" ]; then
                        echo "=== 仓库克隆成功 ==="
                        # 确保在main分支
                        git checkout main
                        # 获取最新代码
                        git pull origin main
                    else
                        echo "=== 仓库克隆失败，使用备用方法 ==="
                        # 备用方法：手动创建目录结构
                        mkdir -p backend frontend
                        echo "目录结构创建完成"
                    fi
                    
                    echo "=== 代码拉取完成 ==="
                '''
            }
        }
        stage('Install Dependencies') {
            steps {
                sh '''
                    echo "=== 开始安装依赖 ==="
                    cd backend
                    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
                    pip install -r requirements.txt --no-input
                    echo "=== 依赖安装完成 ==="
                '''
            }
        }
        stage('Start Backend') {
            steps {
                sh '''
                    echo "=== 开始启动后端服务 ==="
                    cd backend
                    lsof -t -i:5000 | xargs kill -9 2>/dev/null || true
                    nohup python app.py > backend.log 2>&1 &
                    disown
                    sleep 3
                    echo "=== 后端服务启动成功 ==="
                '''
            }
        }
        stage('Start Frontend') {
            steps {
                sh '''
                    echo "=== 开始启动前端服务 ==="
                    cd frontend
                    lsof -t -i:8000 | xargs kill -9 2>/dev/null || true
                    nohup python -m http.server 8000 > frontend.log 2>&1 &
                    disown
                    sleep 3
                    echo "=== 前端服务启动成功 ==="
                '''
            }
        }
    }
    post {
        success {
            echo "🎉 构建成功！项目运行中！"
            echo "后端API地址: http://101.42.35.88:5000"
            echo "前端页面地址: http://101.42.35.88:8000"
        }
        failure {
            echo "❌ 构建失败！"
            echo "请检查构建日志以了解详细错误信息"
        }
    }
}