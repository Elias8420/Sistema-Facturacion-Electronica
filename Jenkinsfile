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
CMD ["sleep", "infinity"]
EOF
                    docker build -t dte-sv-test-env -f Dockerfile.test .
                '''
            }
        }

        stage('CI - Run Tests') {
            steps {
                sh '''
                    docker run -d --name dte-sv-test dte-sv-test-env
                    docker cp custom-addons dte-sv-test:/workspace/
                    docker cp tests dte-sv-test:/workspace/

                    # Capture linting output
                    docker exec dte-sv-test sh -c "flake8 custom-addons/dte_sv/ tests/ --max-line-length=120 --ignore=E501,W503,E261,E241,E221,E272,E741,W292 > /tmp/flake8.out 2>&1; echo \$?" > /tmp/flake8_exit.out
                    docker exec dte-sv-test sh -c "pylint custom-addons/dte_sv/ tests/ --max-line-length=120 --disable=C0114,C0115,C0116,R0801,R0903 > /tmp/pylint.out 2>&1; echo \$?" > /tmp/pylint_exit.out

                    # Copy outputs to workspace
                    docker cp dte-sv-test:/tmp/flake8.out /tmp/flake8.out
                    docker cp dte-sv-test:/tmp/pylint.out /tmp/pylint.out

                    # Show outputs
                    echo "=== Flake8 ==="
                    cat /tmp/flake8.out || true
                    echo "=== Pylint ==="
                    cat /tmp/pylint.out || true

                    # Check exit codes
                    FLAKE8_EXIT=\$(cat /tmp/flake8_exit.out | tr -d '[:space:]')
                    PYLINE_EXIT=\$(cat /tmp/pylint_exit.out | tr -d '[:space:]')

                    echo "flake8 exit: \$FLAKE8_EXIT"
                    echo "pylint exit: \$PYLINE_EXIT"

                    if [ "\$FLAKE8_EXIT" != "0" ] || [ "\$PYLINE_EXIT" != "0" ]; then
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
            echo 'Pipeline failed. Sending details to GitHub.'
            script {
                sh '''
                    GIT_COMMIT=$(git rev-parse HEAD)

                    # Count errors from flake8 and pylint
                    FLAKE8_COUNT=\$(wc -l < /tmp/flake8.out 2>/dev/null || echo "0")
                    PYLINE_COUNT=\$(wc -l < /tmp/pylint.out 2>/dev/null || echo "0")

                    # Build description
                    if [ -f /tmp/flake8.out ] && [ -s /tmp/flake8.out ]; then
                        DESC="Linting failed: \${FLAKE8_COUNT} flake8 errors, \${PYLINE_COUNT} pylint issues"
                    else
                        DESC="CI checks failed"
                    fi

                    # Truncate to 140 chars
                    DESC=\$(echo "\$DESC" | cut -c1-140)

                    echo "Sending to GitHub: \$DESC"

                    curl -s -X POST "https://api.github.com/repos/Marroquin02/Sistema-Facturacion-Electronica/statuses/${GIT_COMMIT}" \
                        -H "Authorization: token ${GITHUB_TOKEN}" \
                        -H "Content-Type: application/json" \
                        -d "{\"state\":\"failure\",\"context\":\"ci/jenkins\",\"description\":\"\$DESC\"}"
                '''
            }
        }
    }
}