# Fraud Detection Service

The fraud detection service analyzes transactions in real-time to identify potentially fraudulent activity using Google's Agent Development Kit and Gemini LLM. This service intercepts transaction requests before they are written to the ledger and provides fraud risk assessment.

Implemented in Python with Flask and Google Agent Development Kit.

## Overview

This service acts as a middleware between the frontend and ledgerwriter services. When a transaction is initiated, it:

1. Receives transaction details from the frontend
2. Fetches user transaction history
3. Analyzes the transaction using Gemini LLM through Agent Development Kit
4. Returns fraud risk assessment
5. Forwards legitimate transactions to ledgerwriter

## Endpoints

| Endpoint              | Type  | Auth? | Description                                                     |
| --------------------- | ----- | ----- | --------------------------------------------------------------- |
| `/ready`              | GET   |       | Readiness probe endpoint                                        |
| `/healthy`            | GET   |       | Health check endpoint                                           |
| `/analyze-transaction`| POST  | 🔒    | Analyzes a transaction for fraud and forwards if legitimate     |
| `/fraud-status`       | GET   | 🔒    | Returns fraud detection statistics                              |
| `/version`            | GET   |       | Returns the contents of `$VERSION`                             |

## Environment Variables

- `VERSION`
  - a version string for the service
- `PORT`
  - the port for the webserver (default: 8080)
- `LOG_LEVEL`
  - the service-wide log level (default: INFO)
- `GEMINI_API_KEY`
  - API key for Google Gemini LLM
- `FRAUD_THRESHOLD`
  - fraud probability threshold (0.0-1.0, default: 0.7)
- `AGENT_PROJECT_ID`
  - Google Cloud project ID for Agent Development Kit

- ConfigMap `environment-config`:
  - `LOCAL_ROUTING_NUM`
    - the routing number for our bank
  - `PUB_KEY_PATH`
    - the path to the JWT signer's public key, mounted as a secret

- ConfigMap `service-api-config`:
  - `TRANSACTIONS_API_ADDR`
    - the address and port of the `ledgerwriter` service
  - `HISTORY_API_ADDR`
    - the address and port of the `transactionhistory` service
  - `BALANCES_API_ADDR`
    - the address and port of the `balancereader` service

## Fraud Detection Features

- **Transaction Pattern Analysis**: Analyzes spending patterns, amounts, and frequency
- **Geolocation Verification**: Checks for unusual location-based transactions
- **Time-based Analysis**: Identifies transactions at unusual hours
- **Velocity Checks**: Detects rapid successive transactions
- **Amount Anomaly Detection**: Flags unusually large transactions
- **Merchant Category Analysis**: Analyzes spending by merchant types

## Agent Development Kit Integration

The service uses Google's Agent Development Kit to:
- Create intelligent agents for fraud analysis
- Leverage Gemini LLM for natural language processing of transaction patterns
- Implement real-time decision making for fraud detection
- Provide explanations for fraud determinations

## Kubernetes Resources

- [deployments/frauddetection](/kubernetes-manifests/frauddetection.yaml)
- [service/frauddetection](/kubernetes-manifests/frauddetection.yaml)
