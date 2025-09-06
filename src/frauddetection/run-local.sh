#!/bin/bash

# Local Development Script for Fraud Detection Service
# This script helps you test the fraud detection service locally

echo "🚀 Bank of Anthos - Fraud Detection Service Local Development"
echo "============================================================="

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is running"

# Build the fraud detection service
echo "🔨 Building fraud detection service..."
cd "$(dirname "$0")"

# Create a local .env file for development
cat > .env.local << EOF
FRAUD_THRESHOLD=0.5
LOG_LEVEL=DEBUG
AGENT_PROJECT_ID=gke-boa-471214
GEMINI_API_KEY=AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU
PORT=8080
LOCAL_TESTING=true
TRANSACTIONS_API_ADDR=mockservice:8081
HISTORY_API_ADDR=mockservice:8082
BALANCES_API_ADDR=mockservice:8083
EOF

# Build the Docker image
docker build -t frauddetection:latest .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Failed to build Docker image"
    exit 1
fi

# Run the service
echo "🏃 Starting fraud detection service on port 8080..."
echo "📝 Logs will be shown below. Press Ctrl+C to stop."
echo ""

docker run --rm -p 8080:8080 --env-file .env.local frauddetection:latest
