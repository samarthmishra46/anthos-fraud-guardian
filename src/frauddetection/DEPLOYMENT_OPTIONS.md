# Deployment Options for Fraud Detection Service

## Current Status
- ❌ **Kubernetes Cluster**: Not currently connected to a cluster
- ✅ **Docker**: Available (version 28.3.3)
- ✅ **Google Cloud SDK**: Available (version 536.0.1)
- ✅ **API Key**: Configured (AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU)
- ✅ **Project ID**: Set (gke-boa-471214)

## Option 1: Local Development with Docker (Recommended for testing)

### Quick Start
```bash
# Navigate to fraud detection service
cd src/frauddetection

# Run the local development script
./run-local.sh
```

### Manual Docker Commands
```bash
# Build the image
docker build -t frauddetection:latest .

# Run with environment variables
docker run -p 8080:8080 \
  -e GEMINI_API_KEY="AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU" \
  -e AGENT_PROJECT_ID="gke-boa-471214" \
  -e FRAUD_THRESHOLD="0.5" \
  -e LOG_LEVEL="DEBUG" \
  frauddetection:latest
```

### Test the Service
```bash
# In another terminal, run tests
./test-service.sh
```

## Option 2: Google Cloud Run (Serverless deployment)

### Prerequisites
```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project gke-boa-471214

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Deploy to Cloud Run
```bash
# Build and deploy in one command
gcloud run deploy frauddetection \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU",AGENT_PROJECT_ID="gke-boa-471214",FRAUD_THRESHOLD="0.7"
```

## Option 3: Google Kubernetes Engine (GKE)

### Create a GKE Cluster
```bash
# Authenticate and set project
gcloud auth login
gcloud config set project gke-boa-471214

# Enable required APIs
gcloud services enable container.googleapis.com

# Create a small GKE cluster
gcloud container clusters create bank-of-anthos-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type e2-medium \
  --enable-autorepair \
  --enable-autoupgrade

# Get credentials
gcloud container clusters get-credentials bank-of-anthos-cluster --zone us-central1-a
```

### Deploy to GKE
```bash
# Create the API key secret
kubectl create secret generic gemini-api-secret \
  --from-literal=api-key="AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU"

# Deploy the application
kubectl apply -f kubernetes-manifests/frauddetection.yaml

# Check deployment
kubectl get pods -l app=frauddetection
kubectl get svc frauddetection
```

## Option 4: Local Kubernetes with Kind

### Install Kind
```bash
# Install kind
go install sigs.k8s.io/kind@latest
# OR using apt (if available)
sudo apt install kind

# Create a local cluster
kind create cluster --name bank-of-anthos

# Set kubectl context
kubectl cluster-info --context kind-bank-of-anthos
```

### Deploy to Kind
```bash
# Load Docker image into Kind
kind load docker-image frauddetection:latest --name bank-of-anthos

# Create secret and deploy
kubectl create secret generic gemini-api-secret \
  --from-literal=api-key="AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU"

kubectl apply -f kubernetes-manifests/frauddetection.yaml
```

## Option 5: Docker Compose (Full Local Stack)

### Create docker-compose.yml
```yaml
version: '3.8'
services:
  frauddetection:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GEMINI_API_KEY=AIzaSyCixf1Cz8FJSOvtRXyRb262ORZVu8eoFpU
      - AGENT_PROJECT_ID=gke-boa-471214
      - FRAUD_THRESHOLD=0.5
      - LOG_LEVEL=DEBUG
    
  # Mock services for testing
  mockservice:
    image: nginx:alpine
    ports:
      - "8081:80"
      - "8082:80" 
      - "8083:80"
```

### Run with Docker Compose
```bash
docker-compose up --build
```

## Recommended Next Steps

### For Immediate Testing (Option 1)
```bash
cd src/frauddetection
./run-local.sh
```

### For Production Deployment (Option 2 or 3)
1. **Cloud Run** (easiest): Follow Option 2 steps
2. **GKE** (full control): Follow Option 3 steps

### Testing Commands
```bash
# Test health
curl http://localhost:8080/healthy

# Test fraud detection
curl -X POST http://localhost:8080/analyze-transaction \
  -H "Authorization: Bearer test-token" \
  -H "Content-Type: application/json" \
  -d '{"fromAccountNum":"123","toAccountNum":"456","amount":"100.00"}'
```

## Troubleshooting

### Docker Issues
```bash
# Check Docker status
docker info

# View container logs
docker logs <container-id>
```

### GCloud Issues
```bash
# Check authentication
gcloud auth list

# Check project
gcloud config list project
```

### Kubernetes Issues
```bash
# Check cluster connection
kubectl cluster-info

# Check contexts
kubectl config get-contexts
```

Choose the option that best fits your needs:
- **Option 1**: Quick local testing
- **Option 2**: Serverless production deployment
- **Option 3**: Full Kubernetes production deployment
- **Option 4**: Local Kubernetes development
- **Option 5**: Full local stack with dependencies
