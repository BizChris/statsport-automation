#!/usr/bin/env python3
"""
Update script to add new Mason Mount records to existing combined CSV.
Handles deduplication and maintains chronological order.
"""
import pandas as pd
import os
import sys
from datetime import datetime

def find_latest_combined_csv():
    """Find the combined Mason Mount CSV."""
    # First try the standard filename
    standard_file = "combined_mason_mount.csv"
    if os.path.exists(standard_file):
        print(f"Found existing combined CSV: {standard_file}")
        return standard_file
    
    # Fallback to timestamped files if standard doesn't exist
    import glob
    pattern = "combined_mason_mount_*.csv"
    files = glob.glob(pattern)
    
    if not files:
        print("No existing combined Mason Mount CSV found!")
        return None
    
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    latest_file = files[0]
    
    print(f"Found existing combined CSV: {latest_file}")
    return latest_file

def find_new_run_csv():
    """Find the newest run CSV file."""
    import glob
    pattern = "runs/*/statsports_*.csv"
    files = glob.glob(pattern)
    
    if not files:
        print("No run CSV files found!")
        return None
    
    # Sort by modification time, newest first
    files.sort(key=os.path.getmtime, reverse=True)
    newest_file = files[0]
    
    run_dir = os.path.basename(os.path.dirname(newest_file))
    print(f"Found newest run CSV: {run_dir}/{os.path.basename(newest_file)}")
    return newest_file

def load_existing_data(csv_file):
    """Load existing Mason Mount data."""
    print(f"Loading existing data from {csv_file}...")
    df = pd.read_csv(csv_file)
    print(f"  Existing records: {len(df)}")
    
    if 'session_date' in df.columns:
        date_range = f"{df['session_date'].min()} to {df['session_date'].max()}"
        print(f"  Date range: {date_range}")
        print(f"  Unique sessions: {df['session_date'].nunique()}")
    
    return df

def extract_mason_mount_from_new_run(csv_file):
    """Extract Mason Mount records from new run."""
    print(f"\nExtracting Mason Mount data from new run...")
    df = pd.read_csv(csv_file)
    print(f"  Total records in new run: {len(df)}")
    
    # Filter for Mason Mount (case-insensitive, partial match)
    player_columns = ['player_display_name', 'player_first_name', 'player_last_name']
    available_cols = [col for col in player_columns if col in df.columns]
    
    mask = pd.Series([False] * len(df))
    
    for col in available_cols:
        if col in df.columns:
            col_mask = df[col].str.contains('mason mount', case=False, na=False)
            mask = mask | col_mask
    
    mason_df = df[mask]
    print(f"  Mason Mount records found: {len(mason_df)}")
    
    if len(mason_df) > 0 and 'session_date' in mason_df.columns:
        unique_sessions = mason_df['session_date'].nunique()
        date_range = f"{mason_df['session_date'].min()} to {mason_df['session_date'].max()}"
        print(f"  New sessions: {unique_sessions}")
        print(f"  Date range: {date_range}")
    
    return mason_df

def combine_and_deduplicate(existing_df, new_df):
    """Combine datasets and remove duplicates."""
    print(f"\nCombining datasets...")
    
    # Add source tracking
    existing_df = existing_df.copy()
    new_df = new_df.copy()
    
    if 'source_run' not in existing_df.columns:
        existing_df['source_run'] = 'existing'
    
    # Get the run directory from the newest file
    newest_run = find_new_run_csv()
    if newest_run:
        run_dir = os.path.basename(os.path.dirname(newest_run))
        new_df['source_run'] = run_dir
    else:
        new_df['source_run'] = 'new_run'
    
    # Combine dataframes
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    print(f"  Combined total: {len(combined_df)} records")
    
    # Remove duplicates based on session_date, drill_id, player_custom_id
    duplicate_cols = ['session_date', 'drill_id', 'player_custom_id']
    available_cols = [col for col in duplicate_cols if col in combined_df.columns]
    
    if available_cols:
        print(f"  Deduplicating based on: {available_cols}")
        before_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=available_cols, keep='first')
        after_count = len(combined_df)
        removed_count = before_count - after_count
        print(f"  Removed {removed_count} duplicate records")
        print(f"  Final count: {after_count} unique records")
    
    # Sort by session date for chronological order
    if 'session_date' in combined_df.columns:
        combined_df = combined_df.sort_values('session_date').reset_index(drop=True)
        print(f"  Sorted chronologically")
    
    return combined_df

def save_updated_csv(df, original_file):
    """Save the updated CSV, overwriting the original file."""
    # Create a backup of the original file
    backup_file = original_file.replace('.csv', '_backup.csv')
    if os.path.exists(original_file):
        import shutil
        shutil.copy2(original_file, backup_file)
        print(f"📋 Backup created: {backup_file}")
    
    # Overwrite the original file with updated data
    df.to_csv(original_file, index=False)
    
    print(f"\n" + "=" * 60)
    print(f"✅ Updated data saved to: {original_file}")
    print(f"📊 Final dataset:")
    print(f"   - {len(df)} total records")
    print(f"   - {len(df.columns)} columns")
    
    if 'session_date' in df.columns:
        print(f"   - {df['session_date'].nunique()} unique sessions")
        print(f"   - Date range: {df['session_date'].min()} to {df['session_date'].max()}")
    
    # Show breakdown by source
    if 'source_run' in df.columns:
        print(f"\n📁 Records by source:")
        source_counts = df['source_run'].value_counts()
        for source, count in source_counts.items():
            print(f"   - {source}: {count} records")
    
    return original_file

def main():
    """Main update function."""
    print("STATSports Mason Mount Data Updater")
    print("=" * 60)
    
    # Find existing combined CSV
    existing_csv = find_latest_combined_csv()
    if not existing_csv:
        print("ERROR: No existing combined CSV found!")
        print("Run combine_runs.py first to create the initial combined file.")
        return
    
    # Find newest run CSV
    new_run_csv = find_new_run_csv()
    if not new_run_csv:
        print("ERROR: No new run CSV found!")
        return
    
    # Load existing data
    existing_df = load_existing_data(existing_csv)
    
    # Extract new Mason Mount data
    new_mason_df = extract_mason_mount_from_new_run(new_run_csv)
    
    if len(new_mason_df) == 0:
        print("\nNo new Mason Mount records found in latest run.")
        return
    
    # Combine and deduplicate
    final_df = combine_and_deduplicate(existing_df, new_mason_df)
    
    # Save updated file (overwrites original)
    updated_file = save_updated_csv(final_df, existing_csv)
    
    print(f"\n✅ Mason Mount dataset updated successfully!")
    print(f"📝 File updated: {updated_file}")

if __name__ == "__main__":
    main()