#!/usr/bin/env python3
"""
Test script for Computer Use ADK Agent

This script tests the basic functionality of the Computer Use ADK Agent
and verifies the connection to the Computer Use API.
"""

import sys
import os
import requests
sys.path.append('computer_use_agent')

from computer_use_agent.agent import execute_computer_task

def test_api_connection():
    """Test connection to Computer Use API"""
    print("🔍 Testing Computer Use API connection...")
    try:
        response = requests.get("http://localhost:7888/health")
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Computer Use API is running!")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Platform: {health_data.get('platform', 'unknown')}")
            return True
        else:
            print(f"❌ API responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Computer Use API is not running")
        print("   Please start it with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False

def test_basic_task():
    """Test basic computer task execution"""
    print("\n🔍 Testing basic task execution...")
    result = execute_computer_task("Please take a screenshot and describe what you see on the screen.")
    
    if result["status"] == "success":
        print("✅ Basic task execution successful!")
        print(f"   Task completed: {result['task_completed']}")
        print(f"   Session ID: {result['session_id']}")
        print(f"   Result preview: {result['result'][:100]}...")
        return True
    else:
        print("❌ Basic task execution failed:")
        print(f"   {result['error_message']}")
        return False

def test_complex_task():
    """Test complex multi-step task"""
    print("\n🔍 Testing complex task execution...")
    result = execute_computer_task(
        "First take a screenshot to see the current state, then open Calculator application if possible."
    )
    
    if result["status"] == "success":
        print("✅ Complex task execution successful!")
        print(f"   Task completed: {result['task_completed']}")
        print(f"   Result preview: {result['result'][:100]}...")
        return True
    else:
        print("❌ Complex task execution failed:")
        print(f"   {result['error_message']}")
        return False

def main():
    print("🚀 Computer Use ADK Agent Test Suite")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: API Connection
    if test_api_connection():
        tests_passed += 1
    
    # Test 2: Basic Task
    if test_basic_task():
        tests_passed += 1
    
    # Test 3: Complex Task
    if test_complex_task():
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The Computer Use ADK Agent is ready to use.")
        print("\nNext steps:")
        print("1. Get a Google AI Studio API key")
        print("2. Update computer_use_agent/.env with your API key")
        print("3. Run: adk web")
        print("4. Open http://localhost:8000 and select 'computer_use_agent'")
        print("\nExample commands to try:")
        print("• 'Take a screenshot and tell me what's on screen'")
        print("• 'Open Calculator and compute 25 * 17'")
        print("• 'Search Google for Python tutorials'")
        print("• 'Create a text file called notes.txt on the desktop'")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        
        if tests_passed == 0:
            print("\nTroubleshooting:")
            print("- Make sure the Computer Use API is running: python app.py")
            print("- Verify it's accessible at http://localhost:7888")
            print("- Check AWS Bedrock configuration for Claude 3.7")

if __name__ == "__main__":
    main() 