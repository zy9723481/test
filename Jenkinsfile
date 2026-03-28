pipeline {
    agent any

    options {
        timeout(time: 10, unit: 'MINUTES')
    }

    environment {
        DB_HOST = '101.42.35.88'
        DB_USER = 'xiaoshouxitong'
        DB_PASSWORD = '55p3knrBYPs8XJew'
        DB_NAME = 'xiaoshouxitong'
        SECRET_KEY = 'your_production_secret_key'
        HOST = '0.0.0.0'
        PORT = '5000'
    }

    stages {
        // 1. 拉最新代码
        stage('Pull Latest Code') {
            steps {
                cleanWs()
                git branch: 'main', url: 'https://github.com/zy9723481/test.git'
            }
        }

        // 2. 安装依赖
        stage('Install Dependencies') {
            steps {
                sh '''
                    cd backend
                    pip install -r requirements.txt --no-input
                '''
            }
        }

        // 3. 🔥 一键启动（前后端一起跑）
        stage('One-Key Start Project') {
            steps {
                sh '''
                    # 杀死旧服务
                    ps -ef | grep python | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

                    # 启动项目
                    cd backend
                    nohup python app.py > app.log 2>&1 &

                    sleep 3
                    echo "====================================="
                    echo " ✅ 项目启动成功！"
                    echo " 访问地址：http://服务器IP:5000 "
                    echo "====================================="
                '''
            }
        }
    }

    post {
        success { echo '🎉 构建 & 启动 全部完成！' }
        failure { echo '❌ 构建失败' }
    }
}