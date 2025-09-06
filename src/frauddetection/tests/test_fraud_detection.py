# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to sys.path to import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, fraud_agent, FraudDetectionAgent

class TestFraudDetectionService(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Sample transaction data
        self.sample_transaction = {
            "fromAccountNum": "1234567890",
            "toAccountNum": "0987654321",
            "amount": "100.00",
            "description": "Test payment"
        }
        
        # Sample transaction history
        self.sample_history = [
            {"amount": "50.00", "description": "Coffee"},
            {"amount": "25.00", "description": "Lunch"},
            {"amount": "200.00", "description": "Groceries"}
        ]
    
    def test_health_endpoints(self):
        """Test health check endpoints"""
        # Test readiness probe
        response = self.app.get('/ready')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'ready')
        
        # Test health check
        response = self.app.get('/healthy')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        
        # Test version endpoint
        response = self.app.get('/version')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('version', data)
    
    @patch('main.fetch_user_history')
    def test_fraud_detection_agent(self, mock_fetch_history):
        """Test fraud detection agent functionality"""
        mock_fetch_history.return_value = self.sample_history
        
        # Test normal transaction
        agent = FraudDetectionAgent("test-project")
        result = agent.analyze_transaction(self.sample_transaction, self.sample_history)
        
        self.assertIn('is_fraud', result)
        self.assertIn('fraud_score', result)
        self.assertIn('fraud_indicators', result)
        self.assertIsInstance(result['fraud_score'], float)
        self.assertGreaterEqual(result['fraud_score'], 0.0)
        self.assertLessEqual(result['fraud_score'], 1.0)
    
    def test_amount_analysis(self):
        """Test amount-based fraud analysis"""
        agent = FraudDetectionAgent("test-project")
        
        # Test normal amount
        result = agent._analyze_amount(100.0, self.sample_history)
        self.assertIn('score', result)
        self.assertIn('is_suspicious', result)
        
        # Test high amount
        result = agent._analyze_amount(15000.0, self.sample_history)
        self.assertTrue(result['is_suspicious'])
        self.assertGreater(result['score'], 0.5)
    
    def test_velocity_analysis(self):
        """Test velocity-based fraud analysis"""
        from datetime import datetime
        agent = FraudDetectionAgent("test-project")
        
        current_time = datetime.now()
        result = agent._analyze_velocity(current_time, self.sample_history)
        
        self.assertIn('score', result)
        self.assertIn('is_suspicious', result)
    
    def test_time_pattern_analysis(self):
        """Test time-based fraud analysis"""
        from datetime import datetime
        agent = FraudDetectionAgent("test-project")
        
        # Test normal hours (e.g., 2 PM)
        normal_time = datetime.now().replace(hour=14)
        result = agent._analyze_time_pattern(normal_time, self.sample_history)
        self.assertFalse(result['is_suspicious'])
        
        # Test unusual hours (e.g., 3 AM)
        unusual_time = datetime.now().replace(hour=3)
        result = agent._analyze_time_pattern(unusual_time, self.sample_history)
        self.assertTrue(result['is_suspicious'])
    
    @patch('main.requests.get')
    @patch('main.requests.post')
    def test_analyze_transaction_endpoint(self, mock_post, mock_get):
        """Test the main transaction analysis endpoint"""
        # Mock external service responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = self.sample_history
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.content = json.dumps({"status": "success"}).encode()
        mock_post.return_value.headers = {"Content-Type": "application/json"}
        
        # Test with valid transaction (should be approved and forwarded)
        response = self.app.post(
            '/analyze-transaction',
            data=json.dumps(self.sample_transaction),
            content_type='application/json',
            headers={'Authorization': 'Bearer valid-test-token'}
        )
        
        # Should forward to ledger (mock returns 200)
        self.assertEqual(response.status_code, 200)
    
    def test_fraud_status_endpoint(self):
        """Test fraud status endpoint"""
        response = self.app.get(
            '/fraud-status',
            headers={'Authorization': 'Bearer valid-test-token'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('statistics', data)
        self.assertIn('fraud_rate_percentage', data)
        self.assertIn('threshold', data)
    
    def test_authentication_required(self):
        """Test that authentication is required for protected endpoints"""
        # Test without authorization header
        response = self.app.post('/analyze-transaction')
        self.assertEqual(response.status_code, 401)
        
        response = self.app.get('/fraud-status')
        self.assertEqual(response.status_code, 401)
        
        # Test with invalid token
        response = self.app.post(
            '/analyze-transaction',
            headers={'Authorization': 'Bearer invalid'}
        )
        self.assertEqual(response.status_code, 401)

if __name__ == '__main__':
    unittest.main()
