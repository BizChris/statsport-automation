#!/usr/bin/env python3
"""
Post-processing script to combine multiple runs and filter for specific players.
Removes duplicate sessions and creates a clean combined CSV.
"""
import pandas as pd
import os
import glob
from datetime import datetime
import sys

def find_csv_files(runs_dir="runs"):
    """Find all CSV files in run directories."""
    csv_files = []
    pattern = os.path.join(runs_dir, "*/statsports_*.csv")
    files = glob.glob(pattern)
    
    for file in files:
        # Extract run info from path
        run_dir = os.path.basename(os.path.dirname(file))
        csv_files.append({
            'path': file,
            'run_dir': run_dir,
            'filename': os.path.basename(file)
        })
    
    return csv_files

def load_and_combine_csvs(csv_files):
    """Load all CSV files and combine them."""
    all_dataframes = []
    
    print(f"Found {len(csv_files)} CSV files:")
    for file_info in csv_files:
        print(f"  - {file_info['run_dir']}: {file_info['filename']}")
        
        try:
            df = pd.read_csv(file_info['path'])
            df['source_run'] = file_info['run_dir']  # Track which run it came from
            all_dataframes.append(df)
            print(f"    Loaded {len(df)} rows")
        except Exception as e:
            print(f"    ERROR loading {file_info['path']}: {e}")
    
    if not all_dataframes:
        print("No CSV files could be loaded!")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    print(f"\nCombined total: {len(combined_df)} rows")
    
    return combined_df

def remove_duplicate_sessions(df):
    """Remove duplicate sessions based on session date, drill, and player."""
    print("\nRemoving duplicate sessions...")
    
    # Create a unique identifier for each drill record
    # Using session_date, drill_id, player_custom_id as the key
    duplicate_cols = ['session_date', 'drill_id', 'player_custom_id']
    
    # Check which columns exist (some might be missing)
    available_cols = [col for col in duplicate_cols if col in df.columns]
    
    if not available_cols:
        print("WARNING: No standard deduplication columns found. Using all columns.")
        return df.drop_duplicates()
    
    print(f"Deduplicating based on: {available_cols}")
    
    before_count = len(df)
    df_deduplicated = df.drop_duplicates(subset=available_cols, keep='first')
    after_count = len(df_deduplicated)
    
    removed_count = before_count - after_count
    print(f"Removed {removed_count} duplicate records")
    print(f"Remaining: {after_count} unique records")
    
    return df_deduplicated

def filter_by_player(df, player_name):
    """Filter dataframe for specific player."""
    print(f"\nFiltering for player: '{player_name}'")
    
    # Try different player name columns
    player_columns = ['player_display_name', 'player_first_name', 'player_last_name']
    available_player_cols = [col for col in player_columns if col in df.columns]
    
    if not available_player_cols:
        print("ERROR: No player name columns found!")
        print("Available columns:", list(df.columns))
        return df
    
    print(f"Searching in columns: {available_player_cols}")
    
    # Create a case-insensitive search across all player name columns
    mask = pd.Series([False] * len(df))
    
    for col in available_player_cols:
        if col in df.columns:
            # Case-insensitive partial match
            col_mask = df[col].str.contains(player_name, case=False, na=False)
            mask = mask | col_mask
            matches = col_mask.sum()
            print(f"  {col}: {matches} matches")
    
    filtered_df = df[mask]
    print(f"\nTotal matches for '{player_name}': {len(filtered_df)} records")
    
    if len(filtered_df) > 0:
        # Show unique sessions found
        if 'session_date' in filtered_df.columns:
            unique_sessions = filtered_df['session_date'].nunique()
            date_range = f"{filtered_df['session_date'].min()} to {filtered_df['session_date'].max()}"
            print(f"Spans {unique_sessions} unique sessions from {date_range}")
    
    return filtered_df

def main():
    """Main processing function."""
    player_name = "mason mount"  # Default player
    
    # Allow player name to be passed as argument
    if len(sys.argv) > 1:
        player_name = " ".join(sys.argv[1:])
    
    print(f"STATSports Run Combiner - Filtering for: '{player_name}'")
    print("=" * 60)
    
    # Find all CSV files
    csv_files = find_csv_files()
    if not csv_files:
        print("No CSV files found in runs/ directory!")
        return
    
    # Load and combine all CSV files
    combined_df = load_and_combine_csvs(csv_files)
    if combined_df is None:
        return
    
    # Remove duplicates
    deduplicated_df = remove_duplicate_sessions(combined_df)
    
    # Filter for specific player
    player_df = filter_by_player(deduplicated_df, player_name)
    
    if len(player_df) == 0:
        print(f"\nNo records found for player: '{player_name}'")
        print("\nAvailable players (first 20):")
        if 'player_display_name' in deduplicated_df.columns:
            unique_players = deduplicated_df['player_display_name'].dropna().unique()
            for i, player in enumerate(sorted(unique_players)[:20]):
                print(f"  - {player}")
            if len(unique_players) > 20:
                print(f"  ... and {len(unique_players) - 20} more")
        return
    
    # Save combined result
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_player_name = player_name.replace(' ', '_').replace('/', '_')
    output_file = f"combined_{safe_player_name}_{timestamp}.csv"
    
    player_df.to_csv(output_file, index=False)
    
    print(f"\n" + "=" * 60)
    print(f"✅ Combined data saved to: {output_file}")
    print(f"📊 Final dataset:")
    print(f"   - {len(player_df)} total records")
    print(f"   - {len(player_df.columns)} columns")
    if 'session_date' in player_df.columns:
        print(f"   - {player_df['session_date'].nunique()} unique sessions")
        print(f"   - Date range: {player_df['session_date'].min()} to {player_df['session_date'].max()}")
    
    # Show source run breakdown
    if 'source_run' in player_df.columns:
        print(f"\n📁 Records by source run:")
        source_counts = player_df['source_run'].value_counts()
        for run, count in source_counts.items():
            print(f"   - {run}: {count} records")

if __name__ == "__main__":
    main()