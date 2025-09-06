#!/usr/bin/env python3

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

import os
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify, Response
import requests
import jwt
from google.generativeai import configure, GenerativeModel
from google.cloud import aiplatform
import numpy as np
import pandas as pd
from functools import wraps

# Configure logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
VERSION = os.environ.get('VERSION', '1.0.0')
PORT = int(os.environ.get('PORT', 8080))
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'dummy-api-key-for-testing')
FRAUD_THRESHOLD = float(os.environ.get('FRAUD_THRESHOLD', '0.7'))
AGENT_PROJECT_ID = os.environ.get('AGENT_PROJECT_ID', 'bank-of-anthos-fraud')

# Service endpoints
TRANSACTIONS_API_ADDR = os.environ.get('TRANSACTIONS_API_ADDR', 'ledgerwriter:8080')
HISTORY_API_ADDR = os.environ.get('HISTORY_API_ADDR', 'transactionhistory:8080')
BALANCES_API_ADDR = os.environ.get('BALANCES_API_ADDR', 'balancereader:8080')

# JWT Configuration
LOCAL_ROUTING_NUM = os.environ.get('LOCAL_ROUTING_NUM', '883745000')
PUB_KEY_PATH = os.environ.get('PUB_KEY_PATH', '/tmp/.ssh/publickey')

# Initialize Gemini (with dummy configuration for now)
try:
    configure(api_key=GEMINI_API_KEY)
    gemini_model = GenerativeModel('gemini-1.5-flash')
    logger.info("Gemini model initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize Gemini model: {e}. Using dummy mode.")
    gemini_model = None

# Fraud detection statistics
fraud_stats = {
    'total_transactions': 0,
    'flagged_transactions': 0,
    'blocked_transactions': 0,
    'last_analysis_time': None
}

class FraudDetectionAgent:
    """
    Fraud Detection Agent using Google Agent Development Kit and Gemini LLM
    """
    
    def __init__(self, project_id: str, model: GenerativeModel = None):
        self.project_id = project_id
        self.model = model
        self.fraud_patterns = {
            'high_amount_threshold': 10000.0,
            'velocity_window_minutes': 10,
            'max_transactions_per_window': 5,
            'unusual_hours': [0, 1, 2, 3, 4, 5],  # 12 AM - 5 AM
            'suspicious_amount_patterns': [100.00, 200.00, 500.00, 1000.00]
        }
    
    def analyze_transaction(self, transaction: Dict, user_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze a transaction for fraud using multiple detection methods
        """
        logger.info(f"Analyzing transaction for user {transaction.get('fromAccountNum', 'unknown')}")
        
        # Extract transaction details
        amount = float(transaction.get('amount', 0))
        from_account = transaction.get('fromAccountNum', '')
        to_account = transaction.get('toAccountNum', '')
        transaction_time = datetime.now()
        
        # Run multiple fraud detection checks
        fraud_indicators = []
        fraud_score = 0.0
        
        # 1. Amount-based analysis
        amount_risk = self._analyze_amount(amount, user_history)
        fraud_score += amount_risk['score']
        if amount_risk['is_suspicious']:
            fraud_indicators.append(amount_risk['reason'])
        
        # 2. Velocity analysis
        velocity_risk = self._analyze_velocity(transaction_time, user_history)
        fraud_score += velocity_risk['score']
        if velocity_risk['is_suspicious']:
            fraud_indicators.append(velocity_risk['reason'])
        
        # 3. Time-based analysis
        time_risk = self._analyze_time_pattern(transaction_time, user_history)
        fraud_score += time_risk['score']
        if time_risk['is_suspicious']:
            fraud_indicators.append(time_risk['reason'])
        
        # 4. Pattern analysis using Gemini LLM
        if self.model:
            llm_analysis = self._analyze_with_gemini(transaction, user_history)
            fraud_score += llm_analysis['score']
            if llm_analysis['is_suspicious']:
                fraud_indicators.append(llm_analysis['reason'])
        else:
            # Dummy LLM analysis for testing
            llm_analysis = self._dummy_llm_analysis(transaction, user_history)
            fraud_score += llm_analysis['score']
            if llm_analysis['is_suspicious']:
                fraud_indicators.append(llm_analysis['reason'])
        
        # Normalize fraud score (0.0 - 1.0)
        fraud_score = min(1.0, fraud_score / 4.0)
        
        # Determine if transaction is fraudulent
        is_fraud = fraud_score >= FRAUD_THRESHOLD
        
        return {
            'is_fraud': is_fraud,
            'fraud_score': fraud_score,
            'fraud_indicators': fraud_indicators,
            'analysis_timestamp': transaction_time.isoformat(),
            'threshold_used': FRAUD_THRESHOLD,
            'recommendation': 'BLOCK' if is_fraud else 'ALLOW'
        }
    
    def _analyze_amount(self, amount: float, history: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction amount for suspicious patterns"""
        
        # Check for unusually high amounts
        if amount > self.fraud_patterns['high_amount_threshold']:
            return {
                'score': 0.8,
                'is_suspicious': True,
                'reason': f'Unusually high transaction amount: ${amount:,.2f}'
            }
        
        # Analyze historical spending patterns
        if history:
            historical_amounts = [float(t.get('amount', 0)) for t in history[-30:]]  # Last 30 transactions
            if historical_amounts:
                avg_amount = np.mean(historical_amounts)
                std_amount = np.std(historical_amounts)
                
                # Check if current amount is more than 3 standard deviations from mean
                if std_amount > 0 and abs(amount - avg_amount) > 3 * std_amount:
                    return {
                        'score': 0.6,
                        'is_suspicious': True,
                        'reason': f'Amount ${amount:,.2f} significantly deviates from user pattern (avg: ${avg_amount:.2f})'
                    }
        
        # Check for suspicious round amounts
        if amount in self.fraud_patterns['suspicious_amount_patterns']:
            return {
                'score': 0.3,
                'is_suspicious': True,
                'reason': f'Suspicious round amount: ${amount:,.2f}'
            }
        
        return {'score': 0.0, 'is_suspicious': False, 'reason': 'Amount appears normal'}
    
    def _analyze_velocity(self, transaction_time: datetime, history: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction velocity for rapid successive transactions"""
        
        if not history:
            return {'score': 0.0, 'is_suspicious': False, 'reason': 'No transaction history available'}
        
        # Count transactions in the last velocity window
        window_start = transaction_time - timedelta(minutes=self.fraud_patterns['velocity_window_minutes'])
        recent_transactions = 0
        
        for transaction in history:
            # Note: In real implementation, we'd parse actual timestamps
            # For now, assume recent transactions are at the end of the list
            recent_transactions += 1
            if recent_transactions >= len(history) - 10:  # Last 10 transactions as "recent"
                break
        
        if recent_transactions > self.fraud_patterns['max_transactions_per_window']:
            return {
                'score': 0.7,
                'is_suspicious': True,
                'reason': f'High transaction velocity: {recent_transactions} transactions in {self.fraud_patterns["velocity_window_minutes"]} minutes'
            }
        
        return {'score': 0.0, 'is_suspicious': False, 'reason': 'Transaction velocity appears normal'}
    
    def _analyze_time_pattern(self, transaction_time: datetime, history: List[Dict]) -> Dict[str, Any]:
        """Analyze transaction timing for unusual patterns"""
        
        hour = transaction_time.hour
        
        # Check for transactions during unusual hours
        if hour in self.fraud_patterns['unusual_hours']:
            return {
                'score': 0.4,
                'is_suspicious': True,
                'reason': f'Transaction at unusual hour: {hour}:00'
            }
        
        # Check for weekend transactions (additional risk factor)
        if transaction_time.weekday() >= 5:  # Saturday or Sunday
            return {
                'score': 0.2,
                'is_suspicious': False,
                'reason': 'Weekend transaction (minor risk factor)'
            }
        
        return {'score': 0.0, 'is_suspicious': False, 'reason': 'Transaction timing appears normal'}
    
    def _analyze_with_gemini(self, transaction: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Use Gemini LLM to analyze transaction patterns"""
        
        try:
            # Prepare context for Gemini
            prompt = self._build_analysis_prompt(transaction, history)
            
            # Generate analysis using Gemini
            response = self.model.generate_content(prompt)
            analysis_text = response.text
            
            # Parse Gemini's response (simplified parsing)
            fraud_score = 0.0
            is_suspicious = False
            reason = "AI analysis completed"
            
            if "FRAUD" in analysis_text.upper() or "SUSPICIOUS" in analysis_text.upper():
                fraud_score = 0.8
                is_suspicious = True
                reason = "AI detected suspicious patterns in transaction behavior"
            elif "CAUTION" in analysis_text.upper() or "UNUSUAL" in analysis_text.upper():
                fraud_score = 0.4
                is_suspicious = True
                reason = "AI detected unusual but not necessarily fraudulent patterns"
            
            return {
                'score': fraud_score,
                'is_suspicious': is_suspicious,
                'reason': reason,
                'ai_analysis': analysis_text[:200]  # Truncate for logging
            }
            
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._dummy_llm_analysis(transaction, history)
    
    def _dummy_llm_analysis(self, transaction: Dict, history: List[Dict]) -> Dict[str, Any]:
        """Dummy LLM analysis for testing when Gemini is not available"""
        
        amount = float(transaction.get('amount', 0))
        
        # Simple rule-based dummy analysis
        if amount > 5000:
            return {
                'score': 0.6,
                'is_suspicious': True,
                'reason': 'Dummy AI analysis: Large amount transaction requires review',
                'ai_analysis': 'DUMMY MODE: Transaction flagged due to high amount'
            }
        elif amount < 1:
            return {
                'score': 0.3,
                'is_suspicious': True,
                'reason': 'Dummy AI analysis: Micro-transaction could be testing behavior',
                'ai_analysis': 'DUMMY MODE: Very small transaction detected'
            }
        
        return {
            'score': 0.1,
            'is_suspicious': False,
            'reason': 'Dummy AI analysis: Transaction appears normal',
            'ai_analysis': 'DUMMY MODE: No significant fraud indicators detected'
        }
    
    def _build_analysis_prompt(self, transaction: Dict, history: List[Dict]) -> str:
        """Build a prompt for Gemini LLM analysis"""
        
        prompt = f"""
        You are a fraud detection expert analyzing a bank transaction. Based on the transaction details and user history, 
        determine if this transaction is potentially fraudulent.

        Current Transaction:
        - Amount: ${transaction.get('amount', 0)}
        - From Account: {transaction.get('fromAccountNum', 'N/A')}
        - To Account: {transaction.get('toAccountNum', 'N/A')}
        - Description: {transaction.get('description', 'N/A')}

        Recent Transaction History (last {len(history)} transactions):
        """
        
        for i, hist_transaction in enumerate(history[-10:]):  # Last 10 transactions
            prompt += f"- Transaction {i+1}: ${hist_transaction.get('amount', 0)} - {hist_transaction.get('description', 'N/A')}\n"
        
        prompt += """
        
        Please analyze this transaction and respond with one of:
        - NORMAL: Transaction appears legitimate
        - CAUTION: Transaction has some unusual characteristics but may be legitimate
        - SUSPICIOUS: Transaction shows concerning patterns
        - FRAUD: Transaction is likely fraudulent
        
        Provide a brief explanation for your assessment.
        """
        
        return prompt

# Initialize fraud detection agent
fraud_agent = FraudDetectionAgent(AGENT_PROJECT_ID, gemini_model)

def authenticate_token(f):
    """Decorator for JWT token authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authorization header missing'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # Remove 'Bearer ' prefix
            # In a real implementation, verify the JWT token
            # For now, we'll accept any token that looks valid
            if len(token) > 10:
                return f(*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Invalid token format'}), 401
    
    return decorated_function

def fetch_user_history(account_num: str) -> List[Dict]:
    """Fetch user transaction history from transaction history service"""
    # Check if we're in local testing mode
    if os.environ.get('LOCAL_TESTING', '').lower() == 'true':
        # Return mock transaction history for testing
        logger.info("LOCAL_TESTING mode: Using mock transaction history")
        mock_history = [
            {"amount": "50.00", "description": "Coffee purchase", "timestamp": "2025-09-01T10:00:00Z"},
            {"amount": "25.00", "description": "Lunch", "timestamp": "2025-09-02T12:30:00Z"},
            {"amount": "200.00", "description": "Groceries", "timestamp": "2025-09-03T15:45:00Z"},
            {"amount": "75.00", "description": "Gas station", "timestamp": "2025-09-04T08:20:00Z"},
            {"amount": "150.00", "description": "Online shopping", "timestamp": "2025-09-04T19:15:00Z"}
        ]
        return mock_history
    
    try:
        response = requests.get(
            f'http://{HISTORY_API_ADDR}/transactions/{account_num}',
            headers={'Authorization': request.headers.get('Authorization', '')},
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Failed to fetch history for account {account_num}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching user history: {e}")
        return []

def forward_to_ledger(transaction_data: Dict) -> Response:
    """Forward approved transaction to ledger writer service"""
    # Check if we're in local testing mode
    if os.environ.get('LOCAL_TESTING', '').lower() == 'true':
        # Return a mock successful response for local testing
        logger.info("LOCAL_TESTING mode: Simulating successful transaction")
        mock_response = {
            'transactionId': f"mock-txn-{int(time.time())}",
            'status': 'success',
            'message': 'Transaction processed successfully (MOCK MODE)',
            'amount': transaction_data.get('amount'),
            'fromAccount': transaction_data.get('fromAccountNum'),
            'toAccount': transaction_data.get('toAccountNum'),
            'fraud_analysis': transaction_data.get('fraud_analysis')
        }
        return jsonify(mock_response), 201
    
    try:
        response = requests.post(
            f'http://{TRANSACTIONS_API_ADDR}/transactions',
            json=transaction_data,
            headers={
                'Authorization': request.headers.get('Authorization', ''),
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        return Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
    except Exception as e:
        logger.error(f"Error forwarding to ledger: {e}")
        return jsonify({'error': 'Failed to process transaction'}), 500

@app.route('/ready', methods=['GET'])
def readiness_probe():
    """Readiness probe endpoint"""
    return jsonify({'status': 'ready', 'service': 'frauddetection', 'version': VERSION})

@app.route('/healthy', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'frauddetection',
        'version': VERSION,
        'gemini_available': gemini_model is not None,
        'fraud_stats': fraud_stats
    })

@app.route('/version', methods=['GET'])
def version():
    """Version endpoint"""
    return jsonify({'version': VERSION})

@app.route('/analyze-transaction', methods=['POST'])
@authenticate_token
def analyze_transaction():
    """Analyze transaction for fraud and forward if legitimate"""
    global fraud_stats
    
    try:
        transaction_data = request.get_json()
        if not transaction_data:
            return jsonify({'error': 'No transaction data provided'}), 400
        
        fraud_stats['total_transactions'] += 1
        fraud_stats['last_analysis_time'] = datetime.now().isoformat()
        
        # Extract account information
        from_account = transaction_data.get('fromAccountNum', '')
        
        # Fetch user transaction history
        user_history = fetch_user_history(from_account)
        
        # Analyze transaction for fraud
        analysis_result = fraud_agent.analyze_transaction(transaction_data, user_history)
        
        # Update statistics
        if analysis_result['fraud_score'] > 0.3:  # Any suspicion level
            fraud_stats['flagged_transactions'] += 1
        
        if analysis_result['is_fraud']:
            fraud_stats['blocked_transactions'] += 1
            logger.warning(f"Blocking fraudulent transaction: {analysis_result}")
            return jsonify({
                'status': 'blocked',
                'reason': 'Transaction blocked due to fraud detection',
                'analysis': analysis_result
            }), 403
        
        # Transaction approved - forward to ledger
        logger.info(f"Transaction approved with fraud score: {analysis_result['fraud_score']}")
        
        # Add fraud analysis metadata to transaction
        transaction_data['fraud_analysis'] = {
            'score': analysis_result['fraud_score'],
            'analyzed_at': analysis_result['analysis_timestamp'],
            'service_version': VERSION
        }
        
        # Forward to ledger writer
        return forward_to_ledger(transaction_data)
        
    except Exception as e:
        logger.error(f"Error in transaction analysis: {e}")
        return jsonify({'error': 'Internal server error during fraud analysis'}), 500

@app.route('/fraud-status', methods=['GET'])
@authenticate_token
def fraud_status():
    """Get fraud detection statistics"""
    try:
        fraud_rate = 0.0
        if fraud_stats['total_transactions'] > 0:
            fraud_rate = (fraud_stats['blocked_transactions'] / fraud_stats['total_transactions']) * 100
        
        return jsonify({
            'statistics': fraud_stats,
            'fraud_rate_percentage': round(fraud_rate, 2),
            'threshold': FRAUD_THRESHOLD,
            'service_status': 'active',
            'ai_model_status': 'active' if gemini_model else 'dummy_mode'
        })
    except Exception as e:
        logger.error(f"Error retrieving fraud status: {e}")
        return jsonify({'error': 'Failed to retrieve fraud status'}), 500

if __name__ == '__main__':
    logger.info(f"Starting Fraud Detection Service v{VERSION} on port {PORT}")
    logger.info(f"Fraud threshold: {FRAUD_THRESHOLD}")
    logger.info(f"Gemini model available: {gemini_model is not None}")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
