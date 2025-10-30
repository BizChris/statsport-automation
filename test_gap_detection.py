#!/usr/bin/env python3
"""
Test script to simulate a gap scenario and verify the daily script handles it correctly.
"""
import pandas as pd
from datetime import datetime, timedelta
import shutil
import os

def test_gap_scenario():
    """Test what happens when there's a gap in data."""
    print("🧪 Testing Gap Detection Scenario")
    print("=" * 50)
    
    # Make a backup of current CSV
    if os.path.exists("combined_mason_mount.csv"):
        shutil.copy("combined_mason_mount.csv", "combined_mason_mount_test_backup.csv")
        print("📋 Backed up current CSV file")
        
        # Load the CSV and modify the max date to simulate a gap
        df = pd.read_csv("combined_mason_mount.csv")
        
        if 'session_date' in df.columns:
            current_max = pd.to_datetime(df['session_date']).max()
            print(f"📅 Current max date in CSV: {current_max.strftime('%Y-%m-%d')}")
            
            # Simulate the CSV being 3 days old
            simulated_old_date = datetime.now() - timedelta(days=3)
            print(f"🕐 Simulating CSV with max date: {simulated_old_date.strftime('%Y-%m-%d')}")
            
            # Filter data to simulate old dataset
            df['session_date_parsed'] = pd.to_datetime(df['session_date'])
            old_df = df[df['session_date_parsed'] <= simulated_old_date].copy()
            old_df = old_df.drop('session_date_parsed', axis=1)
            
            # Save the simulated old CSV
            old_df.to_csv("combined_mason_mount_simulated.csv", index=False)
            print(f"💾 Created simulated old CSV with {len(old_df)} records")
            
            # Test what the daily script would extract
            print(f"\n🔍 Testing daily script date detection...")
            os.system("./daily_extract.sh")
            
        else:
            print("❌ No session_date column found in CSV")
    else:
        print("❌ No combined_mason_mount.csv found")

def cleanup_test():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    # Remove test files
    test_files = ["combined_mason_mount_simulated.csv", "combined_mason_mount_backup.csv"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"🗑️  Removed {file}")
    
    # Restore original if backup exists
    if os.path.exists("combined_mason_mount_test_backup.csv"):
        shutil.move("combined_mason_mount_test_backup.csv", "combined_mason_mount.csv")
        print("♻️  Restored original CSV file")

if __name__ == "__main__":
    test_gap_scenario()
    print(f"\n📊 Check the logs to see the date range that was extracted:")
    print(f"tail -5 /tmp/statsports_cron.log")
    
    input("\nPress Enter to clean up test files...")
    cleanup_test()
    print("✅ Test complete!")