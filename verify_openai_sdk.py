#!/usr/bin/env python3
"""
OpenAI SDK Verification Script

Tests that the OpenAI SDK is properly installed and compatible.
Run this after deployment to verify the SDK fix.

Usage:
    python verify_openai_sdk.py
"""

import sys
import os

def verify_openai_import():
    """Verify OpenAI SDK can be imported."""
    print("=" * 60)
    print("OPENAI SDK VERIFICATION")
    print("=" * 60)
    print()
    
    try:
        import openai
        print(f"✓ OpenAI SDK imported successfully")
        print(f"  Version: {openai.__version__}")
        print()
        return True
    except ImportError as e:
        print(f"✗ Failed to import OpenAI SDK")
        print(f"  Error: {e}")
        print()
        return False

def verify_openai_client():
    """Verify OpenAI client can be instantiated."""
    try:
        from openai import OpenAI
        print(f"✓ OpenAI client class available")
        print()
        return True
    except ImportError as e:
        print(f"✗ Failed to import OpenAI client")
        print(f"  Error: {e}")
        print()
        return False

def verify_api_key():
    """Verify API key is configured."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        print(f"✓ OPENAI_API_KEY is set")
        print(f"  Key starts with: {api_key[:7]}...")
        print()
        return True
    else:
        print(f"✗ OPENAI_API_KEY is not set")
        print(f"  Set this environment variable before testing")
        print()
        return False

def verify_client_initialization():
    """Verify OpenAI client can be initialized."""
    try:
        from openai import OpenAI
        api_key = os.environ.get('OPENAI_API_KEY')
        
        if not api_key:
            print(f"⊘ Skipping client initialization (no API key)")
            print()
            return None
        
        client = OpenAI(api_key=api_key)
        print(f"✓ OpenAI client initialized successfully")
        print(f"  No 'proxies' argument error")
        print()
        return client
    except TypeError as e:
        if 'proxies' in str(e):
            print(f"✗ FAILED: Client initialization error")
            print(f"  Error: {e}")
            print(f"  This is the bug we're fixing!")
            print()
            return False
        else:
            print(f"✗ Client initialization error: {e}")
            print()
            return False
    except Exception as e:
        print(f"✗ Client initialization error: {e}")
        print()
        return False

def verify_api_call(client):
    """Verify API call works."""
    if client is None:
        print(f"⊘ Skipping API call test (no client)")
        print()
        return None
    
    if client is False:
        return False
    
    try:
        print(f"Testing API call...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'test'"}],
            max_tokens=5
        )
        
        result = response.choices[0].message.content
        print(f"✓ API call successful")
        print(f"  Response: {result}")
        print()
        return True
    except Exception as e:
        print(f"✗ API call failed: {e}")
        print()
        return False

def verify_aiservice():
    """Verify AIService class works."""
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from coaching.ai_service import AIService
        
        print(f"✓ AIService class imported")
        
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            print(f"⊘ Skipping AIService initialization (no API key)")
            print()
            return None
        
        service = AIService()
        print(f"✓ AIService initialized successfully")
        print(f"  Model: {service.model}")
        print()
        return service
    except Exception as e:
        print(f"✗ AIService error: {e}")
        print()
        return False

def main():
    """Run all verification tests."""
    results = []
    
    # Test 1: Import
    results.append(verify_openai_import())
    
    # Test 2: Client class
    results.append(verify_openai_client())
    
    # Test 3: API key
    has_key = verify_api_key()
    results.append(has_key)
    
    # Test 4: Client initialization
    client = verify_client_initialization()
    if client is not None:
        results.append(client is not False)
    
    # Test 5: API call
    if has_key and client and client is not False:
        results.append(verify_api_call(client))
    
    # Test 6: AIService
    service = verify_aiservice()
    if service is not None:
        results.append(service is not False)
    
    # Summary
    print("=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r is True)
    failed = sum(1 for r in results if r is False)
    skipped = sum(1 for r in results if r is None)
    
    print(f"Passed:  {passed}")
    print(f"Failed:  {failed}")
    print(f"Skipped: {skipped}")
    print()
    
    if failed > 0:
        print("✗ VERIFICATION FAILED")
        print()
        print("The OpenAI SDK is not working correctly.")
        print("Check the error messages above.")
        sys.exit(1)
    elif passed > 0:
        print("✓ VERIFICATION PASSED")
        print()
        print("The OpenAI SDK is working correctly.")
        if skipped > 0:
            print(f"Note: {skipped} test(s) skipped (likely missing API key)")
        sys.exit(0)
    else:
        print("⊘ VERIFICATION INCOMPLETE")
        print()
        print("Set OPENAI_API_KEY to run full verification.")
        sys.exit(0)

if __name__ == '__main__':
    main()
