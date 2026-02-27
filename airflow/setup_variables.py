"""
Airflow Configuration Setup for StormGuard Integration
=====================================================
Sets up required Airflow variables and connections for alert trigger DAG.

Run this script once after Airflow is initialized:
    python airflow/setup_variables.py
"""

import os
import json
from airflow.models import Variable
from airflow.exceptions import AirflowException

# Configuration
CONFIG = {
    "STORMGUARD_API_URL": os.getenv(
        "STORMGUARD_API_URL",
        "http://localhost:8000"
    ),
    "STORMGUARD_API_KEY": os.getenv(
        "STORMGUARD_API_KEY",
        ""
    ),
    "ALERT_RISK_THRESHOLD": os.getenv(
        "ALERT_RISK_THRESHOLD",
        "0.60"  # 60% risk
    ),
    "FIREBASE_CREDENTIALS_PATH": os.getenv(
        "FIREBASE_CREDENTIALS_PATH",
        "/app/firebase-credentials.json"
    ),
}

def setup_variables():
    """
    Set Airflow variables for StormGuard integration
    """
    
    print("Setting up Airflow variables for StormGuard...")
    
    for var_name, var_value in CONFIG.items():
        try:
            # Check if variable already exists
            existing = Variable.get(var_name, default_var=None)
            
            if existing is None:
                # Create new variable
                Variable.set(var_name, var_value)
                print(f"✓ Created variable: {var_name}={var_value}")
            else:
                print(f"→ Variable already exists: {var_name}={existing}")
        
        except Exception as e:
            print(f"✗ Error setting variable {var_name}: {e}")
            raise
    
    print("\n✓ All variables configured successfully!")


def get_airflow_home():
    """Get AIRFLOW_HOME directory"""
    return os.getenv("AIRFLOW_HOME", "~/airflow")


def print_configuration():
    """Print current configuration"""
    print("\n" + "=" * 60)
    print("StormGuard Airflow Configuration")
    print("=" * 60)
    
    for var_name, var_value in CONFIG.items():
        # Mask sensitive values
        if "KEY" in var_name or "TOKEN" in var_name:
            display_value = var_value[:10] + "..." if var_value else "(not set)"
        else:
            display_value = var_value
        
        print(f"{var_name:30} = {display_value}")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    print_configuration()
    setup_variables()
