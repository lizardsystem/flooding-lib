pipeline {
    agent { label 'nxt' }
    stages {
        stage("Checkout") {
            steps {
                checkout scm
                sh "echo 'COMPOSE_PROJECT_NAME=${env.JOB_NAME}-${env.BUILD_ID}' > .env"
                sh "docker --version; docker-compose --version"
            }
        }
        stage("Build") {
            steps {
                sh "docker-compose down --volumes"
                sh "docker-compose build --build-arg uid=`id -u` --build-arg gid=`id -g` app"
                sh "docker-compose run --rm app buildout"
            }
        }
        stage("Test") {
            steps {
                sh "docker-compose run --rm app bin/test"
            }
        }
        }
    }
    post {
        always {
            sh "docker-compose down --volumes --remove-orphans && docker-compose rm -f"
        }
    }
}
