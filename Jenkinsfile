pipeline {
    agent any

    environment {
        REGISTRY = 'registry.fopinet.com'
        IMAGE_NAME = 'dte_sv'
        REGISTRY_CREDS = credentials('registry-fopinet-creds')
        GITHUB_TOKEN = credentials('github-api-token')
        DOKPLOY_WEBHOOK = 'https://dokploy.fopinet.com/api/deploy/compose/RJeR51sk8LAf8xMmYPkwl'
        JENKINS_URL = 'https://jenkins.fopinet.com'
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
CMD ["sleep", "infinity"]
EOF
                    docker build -t dte-sv-test-env -f Dockerfile.test .
                '''
            }
        }

        stage('CI - Run Tests') {
            steps {
                sh '''
                    # Clean up any previous container with same name
                    docker rm -f dte-sv-test || true

                    docker run -d --name dte-sv-test dte-sv-test-env
                    docker cp custom-addons dte-sv-test:/workspace/
                    docker cp tests dte-sv-test:/workspace/

                    # Capture linting output
                    docker exec dte-sv-test sh -c "flake8 custom-addons/dte_sv/ tests/ --max-line-length=120 > /tmp/flake8.out 2>&1; echo \$?" > /tmp/flake8_exit.out
                    docker exec dte-sv-test sh -c "pylint custom-addons/dte_sv/ tests/ --max-line-length=120 --disable=C0114,C0115,C0116,R0801,R0903,E0401,W0104,W0718,C0415,W0613,W0212,W0707,W1514 > /tmp/pylint.out 2>&1; echo \$?" > /tmp/pylint_exit.out

                    # Copy outputs to workspace
                    docker cp dte-sv-test:/tmp/flake8.out /tmp/flake8.out
                    docker cp dte-sv-test:/tmp/pylint.out /tmp/pylint.out

                    # Show outputs
                    echo "=== Flake8 ==="
                    cat /tmp/flake8.out || true
                    echo "=== Pylint ==="
                    cat /tmp/pylint.out || true

                    # Check exit codes
                    FLAKE8_EXIT=$(cat /tmp/flake8_exit.out | tr -d '[:space:]')
                    PYLINE_EXIT=$(cat /tmp/pylint_exit.out | tr -d '[:space:]')

                    echo "flake8 exit: $FLAKE8_EXIT"
                    echo "pylint exit: $PYLINE_EXIT"

                    if [ "$FLAKE8_EXIT" != "0" ] || [ "$PYLINE_EXIT" != "0" ]; then
                        echo "Linting failed"
                        exit 1
                    fi

                    docker rm -f dte-sv-test
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
                def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                def consoleUrl = "${env.BUILD_URL}console"
                def payload = '{"state":"success","context":"ci/jenkins","description":"All CI checks passed","target_url":"' + consoleUrl + '"}'
                sh "curl -s -X POST 'https://api.github.com/repos/Marroquin02/Sistema-Facturacion-Electronica/statuses/${gitCommit}' -H 'Authorization: token ${env.GITHUB_TOKEN}' -H 'Content-Type: application/json' -d '${payload}'"
            }
        }
        failure {
            echo 'Pipeline failed. Sending details to GitHub.'
            script {
                def gitCommit = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
                def consoleUrl = "${env.BUILD_URL}console"

                def flake8Count = sh(script: 'wc -l < /tmp/flake8.out 2>/dev/null || echo "0"', returnStdout: true).trim()
                def pylintCount = sh(script: 'wc -l < /tmp/pylint.out 2>/dev/null || echo "0"', returnStdout: true).trim()

                def desc = (fileExists('/tmp/flake8.out') && size('/tmp/flake8.out') > 0)
                    ? "Linting failed: ${flake8Count} flake8 errors, ${pylintCount} pylint issues"
                    : "CI checks failed"
                desc = desc.take(140)

                def payload = '{"state":"failure","context":"ci/jenkins","description":"' + desc + '","target_url":"' + consoleUrl + '"}'
                sh "echo 'Sending to GitHub: ${desc}' && curl -s -X POST 'https://api.github.com/repos/Marroquin02/Sistema-Facturacion-Electronica/statuses/${gitCommit}' -H 'Authorization: token ${env.GITHUB_TOKEN}' -H 'Content-Type: application/json' -d '${payload}'"
            }
        }
    }
}