#!/usr/bin/env python3
"""
End-to-end test script for AI endpoints
Tests all AI endpoints and reports issues
"""

import requests
import json
import sys
from uuid import UUID

# Configuration
BASE_URL = "http://localhost:9500"
API_PREFIX = "/api/v1/md"

# Test data
TEST_ENCOUNTER_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"  # Valid UUID format

def test_endpoint(name, method, path, data=None, files=None, params=None):
    """Test an endpoint and return results"""
    url = f"{BASE_URL}{API_PREFIX}{path}"
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    
    try:
        if method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=30)
            elif params:
                # Send as query params for POST
                response = requests.post(url, params=params, timeout=30)
            else:
                response = requests.post(url, timeout=30)
        elif method == "GET":
            response = requests.get(url, params=params, timeout=30)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅ SUCCESS")
            try:
                result = response.json()
                print(f"Response: {json.dumps(result, indent=2)[:500]}")
                return True, result
            except:
                print(f"Response: {response.text[:500]}")
                return True, response.text
        elif response.status_code == 422:
            print(f"❌ VALIDATION ERROR (422)")
            try:
                error_detail = response.json()
                print(f"Error detail: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"Response: {response.text}")
            return False, response.text
        elif response.status_code == 404:
            print(f"❌ NOT FOUND (404)")
            print(f"Response: {response.text}")
            return False, response.text
        elif response.status_code == 500:
            print(f"❌ SERVER ERROR (500)")
            print(f"Response: {response.text}")
            return False, response.text
        else:
            print(f"❌ UNEXPECTED STATUS ({response.status_code})")
            print(f"Response: {response.text}")
            return False, response.text
            
    except Exception as e:
        print(f"❌ REQUEST FAILED: {str(e)}")
        return False, str(e)

def run_all_tests():
    """Run all endpoint tests"""
    results = []
    
    # Test 1: Voice transcription (requires audio file)
    print("\n" + "="*60)
    print("TEST 1: Voice Transcription")
    print("="*60)
    
    # Create a dummy audio file for testing
    try:
        with open("/tmp/test_audio.wav", "wb") as f:
            f.write(b"RIFF" + b"\x00" * 100)  # Minimal WAV header
        
        with open("/tmp/test_audio.wav", "rb") as f:
            success, result = test_endpoint(
                "Voice Transcribe",
                "POST",
                "/voice/transcribe",
                files={"file": ("test.wav", f, "audio/wav")}
            )
            results.append(("voice/transcribe", success, result))
    except Exception as e:
        print(f"❌ Failed to create test audio: {e}")
        results.append(("voice/transcribe", False, str(e)))
    
    # Test 2: AI Suggest Questions
    print("\n" + "="*60)
    print("TEST 2: AI Suggest Questions")
    print("="*60)
    
    success, result = test_endpoint(
                "AI Suggest Questions",
                "POST",
                "/ai/suggest-questions",
                params={"encounter_id": TEST_ENCOUNTER_ID, "transcript": "Patient has fever and chest pain"}
            )
    results.append(("ai/suggest-questions", success, result))
    
    # Test 3: AI Suggest Management
    print("\n" + "="*60)
    print("TEST 3: AI Suggest Management")
    print("="*60)
    
    success, result = test_endpoint(
        "AI Suggest Management",
        "POST",
        "/ai/suggest-management",
        params={"encounter_id": TEST_ENCOUNTER_ID}
    )
    results.append(("ai/suggest-management", success, result))
    
    # Test 4: AI Suggest Exam
    print("\n" + "="*60)
    print("TEST 4: AI Suggest Exam")
    print("="*60)
    
    success, result = test_endpoint(
        "AI Suggest Exam",
        "POST",
        "/ai/suggest-exam",
        params={
            "encounter_id": TEST_ENCOUNTER_ID,
            "findings": "Patient has fever and chest pain"
        }
    )
    results.append(("ai/suggest-exam", success, result))
    
    # Test 5: Encounter Templates
    print("\n" + "="*60)
    print("TEST 5: Encounter Templates")
    print("="*60)
    
    success, result = test_endpoint(
        "Save Encounter Template",
        "POST",
        "/encounter-templates",
        params={
            "encounter_id": TEST_ENCOUNTER_ID,
            "prompt_template": "You are a doctor. Provide key insights."
        }
    )
    results.append(("encounter-templates", success, result))
    
    # Test 6: Generate Document
    print("\n" + "="*60)
    print("TEST 6: Generate Document")
    print("="*60)
    
    success, result = test_endpoint(
        "Generate Document",
        "POST",
        f"/encounters/{TEST_ENCOUNTER_ID}/generate-document",
        params={"title": "Clinical Summary"}
    )
    results.append(("generate-document", success, result))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, success, result in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
        if not success:
            failed += 1
        else:
            passed += 1
    
    print(f"\nTotal: {passed} passed, {failed} failed")
    
    return failed == 0

if __name__ == "__main__":
    print("AI Endpoints Test Script")
    print(f"Base URL: {BASE_URL}")
    print(f"API Prefix: {API_PREFIX}")
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
