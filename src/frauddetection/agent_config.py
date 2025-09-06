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

"""
Agent Configuration for Fraud Detection using Google Agent Development Kit

This module provides configuration and setup for fraud detection agents
that work with Google's Agent Development Kit and Gemini LLM.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass
from google.generativeai import configure, GenerativeModel
from google.cloud import aiplatform

@dataclass
class AgentConfig:
    """Configuration for fraud detection agents"""
    project_id: str
    location: str = "us-central1"
    model_name: str = "gemini-1.5-flash"
    temperature: float = 0.1  # Low temperature for consistent results
    max_output_tokens: int = 1024
    fraud_threshold: float = 0.7
    
    # Agent behavior settings
    max_analysis_time: int = 30  # seconds
    enable_learning: bool = True
    use_historical_data: bool = True
    
    # Risk factors weights
    amount_weight: float = 0.25
    velocity_weight: float = 0.25  
    time_weight: float = 0.15
    pattern_weight: float = 0.35  # AI analysis gets highest weight

class FraudDetectionAgentManager:
    """
    Manager class for fraud detection agents using Google Agent Development Kit
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.model = None
        self.agent_client = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Google AI services"""
        try:
            # Initialize Vertex AI
            aiplatform.init(
                project=self.config.project_id,
                location=self.config.location
            )
            
            # Initialize Gemini
            api_key = os.environ.get('GEMINI_API_KEY')
            if api_key and api_key != 'dummy-api-key-for-testing':
                configure(api_key=api_key)
                self.model = GenerativeModel(
                    model_name=self.config.model_name,
                    generation_config={
                        "temperature": self.config.temperature,
                        "max_output_tokens": self.config.max_output_tokens,
                    }
                )
                print(f"Initialized Gemini model: {self.config.model_name}")
            else:
                print("Warning: Using dummy mode - no valid API key provided")
                
        except Exception as e:
            print(f"Warning: Failed to initialize AI services: {e}")
            print("Running in fallback mode")
    
    def create_fraud_detection_agent(self) -> 'FraudDetectionAgent':
        """Create a new fraud detection agent instance"""
        from main import FraudDetectionAgent  # Import here to avoid circular import
        return FraudDetectionAgent(self.config.project_id, self.model)
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for fraud detection"""
        return """
        You are an expert fraud detection AI agent for a banking system. Your role is to analyze
        financial transactions and determine their fraud risk level.
        
        Key responsibilities:
        1. Analyze transaction patterns for anomalies
        2. Consider user spending history and behavior
        3. Evaluate transaction timing, amounts, and frequency
        4. Provide risk scores between 0.0 (safe) and 1.0 (definite fraud)
        5. Explain your reasoning clearly and concisely
        
        Risk factors to consider:
        - Unusual transaction amounts (very high or suspicious round numbers)
        - High transaction frequency (velocity attacks)
        - Transactions at unusual times (late night/early morning)
        - Deviation from normal spending patterns
        - Geographic inconsistencies (if available)
        - Account age and transaction history
        
        Response format:
        - Risk Score: [0.0-1.0]
        - Risk Level: [LOW/MEDIUM/HIGH/CRITICAL]
        - Primary Concerns: [list main risk factors]
        - Recommendation: [APPROVE/REVIEW/BLOCK]
        - Explanation: [brief reasoning]
        
        Be conservative but not overly restrictive. False positives inconvenience customers,
        but false negatives can result in financial losses.
        """
    
    def update_model_parameters(self, **kwargs):
        """Update model parameters dynamically"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                print(f"Updated {key} to {value}")

# Default configurations for different environments
DEVELOPMENT_CONFIG = AgentConfig(
    project_id=os.environ.get('AGENT_PROJECT_ID', 'bank-of-anthos-dev'),
    fraud_threshold=0.5,  # Lower threshold for testing
    temperature=0.2,  # Slightly higher for variety in dev
    enable_learning=True
)

STAGING_CONFIG = AgentConfig(
    project_id=os.environ.get('AGENT_PROJECT_ID', 'bank-of-anthos-staging'),
    fraud_threshold=0.6,  # Medium threshold
    temperature=0.1,
    enable_learning=True
)

PRODUCTION_CONFIG = AgentConfig(
    project_id=os.environ.get('AGENT_PROJECT_ID', 'bank-of-anthos-prod'),
    fraud_threshold=0.7,  # Higher threshold for production
    temperature=0.05,  # Very low for consistency
    enable_learning=False  # Disable learning in production for stability
)

def get_config_for_environment(env: str = None) -> AgentConfig:
    """Get configuration based on environment"""
    env = env or os.environ.get('ENV', 'development').lower()
    
    config_map = {
        'development': DEVELOPMENT_CONFIG,
        'dev': DEVELOPMENT_CONFIG,
        'staging': STAGING_CONFIG,
        'stage': STAGING_CONFIG,
        'production': PRODUCTION_CONFIG,
        'prod': PRODUCTION_CONFIG
    }
    
    return config_map.get(env, DEVELOPMENT_CONFIG)

# Example usage patterns for different fraud scenarios
FRAUD_SCENARIOS = {
    'velocity_attack': {
        'description': 'Multiple rapid transactions in short time',
        'pattern': 'High frequency, similar amounts',
        'risk_score': 0.8
    },
    'amount_anomaly': {
        'description': 'Transaction amount significantly different from normal',
        'pattern': 'Amount >> usual spending or suspicious round number',
        'risk_score': 0.6
    },
    'time_anomaly': {
        'description': 'Transaction at unusual time',
        'pattern': 'Late night/early morning transactions',
        'risk_score': 0.4
    },
    'first_transaction': {
        'description': 'First transaction for new account',
        'pattern': 'No transaction history',
        'risk_score': 0.3
    },
    'card_testing': {
        'description': 'Small amounts to test stolen card',
        'pattern': 'Very small amounts (< $5)',
        'risk_score': 0.5
    }
}

if __name__ == "__main__":
    # Example initialization
    config = get_config_for_environment()
    manager = FraudDetectionAgentManager(config)
    agent = manager.create_fraud_detection_agent()
    print(f"Fraud detection agent initialized with threshold: {config.fraud_threshold}")
