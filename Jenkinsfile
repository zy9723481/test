pipeline {
    agent any
    options { timeout(time: 20, unit: 'MINUTES') }
    stages {
        stage('Pull Code') {
            steps {
                cleanWs()
                sh '''
                    git config --global http.sslVerify false
                    git clone https://github.com/zy9723481/test.git . --depth 1 --single-branch
                '''
            }
        }
        stage('Install Dependencies') {
            steps {
                sh '''
                    cd backend
                    pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
                    pip install -r requirements.txt --no-input
                '''
            }
        }
        stage('Start Backend') {
            steps {
                sh '''
                    cd backend
                    lsof -t -i:5000 | xargs kill -9 2>/dev/null || true
                    nohup python app.py > backend.log 2>&1 &
                    disown
                    sleep 3
                    echo "✅ 后端服务启动成功！"
                '''
            }
        }
        stage('Start Frontend') {
            steps {
                sh '''
                    cd frontend
                    lsof -t -i:8000 | xargs kill -9 2>/dev/null || true
                    nohup python -m http.server 8000 > frontend.log 2>&1 &
                    disown
                    sleep 3
                    echo "✅ 前端服务启动成功！"
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
        }
    }
}