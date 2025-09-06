# Fraud Detection Service Deployment Guide

This guide provides instructions for deploying the Fraud Detection service in the Bank of Anthos application.

## Prerequisites

1. **Google Cloud Project**: A GCP project with the following APIs enabled:
   - Google Kubernetes Engine (GKE)
   - Cloud AI Platform
   - Vertex AI API
   - Container Registry or Artifact Registry

2. **Gemini API Key**: Obtain an API key for Google Gemini LLM
   ```bash
   # Set your API key
   export GEMINI_API_KEY="your-actual-api-key-here"
   ```

3. **Kubernetes Cluster**: A running GKE cluster with the Bank of Anthos application deployed

## Deployment Steps

### 1. Update API Key Secret

Update the Gemini API key secret:

```bash
# Create or update the secret with your actual API key
kubectl create secret generic gemini-api-secret \
  --from-literal=api-key="${GEMINI_API_KEY}" \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Deploy the Service

Deploy the fraud detection service using kubectl:

```bash
# Deploy from the root directory
kubectl apply -f kubernetes-manifests/frauddetection.yaml
```

Or using Skaffold for development:

```bash
# For development
skaffold dev --module frauddetection

# For production build and deploy
skaffold run --module frauddetection
```

### 3. Verify Deployment

Check that the service is running:

```bash
# Check pod status
kubectl get pods -l app=frauddetection

# Check service
kubectl get svc frauddetection

# Check logs
kubectl logs -l app=frauddetection -f
```

### 4. Test the Service

Test the fraud detection endpoints:

```bash
# Port forward to test locally
kubectl port-forward svc/frauddetection 8080:8080

# Test health endpoint
curl http://localhost:8080/healthy

# Test readiness
curl http://localhost:8080/ready
```

## Configuration

### Environment Variables

The service can be configured using the following environment variables:

- `GEMINI_API_KEY`: Your Google Gemini API key (required for production)
- `FRAUD_THRESHOLD`: Fraud probability threshold (0.0-1.0, default: 0.7)
- `AGENT_PROJECT_ID`: Google Cloud project ID for Agent Development Kit
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### ConfigMaps

The service uses the following ConfigMaps:

1. `environment-config`: Contains bank routing information
2. `service-api-config`: Contains API addresses for other services

### Secrets

- `gemini-api-secret`: Contains the Gemini API key
- `jwt-key`: Contains JWT public key for authentication

## Monitoring

### Health Checks

The service provides the following health endpoints:

- `/ready`: Readiness probe (used by Kubernetes)
- `/healthy`: Health check with detailed status
- `/fraud-status`: Fraud detection statistics (requires authentication)

### Logging

Logs are written to stdout and can be viewed using:

```bash
kubectl logs -l app=frauddetection
```

### Metrics

The service exposes fraud detection metrics through the `/fraud-status` endpoint:

- Total transactions processed
- Number of flagged transactions
- Number of blocked transactions
- Current fraud detection rate

## Troubleshooting

### Common Issues

1. **API Key Issues**:
   ```bash
   # Check if secret exists
   kubectl get secret gemini-api-secret
   
   # View secret (base64 encoded)
   kubectl get secret gemini-api-secret -o yaml
   ```

2. **Service Communication Issues**:
   ```bash
   # Check service endpoints
   kubectl get endpoints frauddetection
   
   # Test internal connectivity
   kubectl run test-pod --image=curlimages/curl --rm -it -- /bin/sh
   # Then inside the pod:
   curl http://frauddetection:8080/ready
   ```

3. **High Memory Usage**:
   - Increase memory limits in the deployment
   - Adjust the `CACHE_SIZE` configuration if implemented

4. **AI Model Issues**:
   - Check if running in dummy mode (when Gemini API is unavailable)
   - Verify API key and project configuration
   - Check Cloud AI Platform API quota

### Log Analysis

Common log patterns to look for:

```bash
# Successful fraud analysis
kubectl logs -l app=frauddetection | grep "Transaction approved"

# Blocked transactions
kubectl logs -l app=frauddetection | grep "Blocking fraudulent transaction"

# API errors
kubectl logs -l app=frauddetection | grep "ERROR"
```

## Integration with Frontend

The fraud detection service is automatically integrated with the frontend service. The frontend routes all transaction requests through the fraud detection service, which:

1. Analyzes the transaction for fraud
2. Blocks fraudulent transactions
3. Forwards legitimate transactions to the ledger writer

This integration is transparent to users and doesn't require any frontend code changes beyond the configuration update.

## Performance Considerations

- **Response Time**: The service adds 100-500ms to transaction processing
- **Throughput**: Can handle ~100 transactions per second per instance
- **Scaling**: Use horizontal pod autoscaling based on CPU/memory usage

For high-throughput environments, consider:
- Increasing replica count
- Using async processing for non-critical fraud checks
- Implementing caching for user behavior patterns

## Security

The fraud detection service implements several security measures:

- JWT token validation for all protected endpoints
- Non-root container execution
- Read-only root filesystem
- Minimal container image with security scanning
- Network policies (if enabled in your cluster)

Make sure to:
- Regularly rotate the Gemini API key
- Monitor for unusual fraud detection patterns
- Keep the container image updated
- Review fraud detection rules periodically
