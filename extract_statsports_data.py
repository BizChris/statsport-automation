#!/usr/bin/env python3
"""
Streamlined STATSports data extraction script.
Pulls full data directly with smart day->hour fallback:
- Tries full day first with normal timeout
- If day fails, does quick 10s probe to check if data exists
- Only attempts hourly fallback if data is detected
- Skips empty days entirely to avoid wasting time
"""
import json
import pandas as pd
from datetime import datetime, timedelta
from statsports_client import StatsportsClient
import time
import sys
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# Base names (will be namespaced per run inside runs/<run_id>/)
CHECKPOINT_FILE_NAME = "checkpoint.json"
PROGRESS_SESSIONS_NAME = "progress_sessions.jsonl"
PROGRESS_PLAYERS_NAME = "progress_players.jsonl"

def get_timestamp():
    """Get current timestamp for logging."""
    return datetime.now().strftime("%H:%M:%S")

# ---------------- Incremental Persistence Helpers ---------------- #

def _safe_read_json(path: str, default):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return default

def load_incremental_progress(range_start: datetime, range_end: datetime, run_dir: str):
    """Load previously saved per-day progress for SAME run directory if resuming.
    Returns: (processed_dates_set, all_sessions_list, all_player_details_dict)."""
    processed_dates = set()
    all_sessions: List[Dict[str, Any]] = []
    all_player_details: Dict[str, Any] = {}

    checkpoint_path = os.path.join(run_dir, CHECKPOINT_FILE_NAME)
    progress_sessions_path = os.path.join(run_dir, PROGRESS_SESSIONS_NAME)
    progress_players_path = os.path.join(run_dir, PROGRESS_PLAYERS_NAME)

    checkpoint = _safe_read_json(checkpoint_path, {})
    if checkpoint:
        if (checkpoint.get("range_start") == range_start.strftime('%Y-%m-%d') and
            checkpoint.get("range_end") == range_end.strftime('%Y-%m-%d')):
            processed_dates = set(checkpoint.get("processed_dates", []))
        else:
            # Different range → ignore old checkpoint
            return set(), [], {}

    # Load sessions jsonl
    if processed_dates and os.path.exists(progress_sessions_path):
        try:
            with open(progress_sessions_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        date_key = rec.get('date')
                        if date_key in processed_dates:
                            sessions = rec.get('sessions', [])
                            all_sessions.extend(sessions)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    # Load player details jsonl
    if processed_dates and os.path.exists(progress_players_path):
        try:
            with open(progress_players_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        date_key = rec.get('date')
                        if date_key in processed_dates:
                            players = rec.get('players', [])
                            all_player_details[date_key] = players
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    return processed_dates, all_sessions, all_player_details

def append_day_progress(date_key: str, sessions: List[Dict[str, Any]], players: List[Dict[str, Any]], run_dir: str):
    """Append one day's sessions & player details to run-local jsonl progress files."""
    progress_sessions_path = os.path.join(run_dir, PROGRESS_SESSIONS_NAME)
    progress_players_path = os.path.join(run_dir, PROGRESS_PLAYERS_NAME)
    try:
        with open(progress_sessions_path, 'a') as f:
            f.write(json.dumps({"date": date_key, "sessions": sessions}) + "\n")
    except Exception as e:
        print(f"[WARN] Failed to append sessions for {date_key}: {e}")
    try:
        with open(progress_players_path, 'a') as f:
            f.write(json.dumps({"date": date_key, "players": players}) + "\n")
    except Exception as e:
        print(f"[WARN] Failed to append players for {date_key}: {e}")

def update_checkpoint(range_start: datetime, range_end: datetime, processed_dates: List[str], total_sessions: int, run_dir: str):
    data = {
        "range_start": range_start.strftime('%Y-%m-%d'),
        "range_end": range_end.strftime('%Y-%m-%d'),
        "processed_dates": processed_dates,
        "total_sessions": total_sessions,
        "last_updated": datetime.utcnow().isoformat() + 'Z'
    }
    try:
        checkpoint_path = os.path.join(run_dir, CHECKPOINT_FILE_NAME)
        with open(checkpoint_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write checkpoint: {e}")

def get_date_ranges(start_date, end_date, period_type="day"):
    """Generate date ranges (daily or hourly)."""
    ranges = []
    current = start_date
    
    if period_type == "day":
        delta = timedelta(days=1)
    elif period_type == "hour":
        delta = timedelta(hours=1)
    
    while current <= end_date:
        period_end = min(current + delta - timedelta(seconds=1), end_date)
        ranges.append((current, period_end))
        current = period_end + timedelta(seconds=1)
    
    return ranges

def format_date_for_api(date):
    """Format date for API call."""
    return date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

def get_full_sessions(client, start_date, end_date):
    """Get full session data for a date range."""
    payload = {
        "thirdPartyApiId": client.api_key,
        "sessionStartDate": format_date_for_api(start_date),
        "sessionEndDate": format_date_for_api(end_date)
    }
    
    try:
        result = client.post("/thirdPartyData/getFullSessionsByDateRange", json=payload)
        return result if result else []
    except Exception as e:
        print(f"Failed to get sessions for {start_date.date()} to {end_date.date()}: {e}")
        return None

def get_player_details(client, session_date):
    """Get player details for a specific session date."""
    payload = {
        "thirdPartyApiId": client.api_key,
        "sessionDate": session_date
    }
    
    try:
        result = client.post("/thirdPartyData/getPlayerDetails", json=payload)
        return result if result else []
    except Exception as e:
        print(f"Failed to get player details for {session_date}: {e}")
        return []

def has_data_for_day(client, date_str):
    """Quick check if day has any data using minimal timeout"""
    print(f"  Probing {date_str} for data (quick check)...")
    
    # Store original timeout
    original_timeout = getattr(client, 'timeout', 60)
    discovery_timeout = int(os.getenv('STATSPORTS_DISCOVERY_TIMEOUT_SECS', '10'))
    
    try:
        # Temporarily reduce timeout for discovery
        client.timeout = discovery_timeout
        
        # Parse date string to datetime objects for the API call
        day_start = datetime.strptime(date_str, "%Y-%m-%d")
        day_end = day_start.replace(hour=23, minute=59, second=59)
        
        response = get_full_sessions(client, day_start, day_end)
        
        # Check if we got any sessions
        has_data = response is not None and len(response) > 0
        
        if has_data:
            print(f"  ✓ Data found for {date_str}")
        else:
            print(f"  ✗ No data for {date_str}")
            
        return has_data
        
    except Exception as e:
        print(f"  ✗ Probe failed for {date_str}: {e}")
        return False
    finally:
        # Always restore original timeout
        client.timeout = original_timeout

def extract_day_with_smart_fallback(client, day_start, day_end, date_str):
    """Try day first, then smart hourly fallback only if data exists"""
    
    print(f"\n--- Processing {date_str} ---")
    
    # First attempt: try to get the full day with normal timeout
    print(f"Attempting full day extraction for {date_str}...")
    day_sessions = get_full_sessions(client, day_start, day_end)
    
    if day_sessions is not None and len(day_sessions) > 0:
        print(f"✓ Full day extraction successful for {date_str} ({len(day_sessions)} sessions)")
        return day_sessions
    elif day_sessions is not None and len(day_sessions) == 0:
        print(f"✓ Full day extraction returned empty for {date_str}")
        return []
    else:
        print(f"✗ Full day extraction failed for {date_str}")
    
    # Second attempt: quick probe to see if ANY data exists
    if not has_data_for_day(client, date_str):
        print(f"No data detected for {date_str} - skipping hourly attempts")
        return []
    
    # Third attempt: data exists but day-level failed, try hourly
    print(f"Data exists for {date_str} but day-level failed - trying hourly fallback...")
    
    hourly_ranges = get_date_ranges(day_start, day_end, "hour")
    all_day_sessions = []
    
    for hour_start, hour_end in hourly_ranges:
        try:
            print(f"  Trying hour {hour_start.hour}:00-{hour_start.hour}:59...")
            hour_sessions = get_full_sessions(client, hour_start, hour_end)
            
            if hour_sessions is not None and len(hour_sessions) > 0:
                print(f"    ✓ Found {len(hour_sessions)} sessions in hour {hour_start.hour}")
                all_day_sessions.extend(hour_sessions)
            elif hour_sessions is not None:
                # Empty response is fine, just no data for this hour
                pass
            else:
                print(f"    ✗ Hour {hour_start.hour} API error")
                
        except Exception as e:
            print(f"    ✗ Hour {hour_start.hour} failed: {e}")
            continue
        
        # Small delay between hours to be nice to the API
        time.sleep(0.2)
    
    print(f"Hourly fallback complete for {date_str}: {len(all_day_sessions)} total sessions")
    return all_day_sessions

def extract_all_data_directly(client, start_date, end_date, run_dir: str, resume: bool = True):
    """Extract all data with day->hour fallback and save incrementally inside run directory."""
    print("Extracting (day->hour) with incremental per-run persistence...")
    processed_dates, all_sessions, all_player_details = (set(), [], {})
    if resume:
        processed_dates, all_sessions_loaded, all_player_details_loaded = load_incremental_progress(start_date, end_date, run_dir)
        if processed_dates:
            print(f"Resume detected: {len(processed_dates)} days already processed in this run.")
            all_sessions = all_sessions_loaded
            all_player_details = all_player_details_loaded

    daily_ranges = get_date_ranges(start_date, end_date, "day")
    total_days = len(daily_ranges)

    for i, (day_start, day_end) in enumerate(daily_ranges):
        date_str = day_start.strftime('%Y-%m-%d')
        date_key_full = date_str + "T00:00:00Z"
        if date_str in processed_dates:
            print(f"[{get_timestamp()}] Day {i+1}/{total_days}: {date_str} (skipped - already processed)")
            continue

        start_time = time.time()
        print(f"[{get_timestamp()}] Day {i+1}/{total_days}: {date_str}")

        # Use smart fallback strategy
        day_sessions = extract_day_with_smart_fallback(client, day_start, day_end, date_str)
        player_details_for_day: List[Dict[str, Any]] = []

        # Log final result for this day
        if day_sessions:
            print(f"Final result: {len(day_sessions)} sessions for {date_str}")
        else:
            print(f"Final result: No sessions for {date_str}")

        # Deduplicate sessions for the day (by sessionDetails signature)
        if day_sessions:
            dedup = []
            seen = set()
            for s in day_sessions:
                sig = json.dumps(s.get("sessionDetails", {}), sort_keys=True)
                if sig not in seen:
                    seen.add(sig)
                    dedup.append(s)
            if len(dedup) != len(day_sessions):
                print(f"Deduplicated {len(day_sessions)-len(dedup)} duplicate sessions")
            day_sessions = dedup

        # Fetch player details only if we had sessions
        if day_sessions:
            player_details = get_player_details(client, date_key_full)
            if player_details:
                player_details_for_day = player_details
                all_player_details[date_key_full] = player_details_for_day
                print(f"  + {len(player_details_for_day)} player details")

        # Merge into global collections
        if day_sessions:
            all_sessions.extend(day_sessions)

        # Persist this day immediately
        append_day_progress(date_key_full, day_sessions if day_sessions else [], player_details_for_day, run_dir)
        processed_dates.add(date_str)
        update_checkpoint(start_date, end_date, sorted(list(processed_dates)), len(all_sessions), run_dir)

        # Show timing for this day
        day_time = time.time() - start_time
        print(f"Day {date_str} completed in {day_time:.1f}s")
        time.sleep(0.5)

    print(f"\nExtraction complete: {len(all_sessions)} total sessions across {len(processed_dates)} days.")
    return all_sessions, all_player_details


## Removed advanced snapshot/merge logic for simplicity per user request

def flatten_to_csv(sessions_data, player_details_data):
    """Convert nested JSON data to flat CSV format."""
    print("Converting to CSV format...")
    
    rows = []
    
    for session in sessions_data:
        session_info = session.get("sessionDetails", {})
        session_date = session_info.get("sessionDate")
        session_players = session.get("sessionPlayers", [])
        
        # Get player lookup for this session date
        player_lookup = {}
        if session_date in player_details_data:
            for player in player_details_data[session_date]:
                custom_id = player.get("customPlayerId")
                if custom_id:
                    player_lookup[custom_id] = player
        
        for session_player in session_players:
            player_info = session_player.get("playerDetails", {})
            drills = session_player.get("drills", [])
            
            # Get enriched player data
            enriched_player = player_info.copy()
            custom_id = player_info.get("customPlayerId")
            if custom_id and custom_id in player_lookup:
                enriched_player.update(player_lookup[custom_id])
            
            for drill in drills:
                drill_kpi = drill.get("drillKpi", {})
                
                # Create flat row
                row = {
                    # Session data
                    "session_date": session_date,
                    "session_start_time": session_info.get("startTime"),
                    "session_end_time": session_info.get("endTime"),
                    "session_type": session_info.get("sessionType"),
                    "squad_id": session_info.get("squadId"),
                    
                    # Player data
                    "player_id": session_player.get("id"),
                    "player_display_name": enriched_player.get("displayName"),
                    "player_first_name": enriched_player.get("firstName"),
                    "player_last_name": enriched_player.get("lastName"),
                    "player_custom_id": enriched_player.get("customPlayerId"),
                    "player_squad": enriched_player.get("activeSquadName"),
                    "player_gender": enriched_player.get("gender"),
                    "player_dob": enriched_player.get("dateOfBirth"),
                    
                    # Drill data
                    "drill_id": drill.get("id"),
                    "drill_name": drill.get("drillName"),
                    "drill_start_time": drill.get("startTime"),
                    "drill_end_time": drill.get("endTime"),
                }
                
                # Add all KPI metrics
                for kpi_name, kpi_value in drill_kpi.items():
                    if kpi_name != "customMetrics":
                        row[f"kpi_{kpi_name}"] = kpi_value
                
                # Add custom metrics
                custom_metrics = drill_kpi.get("customMetrics", {})
                for metric_name, metric_value in custom_metrics.items():
                    safe_name = metric_name.replace(" ", "_").replace("(", "").replace(")", "").lower()
                    row[f"custom_{safe_name}"] = metric_value
                
                rows.append(row)
    
    df = pd.DataFrame(rows)
    print(f"CSV conversion complete: {len(df)} rows with {len(df.columns)} columns")
    return df

def main():
    if len(sys.argv) != 3:
        print("Usage: python extract_statsports_data.py YYYY-MM-DD YYYY-MM-DD")
        sys.exit(1)

    try:
        start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d")
    except ValueError:
        print("Dates must be YYYY-MM-DD")
        sys.exit(1)
    if end_date < start_date:
        print("End date before start date")
        sys.exit(1)

    run_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    run_dir = os.path.join('runs', run_id)
    os.makedirs(run_dir, exist_ok=True)

    # Initialize progress artifacts so the run folder is never empty mid-run
    try:
        open(os.path.join(run_dir, PROGRESS_SESSIONS_NAME), 'a').close()
        open(os.path.join(run_dir, PROGRESS_PLAYERS_NAME), 'a').close()
        update_checkpoint(start_date, end_date, [], 0, run_dir)
    except Exception as e:
        print(f"[WARN] Failed to initialize progress files: {e}")
    
    print(f"STATSports Streamlined Data Extraction (simple mode)")
    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Strategy: Day->Hour fallback, per-run folder with timestamp")
    print(f"Run ID: {run_id}")
    print(f"Run folder: {run_dir}")
    print()
    
    # Initialize client
    client = StatsportsClient()
    
    # Always run extraction (now safe & incremental). Later we compile final JSON snapshots.
    all_sessions, all_player_details = extract_all_data_directly(client, start_date, end_date, run_dir=run_dir, resume=True)
    
    # Write final JSON artifacts
    sessions_json_path = os.path.join(run_dir, f"sessions_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json")
    players_json_path = os.path.join(run_dir, f"players_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json")
    try:
        with open(sessions_json_path, 'w') as f:
            json.dump(all_sessions, f, indent=2)
        with open(players_json_path, 'w') as f:
            json.dump(all_player_details, f, indent=2)
        print(f"Sessions JSON: {sessions_json_path}")
        print(f"Players JSON:  {players_json_path}")
    except Exception as e:
        print(f"[WARN] Failed writing final JSON artifacts: {e}")

    # Convert to CSV
    df = flatten_to_csv(all_sessions, all_player_details)
    
    # Save final CSV
    output_filename = os.path.join(run_dir, f"statsports_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv")
    df.to_csv(output_filename, index=False)
    
    print(f"Final CSV saved as: {output_filename}")
    
    # Clean up progress files now that we have final consolidated files
    progress_sessions_path = os.path.join(run_dir, PROGRESS_SESSIONS_NAME)
    progress_players_path = os.path.join(run_dir, PROGRESS_PLAYERS_NAME)
    try:
        if os.path.exists(progress_sessions_path):
            os.remove(progress_sessions_path)
        if os.path.exists(progress_players_path):
            os.remove(progress_players_path)
        print("Cleaned up progress files")
    except Exception as e:
        print(f"[WARN] Failed to clean up progress files: {e}")
    
    print(f"Data summary:")
    print(f"  Total rows: {len(df)}")
    if len(df) > 0 and 'session_date' in df.columns:
        print(f"  Date range: {df['session_date'].min()} to {df['session_date'].max()}")
        print(f"  Unique players: {df['player_display_name'].nunique()}")
        print(f"  Unique sessions: {df['session_date'].nunique()}")
    elif len(df) == 0:
        print(f"  No data extracted for this date range")
    else:
        print(f"  {len(df.columns)} columns available")
    print()
    print("Streamlined extraction complete. Run artifacts stored in run folder.")

if __name__ == "__main__":
    main()



