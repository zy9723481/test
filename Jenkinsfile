pipeline {
    agent any

    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
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
        stage('Git Pull Latest Code') {
            steps {
                cleanWs() // 清理旧文件，保证每次都是全新代码
                git branch: 'main', url: 'https://github.com/zy9723481/test.git'
                echo "✅ 已拉取最新代码"
            }
        }

        stage('Check Files') {
            steps {
                sh 'ls -la'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    cd backend
                    pip install -r requirements.txt --no-input --upgrade
                '''
                echo "✅ 依赖安装完成"
            }
        }

        stage('Build Project') {
            steps {
                sh '''
                    mkdir -p output
                    cp -r frontend output/
                    cp -r backend output/
                '''
                echo "✅ 项目构建完成"
            }
        }
    }

    post {
        success { echo '🎉 构建成功！永远使用最新代码！' }
        failure { echo '❌ 构建失败！' }
    }
}