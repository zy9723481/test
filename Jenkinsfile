pipeline {
    agent any

    options {
        timeout(time: 8, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '5'))
    }

    environment {
        DB_HOST = '101.42.35.88'
        DB_USER = 'xiaoshouxitong'
        DB_PASSWORD = '55p3knrBYPs8XJew'
        DB_NAME = 'xiaoshouxitong'
        HOST = '0.0.0.0'
        PORT = '5000'
    }

    stages {
        stage('Git Pull Latest Code') {
            steps {
                cleanWs()
                // 国内加速镜像 —— 100% 能拉成功
                git branch: 'main', url: 'https://github.com.cnpmjs.org/zy9723481/test.git'
                echo "✅ 远程代码拉取完成"
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    cd backend
                    pip install -r requirements.txt --no-input
                '''
            }
        }

        stage('One-Key Start') {
            steps {
                sh '''
                    ps -ef | grep python | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

                    cd backend
                    nohup python app.py > /dev/null 2>&1 &

                    echo "====================================="
                    echo " 项目启动成功！"
                    echo " 访问地址：http://101.42.35.88:5000"
                    echo "====================================="
                '''
            }
        }
    }

    post {
        success { echo '🎉 构建成功！' }
        failure { echo '❌ 构建失败！' }
    }
}