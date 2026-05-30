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

        stage('CI - Build Test Image') {
            steps {
                sh '''
                    cat > Dockerfile.test << 'EOF'
FROM python:3.11-slim
RUN pip install flake8 pylint pytest jsonschema num2words requests -q
WORKDIR /workspace
EOF
                    docker build -t dte-sv-test-env -f Dockerfile.test .
                '''
            }
        }

        stage('CI - Run Tests') {
            steps {
                sh '''
                    CONTAINER_ID=$(docker create dte-sv-test-env)
                    docker cp custom-addons ${CONTAINER_ID}:/workspace/
                    docker cp tests ${CONTAINER_ID}:/workspace/
                    docker start ${CONTAINER_ID}
                    docker exec ${CONTAINER_ID} sh -c "flake8 custom-addons/dte_sv/ tests/ --max-line-length=120 --ignore=E501,W503,E261 && pylint custom-addons/dte_sv/ tests/ --max-line-length=120 --disable=C0114,C0115,C0116,R0801,R0903 && pytest tests/ -v --tb=short"
                    docker rm ${CONTAINER_ID}
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    GIT_COMMIT=$(git rev-parse HEAD)
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:${GIT_COMMIT} .
                    docker build -t ${REGISTRY}/${IMAGE_NAME}:latest .
                    echo "Built: ${REGISTRY}/${IMAGE_NAME}:\${GIT_COMMIT} and latest"
                '''
            }
        }

        stage('Push to Registry') {
            steps {
                sh '''
                    GIT_COMMIT=$(git rev-parse HEAD)
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
                    GIT_COMMIT=$(git rev-parse HEAD)
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
                    GIT_COMMIT=$(git rev-parse HEAD)
                    curl -s -X POST "https://api.github.com/repos/Marroquin02/Sistema-Facturacion-Electronica/statuses/${GIT_COMMIT}" \
                        -H "Authorization: token ${GITHUB_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d '{"state":"failure","context":"ci/jenkins","description":"CI checks failed"}'
                '''
            }
        }
    }
}