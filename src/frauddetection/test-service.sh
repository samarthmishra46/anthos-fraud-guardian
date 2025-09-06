#!/bin/bash

# Test script for Fraud Detection Service
echo "🧪 Testing Fraud Detection Service"
echo "=================================="

# Check if service is running
echo "1. Checking service health..."
curl -s http://localhost:8080/healthy | jq . || echo "Service not responding or jq not installed"

echo -e "\n2. Checking service readiness..."
curl -s http://localhost:8080/ready | jq . || echo "Service not ready or jq not installed"

echo -e "\n3. Testing normal transaction..."
curl -s -X POST http://localhost:8080/analyze-transaction \
  -H "Authorization: Bearer dummy-test-token-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAccountNum": "1234567890",
    "toAccountNum": "0987654321",
    "amount": "100.00",
    "description": "Coffee purchase",
    "uuid": "test-uuid-1"
  }' | jq . || echo "Failed to analyze normal transaction"

echo -e "\n4. Testing high-risk transaction..."
curl -s -X POST http://localhost:8080/analyze-transaction \
  -H "Authorization: Bearer dummy-test-token-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "fromAccountNum": "1234567890",
    "toAccountNum": "0987654321",
    "amount": "15000.00",
    "description": "Large suspicious transfer",
    "uuid": "test-uuid-2"
  }' | jq . || echo "Failed to analyze high-risk transaction"

echo -e "\n5. Checking fraud statistics..."
curl -s -H "Authorization: Bearer dummy-test-token-12345" \
  http://localhost:8080/fraud-status | jq . || echo "Failed to get fraud status"

echo -e "\n✅ Test completed!"
echo "If you see JSON responses above, the service is working correctly."
echo "If you see errors, check that the service is running on port 8080."
