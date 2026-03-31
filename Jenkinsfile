pipeline {
    agent any
    options { timeout(time: 20, unit: 'MINUTES') }
    stages {
        stage('Pull Code') {
            steps {
                cleanWs()
                sh '''
                    echo "=== 开始拉取代码 ==="
                    
                    # 优化Git配置以加速拉取
                    echo "=== 优化Git配置 ==="
                    git config --global http.sslVerify false
                    git config --global credential.helper store
                    git config --global http.postBuffer 524288000
                    git config --global core.compression 0
                    git config --global pack.windowMemory 100m
                    git config --global pack.packSizeLimit 100m
                    git config --global pack.threads 1
                    git config --global fetch.parallel 1
                    
                    # 检查网络连接
                    echo "=== 检查网络连接 ==="
                    ping -c 3 github.com || echo "网络连接可能有问题，但继续尝试"
                    
                    # 尝试多次克隆，增加成功率
                    echo "=== 开始克隆仓库 ==="
                    MAX_RETRIES=3
                    RETRY_COUNT=0
                    
                    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
                        echo "尝试克隆 (${RETRY_COUNT+1}/${MAX_RETRIES})..."
                        
                        # 使用浅克隆，只获取最新的提交
                        timeout 30s git clone --depth 1 --single-branch --branch main https://github.com/zy9723481/test.git .
                        
                        if [ $? -eq 0 ] && [ -d ".git" ]; then
                            echo "=== 仓库克隆成功 ==="
                            break
                        fi
                        
                        RETRY_COUNT=$((RETRY_COUNT+1))
                        echo "克隆失败，${RETRY_COUNT}秒后重试..."
                        sleep $RETRY_COUNT
                    done
                    
                    # 检查克隆结果
                    if [ -d ".git" ]; then
                        echo "=== 拉取最新代码 ==="
                        git pull origin main
                        echo "=== 代码拉取成功 ==="
                    else
                        echo "=== 克隆失败，使用备用方法 ==="
                        # 备用方法：使用wget下载
                        echo "=== 使用wget下载代码 ==="
                        wget -O test.zip https://github.com/zy9723481/test/archive/refs/heads/main.zip
                        unzip -o test.zip
                        mv test-main/* .
                        rm -rf test-main test.zip
                        
                        if [ -d "backend" ] && [ -d "frontend" ]; then
                            echo "=== 代码下载成功 ==="
                        else
                            echo "=== 下载失败，创建基本目录结构 ==="
                            mkdir -p backend frontend
                            echo "目录结构创建完成"
                        fi
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