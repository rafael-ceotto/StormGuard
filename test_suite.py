#!/usr/bin/env python3
"""
StormGuard Integration Test Suite

Tests all components of the StormGuard platform including:
- API endpoints
- Database connectivity
- Authentication
- Chat functionality
- Alert system
- Airflow integration
- Firebase notifications

Usage:
    python test_suite.py --full          # Run all tests
    python test_suite.py --api           # Test API only
    python test_suite.py --airflow       # Test Airflow integration
    python test_suite.py --database      # Test database only
    python test_suite.py --verbose       # Show detailed output
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration: float = 0.0

class StormGuardTestSuite:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.api_url = os.getenv("STORMGUARD_API_URL", "http://localhost:8000")
        self.api_key = os.getenv("STORMGUARD_API_KEY", "test-key")
        self.db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/stormguard")
        self.test_user_email = "test@stormguard.local"
        self.test_user_password = "TestPassword123!"
        self.auth_token = None
        
    def log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        levels = {
            "INFO": f"{Colors.BLUE}ℹ{Colors.RESET}",
            "SUCCESS": f"{Colors.GREEN}✓{Colors.RESET}",
            "ERROR": f"{Colors.RED}✗{Colors.RESET}",
            "WARN": f"{Colors.YELLOW}⚠{Colors.RESET}"
        }
        icon = levels.get(level, "•")
        print(f"[{timestamp}] {icon} {message}")
    
    def section(self, title: str):
        """Print a section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")
    
    def add_result(self, name: str, passed: bool, message: str, duration: float = 0.0):
        """Record test result"""
        self.results.append(TestResult(name, passed, message, duration))
        
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if passed else f"{Colors.RED}FAIL{Colors.RESET}"
        self.log(f"{name}: {status} ({duration:.2f}s) - {message}")
    
    # ==================== API Tests ====================
    
    def test_api_health(self) -> bool:
        """Test API health endpoint"""
        start = time.time()
        try:
            resp = requests.get(f"{self.api_url}/api/v1/health", timeout=5)
            duration = time.time() - start
            
            if resp.status_code == 200:
                self.add_result("API Health Check", True, f"API is responding", duration)
                return True
            else:
                self.add_result("API Health Check", False, f"Status code: {resp.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("API Health Check", False, f"Connection error: {str(e)}", duration)
            return False
    
    def test_user_registration(self) -> bool:
        """Test user registration"""
        start = time.time()
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "full_name": "Test User",
                "phone": "+1234567890",
                "location": "New York, NY",
                "timezone": "America/New_York"
            }
            
            resp = requests.post(
                f"{self.api_url}/api/v1/auth/register",
                json=payload,
                timeout=5
            )
            duration = time.time() - start
            
            if resp.status_code in [200, 201]:
                self.add_result("User Registration", True, "User registered successfully", duration)
                return True
            elif resp.status_code == 409:
                self.add_result("User Registration", True, "User already exists", duration)
                return True
            else:
                self.add_result("User Registration", False, f"Status: {resp.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("User Registration", False, f"Error: {str(e)}", duration)
            return False
    
    def test_user_login(self) -> bool:
        """Test user login and token generation"""
        start = time.time()
        try:
            payload = {
                "username": self.test_user_email,
                "password": self.test_user_password
            }
            
            resp = requests.post(
                f"{self.api_url}/api/v1/auth/login",
                data=payload,
                timeout=5
            )
            duration = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                self.auth_token = data.get("access_token")
                self.add_result("User Login", True, "Authentication successful", duration)
                return True
            else:
                self.add_result("User Login", False, f"Status: {resp.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("User Login", False, f"Error: {str(e)}", duration)
            return False
    
    def test_user_profile(self) -> bool:
        """Test user profile retrieval"""
        if not self.auth_token:
            self.add_result("User Profile", False, "No auth token", 0)
            return False
        
        start = time.time()
        try:
            resp = requests.get(
                f"{self.api_url}/api/v1/users/me",
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )
            duration = time.time() - start
            
            if resp.status_code == 200:
                self.add_result("User Profile", True, "Profile retrieved", duration)
                return True
            else:
                self.add_result("User Profile", False, f"Status: {resp.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("User Profile", False, f"Error: {str(e)}", duration)
            return False
    
    def test_alert_send(self) -> bool:
        """Test alert sending endpoint"""
        if not self.auth_token:
            self.add_result("Alert Send", False, "No auth token", 0)
            return False
        
        start = time.time()
        try:
            payload = {
                "user_ids": ["test-user-1", "test-user-2"],
                "disaster_type": "hurricane",
                "title": "Test Hurricane Alert",
                "message": "This is a test alert",
                "risk_level": "HIGH",
                "risk_score": 0.85,
                "latitude": 40.7128,
                "longitude": -74.0060,
                "radius_km": 150
            }
            
            resp = requests.post(
                f"{self.api_url}/api/v1/alerts/send",
                json=payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=5
            )
            duration = time.time() - start
            
            if resp.status_code in [200, 201]:
                self.add_result("Alert Send", True, "Alerts sent successfully", duration)
                return True
            else:
                self.add_result("Alert Send", False, f"Status: {resp.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("Alert Send", False, f"Error: {str(e)}", duration)
            return False
    
    def test_chat_message(self) -> bool:
        """Test chat message endpoint"""
        if not self.auth_token:
            self.add_result("Chat Message", False, "No auth token", 0)
            return False
        
        start = time.time()
        try:
            payload = {
                "message": "What should I do in a hurricane?"
            }
            
            resp = requests.post(
                f"{self.api_url}/api/v1/chat/message",
                json=payload,
                headers={"Authorization": f"Bearer {self.auth_token}"},
                timeout=10
            )
            duration = time.time() - start
            
            if resp.status_code in [200, 201]:
                self.add_result("Chat Message", True, "Message processed", duration)
                return True
            else:
                self.add_result("Chat Message", False, f"Status: {resp.status_code}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("Chat Message", False, f"Error: {str(e)}", duration)
            return False
    
    # ==================== Database Tests ====================
    
    def test_database_connection(self) -> bool:
        """Test database connectivity"""
        start = time.time()
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.db_url)
            
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.scalar()
            
            duration = time.time() - start
            self.add_result("Database Connection", True, "Connected to database", duration)
            return True
        except Exception as e:
            duration = time.time() - start
            self.add_result("Database Connection", False, f"Error: {str(e)}", duration)
            return False
    
    def test_database_tables(self) -> bool:
        """Verify all required tables exist"""
        start = time.time()
        try:
            from sqlalchemy import create_engine, text, inspect
            engine = create_engine(self.db_url)
            inspector = inspect(engine)
            
            required_tables = [
                'users',
                'user_preferences',
                'alerts',
                'chat_messages',
                'alert_metrics',
                'predictions'
            ]
            
            existing_tables = inspector.get_table_names()
            missing = [t for t in required_tables if t not in existing_tables]
            
            duration = time.time() - start
            
            if not missing:
                self.add_result("Database Tables", True, f"All {len(required_tables)} tables found", duration)
                return True
            else:
                self.add_result("Database Tables", False, f"Missing: {', '.join(missing)}", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("Database Tables", False, f"Error: {str(e)}", duration)
            return False
    
    # ==================== Airflow Tests ====================
    
    def test_airflow_dag_exists(self) -> bool:
        """Check if alert_trigger_dag is registered"""
        start = time.time()
        try:
            import subprocess
            result = subprocess.run(
                ["airflow", "dags", "list", "--output", "table"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            duration = time.time() - start
            
            if "stormguard_alert_trigger" in result.stdout:
                self.add_result("Airflow DAG", True, "alert_trigger_dag is registered", duration)
                return True
            else:
                self.add_result("Airflow DAG", False, "alert_trigger_dag not found", duration)
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("Airflow DAG", False, f"Error: {str(e)}", duration)
            return False
    
    def test_airflow_variables(self) -> bool:
        """Check if Airflow variables are configured"""
        start = time.time()
        try:
            import subprocess
            result = subprocess.run(
                ["airflow", "variables", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            duration = time.time() - start
            
            required_vars = [
                "STORMGUARD_API_URL",
                "ALERT_RISK_THRESHOLD"
            ]
            
            missing = [v for v in required_vars if v not in result.stdout]
            
            if not missing:
                self.add_result("Airflow Variables", True, "All variables configured", duration)
                return True
            else:
                self.add_result(
                    "Airflow Variables",
                    False,
                    f"Missing: {', '.join(missing)}",
                    duration
                )
                return False
        except Exception as e:
            duration = time.time() - start
            self.add_result("Airflow Variables", False, f"Error: {str(e)}", duration)
            return False
    
    # ==================== Test Runners ====================
    
    def run_api_tests(self):
        """Run all API tests"""
        self.section("API Tests")
        self.test_api_health()
        self.test_user_registration()
        self.test_user_login()
        self.test_user_profile()
        self.test_alert_send()
        self.test_chat_message()
    
    def run_database_tests(self):
        """Run all database tests"""
        self.section("Database Tests")
        self.test_database_connection()
        self.test_database_tables()
    
    def run_airflow_tests(self):
        """Run all Airflow tests"""
        self.section("Airflow Tests")
        self.test_airflow_dag_exists()
        self.test_airflow_variables()
    
    def run_all_tests(self):
        """Run all tests"""
        self.run_api_tests()
        self.run_database_tests()
        self.run_airflow_tests()
    
    def print_summary(self):
        """Print test summary"""
        self.section("Test Summary")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        duration = sum(r.duration for r in self.results)
        
        print(f"{Colors.BOLD}Results:{Colors.RESET}")
        print(f"  Total:    {total}")
        print(f"  {Colors.GREEN}Passed:   {passed}{Colors.RESET}")
        print(f"  {Colors.RED}Failed:   {failed}{Colors.RESET}")
        print(f"  Duration: {duration:.2f}s")
        
        if failed > 0:
            print(f"\n{Colors.BOLD}Failed Tests:{Colors.RESET}")
            for result in self.results:
                if not result.passed:
                    print(f"  {Colors.RED}✗{Colors.RESET} {result.name}: {result.message}")
        
        print(f"\n{'=' * 60}\n")
        
        return failed == 0

def main():
    parser = argparse.ArgumentParser(description="StormGuard Integration Test Suite")
    parser.add_argument("--full", action="store_true", help="Run all tests")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--database", action="store_true", help="Run database tests only")
    parser.add_argument("--airflow", action="store_true", help="Run Airflow tests only")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    
    # Default to full test if no specific option given
    if not any([args.full, args.api, args.database, args.airflow]):
        args.full = True
    
    suite = StormGuardTestSuite(verbose=args.verbose)
    
    suite.log("Starting StormGuard Integration Test Suite", "INFO")
    suite.log(f"API URL: {suite.api_url}", "INFO")
    
    try:
        if args.full:
            suite.run_all_tests()
        else:
            if args.api:
                suite.run_api_tests()
            if args.database:
                suite.run_database_tests()
            if args.airflow:
                suite.run_airflow_tests()
        
        success = suite.print_summary()
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test suite interrupted{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Error: {str(e)}{Colors.RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
