pipeline {
    agent any

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
        stage('Prepare') {
            steps {
                sh 'ls -la'
            }
        }
    }
    
    post {
        success {
            echo 'Build successful!'
        }
        failure {
            echo 'Build failed!'
        }
    }
}