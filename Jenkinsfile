pipeline {
    agent any

    environment {
        REGISTRY = 'registry.fopinet.com'
        IMAGE_NAME = 'dte_sv'
        REGISTRY_CREDS = credentials('registry-fopinet-creds')
        GITHUB_TOKEN = credentials('github-api-token')
        DOKPLOY_WEBHOOK = 'https://dokploy.fopinet.com/api/deploy/compose/RJeR51sk8LAf8xMmYPkwl'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup - Install Dependencies') {
            steps {
                sh 'pip install flake8 pylint pytest jsonschema num2words requests -q'
            }
        }

        stage('Lint - flake8') {
            steps {
                sh 'flake8 custom-addons/dte_sv/ tests/ --max-line-length=120 --ignore=E501,W503,E261'
            }
        }

        stage('Lint - pylint') {
            steps {
                sh 'pylint custom-addons/dte_sv/ tests/ --max-line-length=120 --disable=C0114,C0115,C0116,R0801,R0903'
            }
        }

        stage('Test - pytest') {
            steps {
                sh 'pytest tests/ -v --tb=short'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    GIT_COMMIT=$(git rev-parse --short HEAD)
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:${GIT_COMMIT} .
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:latest .
                    echo "Built: ${REGISTRY}/${IMAGE_NAME}:\${GIT_COMMIT} and latest"
                '''
            }
        }

        stage('Push to Registry') {
            steps {
                sh '''
                    GIT_COMMIT=$(git rev-parse --short HEAD)
                    echo "${REGISTRY_CREDS_PSW}" | docker login ${REGISTRY} -u "${REGISTRY_CREDS_USR}" --password-stdin
                    docker push ${REGISTRY}/${IMAGE_NAME}:${GIT_COMMIT}
                    docker push ${REGISTRY}/${IMAGE_NAME}:latest
                    docker logout ${REGISTRY}
                    echo "Images pushed successfully"
                '''
            }
        }

        stage('Trigger Dokploy Deploy') {
            steps {
                sh '''
                    curl -X POST "${DOKPLOY_WEBHOOK}"
                    echo "Dokploy deploy triggered"
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
            script {
                sh '''
                    GIT_COMMIT=$(git rev-parse --short HEAD)
                    curl -s -X POST "https://api.github.com/repos/Marroquin02/Sistema-Facturacion-Electronica/statuses/${GIT_COMMIT}" \
                        -H "Authorization: token ${GITHUB_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d '{"state":"success","context":"ci/jenkins","description":"All CI checks passed"}'
                '''
            }
        }
        failure {
            echo 'Pipeline failed. Check Jenkins logs.'
            script {
                sh '''
                    GIT_COMMIT=$(git rev-parse --short HEAD)
                    curl -s -X POST "https://api.github.com/repos/Marroquin02/Sistema-Facturacion-Electronica/statuses/${GIT_COMMIT}" \
                        -H "Authorization: token ${GITHUB_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d '{"state":"failure","context":"ci/jenkins","description":"CI checks failed"}'
                '''
            }
        }
    }
}