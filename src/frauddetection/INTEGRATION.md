# Fraud Detection Service Integration Guide

## Overview

The Fraud Detection service has been successfully created for the Bank of Anthos application. This service uses Google's Agent Development Kit and Gemini LLM to analyze transactions in real-time and block potentially fraudulent activity.

## What Was Created

### Core Service Files
- `src/frauddetection/main.py` - Main Flask application with fraud detection logic
- `src/frauddetection/agent_config.py` - Agent Development Kit configuration
- `src/frauddetection/README.md` - Service documentation
- `src/frauddetection/requirements.txt` - Python dependencies
- `src/frauddetection/Dockerfile` - Container configuration

### Kubernetes Deployment Files
- `src/frauddetection/k8s/frauddetection.yaml` - Local deployment manifest
- `kubernetes-manifests/frauddetection.yaml` - Main deployment manifest
- Updated `kubernetes-manifests/config.yaml` - Added fraud detection API endpoint

### CI/CD and Development Files
- `src/frauddetection/cloudbuild.yaml` - Google Cloud Build configuration
- `src/frauddetection/skaffold.yaml` - Skaffold development configuration
- Updated root `skaffold.yaml` - Added fraud detection module

### Testing and Configuration
- `src/frauddetection/tests/test_fraud_detection.py` - Unit tests
- `src/frauddetection/DEPLOYMENT.md` - Detailed deployment guide
- `src/frauddetection/.env.example` - Environment configuration examples

## Integration Points

### 1. Frontend Integration
The frontend service has been updated to route all transactions through the fraud detection service:
- Modified `src/frontend/frontend.py` to use `FRAUDDETECTION_API_ADDR`
- Transactions now go: Frontend → Fraud Detection → Ledger Writer

### 2. Configuration Updates
- Added `FRAUDDETECTION_API_ADDR: "frauddetection:8080"` to service-api-config
- Created `gemini-api-secret` for storing the Gemini API key

## How It Works

### Transaction Flow
1. **User initiates transaction** via frontend (payment/deposit)
2. **Frontend sends transaction** to fraud detection service at `/analyze-transaction`
3. **Fraud service analyzes transaction**:
   - Fetches user transaction history
   - Runs multiple fraud detection algorithms
   - Uses Gemini LLM for pattern analysis
   - Calculates fraud risk score
4. **Decision made**:
   - If fraud score < threshold: Forward to ledger writer
   - If fraud score ≥ threshold: Block transaction and return error
5. **Response sent back** to frontend with result

### Fraud Detection Methods
1. **Amount Analysis**: Checks for unusually high amounts or suspicious patterns
2. **Velocity Analysis**: Detects rapid successive transactions
3. **Time Pattern Analysis**: Flags transactions at unusual hours
4. **AI Analysis**: Uses Gemini LLM to analyze transaction patterns and context

## Quick Start

### 1. Set Up API Key
```bash
# Replace with your actual Gemini API key
export GEMINI_API_KEY="your-actual-gemini-api-key"

# Create the secret
kubectl create secret generic gemini-api-secret \
  --from-literal=api-key="${GEMINI_API_KEY}"
```

### 2. Deploy the Service
```bash
# Deploy everything
kubectl apply -f kubernetes-manifests/

# Or use Skaffold for development
skaffold dev
```

### 3. Verify Deployment
```bash
# Check if service is running
kubectl get pods -l app=frauddetection

# Check service health
kubectl port-forward svc/frauddetection 8080:8080
curl http://localhost:8080/healthy
```

## Configuration Options

### Environment Variables
- `FRAUD_THRESHOLD`: Risk score threshold (0.7 = 70% confidence, default)
- `GEMINI_API_KEY`: Your Google Gemini API key
- `LOG_LEVEL`: Logging verbosity (INFO, DEBUG, WARNING, ERROR)
- `AGENT_PROJECT_ID`: Google Cloud project ID for Agent Development Kit

### Fraud Detection Tuning
```python
# In agent_config.py, you can adjust:
FRAUD_THRESHOLD = 0.7  # 70% confidence threshold
AMOUNT_WEIGHT = 0.25   # Weight for amount-based analysis  
VELOCITY_WEIGHT = 0.25 # Weight for velocity analysis
TIME_WEIGHT = 0.15     # Weight for time-based analysis
PATTERN_WEIGHT = 0.35  # Weight for AI pattern analysis
```

## Testing the Service

### 1. Test Normal Transaction
```bash
curl -X POST http://localhost:8080/analyze-transaction \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAccountNum": "1234567890",
    "toAccountNum": "0987654321", 
    "amount": "100.00",
    "description": "Coffee purchase"
  }'
```

### 2. Test High-Risk Transaction
```bash
curl -X POST http://localhost:8080/analyze-transaction \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAccountNum": "1234567890",
    "toAccountNum": "0987654321",
    "amount": "15000.00",
    "description": "Large transfer"
  }'
```

### 3. Check Fraud Statistics
```bash
curl -H "Authorization: Bearer your-jwt-token" \
  http://localhost:8080/fraud-status
```

## Monitoring

### Key Metrics to Monitor
- **Fraud Detection Rate**: Percentage of transactions flagged/blocked
- **False Positive Rate**: Legitimate transactions incorrectly blocked
- **Response Time**: Time to analyze each transaction
- **Service Health**: Uptime and error rates

### Log Analysis
```bash
# View fraud detection logs
kubectl logs -l app=frauddetection -f

# Look for blocked transactions
kubectl logs -l app=frauddetection | grep "Blocking fraudulent"

# Monitor approval rates
kubectl logs -l app=frauddetection | grep "Transaction approved"
```

## Customization

### Adding New Fraud Rules
Edit `src/frauddetection/main.py` in the `FraudDetectionAgent` class:

```python
def _analyze_custom_pattern(self, transaction, history):
    # Add your custom fraud detection logic
    if custom_condition:
        return {
            'score': 0.8,
            'is_suspicious': True,
            'reason': 'Custom fraud pattern detected'
        }
```

### Adjusting AI Prompts
Modify the prompt in `_build_analysis_prompt()` method to change how Gemini analyzes transactions.

### Environment-Specific Configuration
Use different configurations for dev/staging/production environments in `agent_config.py`.

## Security Considerations

1. **API Key Security**: Store Gemini API key in Kubernetes secrets, not in code
2. **JWT Validation**: All endpoints require valid JWT tokens
3. **Network Security**: Service runs on internal cluster network only
4. **Container Security**: Runs as non-root user with read-only filesystem
5. **Audit Logging**: All fraud decisions are logged for compliance

## Troubleshooting

### Common Issues

1. **Service Not Starting**
   ```bash
   kubectl describe pod <frauddetection-pod-name>
   kubectl logs <frauddetection-pod-name>
   ```

2. **API Key Issues**
   ```bash
   kubectl get secret gemini-api-secret -o yaml
   # Check if api-key is properly base64 encoded
   ```

3. **High False Positive Rate**
   - Lower the `FRAUD_THRESHOLD` value
   - Adjust weights in fraud analysis algorithms
   - Review and tune the Gemini prompt

4. **Performance Issues**
   - Increase CPU/memory limits
   - Add more replicas
   - Optimize fraud detection algorithms

## Next Steps

1. **Production Deployment**:
   - Set up proper API key management
   - Configure monitoring and alerting
   - Set up log aggregation
   - Tune fraud detection parameters

2. **Enhancement Ideas**:
   - Add machine learning models for better fraud detection
   - Implement real-time user behavior profiling
   - Add geolocation-based fraud detection
   - Create fraud analyst dashboard
   - Implement feedback loops for model improvement

3. **Integration Extensions**:
   - Add fraud detection to account creation
   - Implement transaction limits based on risk scores
   - Create fraud detection APIs for other services
   - Add real-time fraud alerting

## Support

For issues or questions:
1. Check the logs: `kubectl logs -l app=frauddetection`
2. Review the deployment guide: `src/frauddetection/DEPLOYMENT.md`
3. Run the test suite: `python -m pytest src/frauddetection/tests/`
4. Check service health: `curl http://<service>/healthy`

The fraud detection service is now ready for deployment and integration with your Bank of Anthos application!
