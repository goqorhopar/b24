#!/usr/bin/env python3
"""
Check authorization status
"""

import os
from load_auth_data import get_auth_loader

def check_auth():
    """Check authorization status"""
    print("Meeting Bot Authorization Check")
    print("=" * 40)
    
    auth_loader = get_auth_loader()
    
    # Check files
    files_status = auth_loader.check_auth_files_exist()
    print("\nAuthorization files:")
    for file_type, exists in files_status.items():
        status = "OK" if exists else "MISSING"
        print(f"   {file_type}: {status}")
    
    # Check status
    auth_status = auth_loader.get_auth_status()
    print(f"\nAuthorization status: {auth_status}")
    
    # Check cookies
    selenium_cookies = auth_loader.load_selenium_cookies()
    if selenium_cookies:
        print(f"Cookies loaded: {len(selenium_cookies)} records")
    else:
        print("Cookies not loaded")
    
    # Check storage
    storage_data = auth_loader.load_storage_data()
    if storage_data:
        print("Storage data loaded")
    else:
        print("Storage data not loaded")
    
    print("\n" + "=" * 40)
    if all(files_status.values()):
        print("RESULT: Authorization is configured correctly!")
        print("Bot will be able to automatically login to all platforms.")
        return True
    else:
        print("RESULT: Authorization is not configured.")
        print("Run: python simple_auth.py")
        return False

if __name__ == "__main__":
    check_auth()
