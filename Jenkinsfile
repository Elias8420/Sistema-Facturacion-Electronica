pipeline {
    agent any

    environment {
        REGISTRY = 'registry.fopinet.com'
        IMAGE_NAME = 'dte_sv'
        REGISTRY_CREDS = credentials('registry-fopinet-creds')
        DOKPLOY_WEBHOOK = 'https://dokploy.fopinet.com/api/deploy/compose/RJeR51sk8LAf8xMmYPkwl'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Lint - flake8') {
            steps {
                sh 'flake8 custom-addons/dte_sv/ --max-line-length=120 --ignore=E501,W503,E261'
            }
        }

        stage('Lint - pylint') {
            steps {
                sh 'pylint custom-addons/dte_sv/ --max-line-length=120 --disable=C0114,C0115,C0116,R0801,R0903'
            }
        }

        stage('Test - Validate JSON Schemas') {
            steps {
                sh '''
                    python3 -c "
                    import json, sys, os
                    schemas_dir = 'custom-addons/dte_sv/static/schemas'
                    schemas = ['fe-f-v2.json', 'fe-ccf-v4.json', 'fe-nc-v4.json']
                    for schema_file in schemas:
                        path = os.path.join(schemas_dir, schema_file)
                        with open(path) as f:
                            json.load(f)
                        print(f'OK: {schema_file}')
                    print('All schemas are valid JSON')
                    "
                '''
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
        failure {
            echo 'Pipeline failed. Check Jenkins logs.'
        }
        success {
            echo 'Pipeline completed successfully!'
        }
    }
}