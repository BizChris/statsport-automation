#!/usr/bin/env python3
"""
Upload Mason Mount CSV to OneDrive using Microsoft Graph API.
Requires authentication setup with Microsoft Azure.
"""
import os
import sys
import requests
import json
from datetime import datetime
import glob
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
TENANT_ID = os.getenv('AZURE_TENANT_ID')
CLIENT_ID = os.getenv('AZURE_CLIENT_ID')
CLIENT_SECRET = os.getenv('AZURE_CLIENT_SECRET')
USER_EMAIL = os.getenv('ONEDRIVE_USER_EMAIL', 'chris@e-d.ltd')
FOLDER_PATH = os.getenv('ONEDRIVE_FOLDER_NAME', 'Mason Mount Data')

# Check required environment variables
required_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET']
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
    print("💡 Copy .env.template to .env and fill in your Azure credentials")
    sys.exit(1)

def get_access_token():
    """Get access token using client credentials flow."""
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default',
        'grant_type': 'client_credentials'
    }
    
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"ERROR: Failed to get access token: {e}")
        return None

def find_latest_mason_mount_csv():
    """Find the Mason Mount CSV file."""
    # First try the standard filename
    standard_file = "combined_mason_mount.csv"
    if os.path.exists(standard_file):
        print(f"Found latest Mason Mount CSV: {standard_file}")
        return standard_file
    
    # Fallback to timestamped files if standard doesn't exist
    pattern = "combined_mason_mount_*.csv"
    files = glob.glob(pattern)
    
    if not files:
        print("No Mason Mount CSV files found!")
        return None
    
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    latest_file = files[0]
    
    print(f"Found latest Mason Mount CSV: {latest_file}")
    return latest_file

def upload_to_onedrive(file_path, access_token):
    """Upload file to OneDrive using Microsoft Graph API."""
    
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    
    print(f"Uploading {filename} ({file_size:,} bytes) to OneDrive...")
    
    # Graph API endpoint for uploading to user's OneDrive
    upload_url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/drive/root:/{FOLDER_PATH}/{filename}:/content"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/octet-stream'
    }
    
    try:
        with open(file_path, 'rb') as file:
            response = requests.put(upload_url, headers=headers, data=file)
            response.raise_for_status()
        
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   OneDrive ID: {result['id']}")
        print(f"   Web URL: {result.get('webUrl', 'N/A')}")
        return True
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            print("ERROR: Folder not found. Creating folder first...")
            if create_onedrive_folder(access_token):
                return upload_to_onedrive(file_path, access_token)  # Retry
        else:
            print(f"ERROR: Upload failed: {e}")
            print(f"Response: {response.text}")
        return False
    except Exception as e:
        print(f"ERROR: Upload failed: {e}")
        return False

def create_onedrive_folder(access_token):
    """Create the folder in OneDrive if it doesn't exist."""
    
    print(f"Creating folder '{FOLDER_PATH}' in OneDrive...")
    
    url = f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}/drive/root/children"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "name": FOLDER_PATH,
        "folder": {}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Folder created successfully!")
        print(f"   Folder ID: {result['id']}")
        return True
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 409:
            print("Folder already exists - continuing...")
            return True
        else:
            print(f"ERROR: Failed to create folder: {e}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to create folder: {e}")
        return False

def main():
    """Main upload function."""
    print("STATSports OneDrive Uploader")
    print("=" * 40)
    
    # Check if configuration is set up
    if TENANT_ID == "your-tenant-id" or CLIENT_ID == "your-client-id":
        print("❌ ERROR: OneDrive configuration not set up!")
        print("\n🔧 Setup required:")
        print("1. Go to Azure Portal (portal.azure.com)")
        print("2. Create an App Registration")
        print("3. Get Tenant ID, Client ID, and Client Secret")
        print("4. Grant Microsoft Graph permissions")
        print("5. Update this script with your credentials")
        print("\n📖 See setup instructions below...")
        print_setup_instructions()
        return
    
    # Find latest Mason Mount CSV
    csv_file = find_latest_mason_mount_csv()
    if not csv_file:
        return
    
    # Get access token
    print("🔐 Authenticating with Microsoft Graph...")
    access_token = get_access_token()
    if not access_token:
        return
    
    print("✅ Authentication successful!")
    
    # Upload file
    success = upload_to_onedrive(csv_file, access_token)
    
    if success:
        print(f"\n🎉 Upload completed successfully!")
        print(f"📁 File location: OneDrive > {FOLDER_PATH} > {os.path.basename(csv_file)}")
    else:
        print(f"\n❌ Upload failed!")

def print_setup_instructions():
    """Print detailed setup instructions."""
    print("\n" + "=" * 60)
    print("ONEDRIVE SETUP INSTRUCTIONS")
    print("=" * 60)
    print("1. Go to https://portal.azure.com")
    print("2. Navigate to 'Azure Active Directory' > 'App registrations'")
    print("3. Click 'New registration':")
    print("   - Name: 'STATSports OneDrive Uploader'")
    print("   - Supported account types: 'Single tenant'")
    print("   - Click 'Register'")
    print("\n4. Copy the following values:")
    print("   - Application (client) ID")
    print("   - Directory (tenant) ID")
    print("\n5. Go to 'Certificates & secrets':")
    print("   - Click 'New client secret'")
    print("   - Copy the secret VALUE (not ID)")
    print("\n6. Go to 'API permissions':")
    print("   - Click 'Add a permission' > 'Microsoft Graph' > 'Application permissions'")
    print("   - Add: 'Files.ReadWrite.All' and 'Sites.ReadWrite.All'")
    print("   - Click 'Grant admin consent'")
    print("\n7. Update this script:")
    print(f"   - TENANT_ID = 'your-tenant-id-here'")
    print(f"   - CLIENT_ID = 'your-client-id-here'")
    print(f"   - CLIENT_SECRET = 'your-client-secret-here'")
    print(f"   - USER_EMAIL = 'chris@e-d.ltd'")

if __name__ == "__main__":
    main()