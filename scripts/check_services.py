#!/usr/bin/env python3
# AIDEV-NOTE: Health check script for AI temporal services
"""
Check if all AI temporal services are running properly.
"""

import asyncio
import os
import sys
from temporalio.client import Client
from temporalio.service import ServiceClient
import requests
from datetime import datetime

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEMPORAL_HOST = os.getenv('TEMPORAL_HOST', 'localhost:7233')
TEMPORAL_UI_URL = 'http://localhost:8088'
WEB_APP_URL = 'http://localhost:8000'

async def check_temporal_server():
    """Check if Temporal server is running"""
    try:
        client = await Client.connect(TEMPORAL_HOST)
        print("✓ Temporal Server: Connected")
        return True
    except Exception as e:
        print(f"✗ Temporal Server: Failed to connect - {e}")
        return False

async def check_workers(client: Client):
    """Check which workers are registered"""
    print("\nChecking Workers:")
    task_queues = [
        ("gemini-ai-queue", "Gemini Worker"),
        ("openai-ai-queue", "OpenAI Worker"),
        ("anthropic-ai-queue", "Anthropic Worker"),
        ("ai-workflow-queue", "Workflow Worker"),
        ("document-processing-queue", "Legacy Worker")
    ]
    
    active_workers = 0
    for queue, name in task_queues:
        try:
            # Try to describe the task queue
            response = await client.workflow_service.describe_task_queue(
                namespace="default",
                task_queue={"name": queue},
                task_queue_type=1  # Activity task queue
            )
            if response.pollers:
                print(f"  ✓ {name}: Active ({len(response.pollers)} pollers)")
                active_workers += 1
            else:
                print(f"  ✗ {name}: No active pollers")
        except Exception as e:
            print(f"  ✗ {name}: Not found")
    
    return active_workers

def check_web_services():
    """Check if web services are accessible"""
    print("\nChecking Web Services:")
    
    # Check Temporal UI
    try:
        response = requests.get(TEMPORAL_UI_URL, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Temporal UI: Accessible at {TEMPORAL_UI_URL}")
        else:
            print(f"  ✗ Temporal UI: Returned status {response.status_code}")
    except Exception as e:
        print(f"  ✗ Temporal UI: Not accessible - {type(e).__name__}")
    
    # Check Web App
    try:
        response = requests.get(WEB_APP_URL, timeout=5)
        if response.status_code == 200:
            print(f"  ✓ Web App: Accessible at {WEB_APP_URL}")
        else:
            print(f"  ✗ Web App: Returned status {response.status_code}")
    except Exception as e:
        print(f"  ✗ Web App: Not accessible - {type(e).__name__}")

def check_environment():
    """Check environment variables"""
    print("\nChecking Environment Variables:")
    
    required_vars = [
        ("GEMINI_API_KEY", "Google Gemini"),
        ("OPENAI_API_KEY", "OpenAI"),
        ("ANTHROPIC_API_KEY", "Anthropic Claude")
    ]
    
    configured = 0
    for var, name in required_vars:
        value = os.getenv(var)
        if value and value != "demo_api_key":
            print(f"  ✓ {name}: Configured")
            configured += 1
        else:
            print(f"  ✗ {name}: Not configured (set {var})")
    
    return configured

async def main():
    """Main check function"""
    print(f"AI Temporal Services Health Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)
    
    # Check environment
    env_count = check_environment()
    
    # Check Temporal
    temporal_ok = await check_temporal_server()
    
    if temporal_ok:
        client = await Client.connect(TEMPORAL_HOST)
        worker_count = await check_workers(client)
    else:
        worker_count = 0
    
    # Check web services
    check_web_services()
    
    # Summary
    print("\n" + "="*50)
    print("Summary:")
    print(f"  - Environment: {env_count}/3 API keys configured")
    print(f"  - Workers: {worker_count} active")
    print(f"  - Temporal: {'Running' if temporal_ok else 'Not running'}")
    
    if env_count < 3:
        print("\n⚠️  Warning: Not all API keys are configured.")
        print("   Copy .env.example to .env and add your API keys.")
    
    if worker_count < 4:
        print("\n⚠️  Warning: Not all workers are running.")
        print("   Run 'docker-compose up -d' to start all services.")
    
    if temporal_ok and worker_count >= 4 and env_count == 3:
        print("\n✅ All services are healthy and ready!")
        return 0
    else:
        print("\n❌ Some services need attention.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)