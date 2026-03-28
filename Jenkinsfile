pipeline {
    agent any

    // 全局超时，防止构建卡死
    options {
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10')) // 保留10次构建记录
    }

    environment {
        // 项目环境变量
        DB_HOST = '101.42.35.88'
        DB_USER = 'xiaoshouxitong'
        DB_PASSWORD = '55p3knrBYPs8XJew'
        DB_NAME = 'xiaoshouxitong'
        SECRET_KEY = 'your_production_secret_key'
        HOST = '0.0.0.0'
        PORT = '5000'
    }

    stages {
        // ======================
        // 关键：强制拉取最新代码
        // ======================
        stage('Git Pull Latest Code') {
            steps {
                cleanWs() // 清理工作区，删除旧文件
                git(
                    url: 'https://github.com/zy9723481/test.git',
                    branch: 'main',
                    credentialsId: 'github-token',
                    extensions: [[$class: 'CleanCheckout']] // 强制干净拉取最新代码
                )
                echo "✅ 已拉取最新代码"
            }
        }

        // 查看文件结构
        stage('Check Files') {
            steps {
                sh 'ls -la'
            }
        }

        // 安装Python依赖
        stage('Install Dependencies') {
            steps {
                sh '''
                    cd backend
                    pip install -r requirements.txt --no-input --upgrade
                '''
                echo "✅ 依赖安装完成"
            }
        }

        // 构建打包
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

        // 启动服务（可选）
        stage('Start Service') {
            steps {
                echo "✅ 项目已完成构建，可以启动服务！"
            }
        }
    }

    post {
        success {
            echo '🎉 构建成功！代码是最新的！'
        }
        failure {
            echo '❌ 构建失败！'
        }
    }
}