#!/bin/bash
# Daily STATSports extraction script for cron
#!/bin/bash
# Daily STATSports extraction script for cron
# Finds the latest session date in existing data and extracts from there to yesterday
# This ensures no gaps if Mac was off for multiple days

# Change to the script directory
cd /Users/christopherdickson/Documents/GitHub/statsports_starter

# Start logging
/bin/echo "$(/bin/date): ==================== DAILY EXTRACTION START ====================" >> /tmp/statsports_cron.log

# Set Python executable from virtual environment
PYTHON_EXEC="/Users/christopherdickson/Documents/GitHub/statsports_starter/.venv/bin/python"

# Function to get the latest session date from CSV
get_latest_session_date() {
    if [ -f "combined_mason_mount.csv" ]; then
        /bin/echo "$(/bin/date): Found existing Mason Mount CSV file" >> /tmp/statsports_cron.log
        # Extract max session_date from CSV (assuming it's in YYYY-MM-DDTHH:MM:SSZ format)
        $PYTHON_EXEC -c "
import pandas as pd
import sys
from datetime import datetime, timedelta

try:
    df = pd.read_csv('combined_mason_mount.csv')
    if 'session_date' in df.columns and len(df) > 0:
        # Get max date and convert to YYYY-MM-DD format
        max_date = pd.to_datetime(df['session_date']).max()
        print(max_date.strftime('%Y-%m-%d'))
    else:
        # If no data, start from 2 days ago to be safe
        two_days_ago = datetime.now() - timedelta(days=2)
        print(two_days_ago.strftime('%Y-%m-%d'))
except Exception as e:
    # If any error, fallback to 2 days ago
    two_days_ago = datetime.now() - timedelta(days=2)
    print(two_days_ago.strftime('%Y-%m-%d'))
"
    else
        /bin/echo "$(/bin/date): No existing Mason Mount CSV file found" >> /tmp/statsports_cron.log
        # If no CSV exists, start from 2 days ago
        date -v-2d "+%Y-%m-%d"
    fi
}
# This ensures no gaps if Mac was off for multiple days

# Change to the script directory
cd /Users/christopherdickson/Documents/GitHub/statsports_starter

# Activate virtual environment
source .venv/bin/activate

# Function to get the latest session date from CSV
get_latest_session_date() {
    if [ -f "combined_mason_mount.csv" ]; then
        # Extract max session_date from CSV (assuming it's in YYYY-MM-DDTHH:MM:SSZ format)
        $PYTHON_EXEC -c "
import pandas as pd
import sys
from datetime import datetime, timedelta

try:
    df = pd.read_csv('combined_mason_mount.csv')
    if 'session_date' in df.columns and len(df) > 0:
        # Get max date and convert to YYYY-MM-DD format
        max_date = pd.to_datetime(df['session_date']).max()
        print(max_date.strftime('%Y-%m-%d'))
    else:
        # If no data, start from 2 days ago to be safe
        two_days_ago = datetime.now() - timedelta(days=2)
        print(two_days_ago.strftime('%Y-%m-%d'))
except Exception as e:
    # If any error, fallback to 2 days ago
    two_days_ago = datetime.now() - timedelta(days=2)
    print(two_days_ago.strftime('%Y-%m-%d'))
"
    else
        # If no CSV exists, start from 2 days ago
        date -v-2d "+%Y-%m-%d"
    fi
}

# Get yesterday's date (the day we want to extract up to)
YESTERDAY=$(date -v-1d "+%Y-%m-%d")

# Get the latest session date from existing data
LATEST_DATE=$(get_latest_session_date)

# Log current status
/bin/echo "$(/bin/date): CSV latest session date: $LATEST_DATE" >> /tmp/statsports_cron.log
/bin/echo "$(/bin/date): Target extraction date (yesterday): $YESTERDAY" >> /tmp/statsports_cron.log

# Only run if we need to extract data (latest date is before yesterday)
if [ "$LATEST_DATE" != "$YESTERDAY" ] && [ "$LATEST_DATE" \< "$YESTERDAY" ]; then
    /bin/echo "$(/bin/date): GAP DETECTED - Running extraction from $LATEST_DATE to $YESTERDAY" >> /tmp/statsports_cron.log
    
    # Run the extraction
    /Users/christopherdickson/Documents/GitHub/statsports_starter/run.sh "$LATEST_DATE" "$YESTERDAY"
    
    if [ $? -eq 0 ]; then
        /bin/echo "$(/bin/date): ✅ EXTRACTION SUCCESS for $LATEST_DATE to $YESTERDAY" >> /tmp/statsports_cron.log
        
        # Check if Mason Mount data was updated
        if [ -f "combined_mason_mount.csv" ]; then
            RECORD_COUNT=$($PYTHON_EXEC -c "import pandas as pd; df=pd.read_csv('combined_mason_mount.csv'); print(len(df))")
            /bin/echo "$(/bin/date): Mason Mount dataset now contains $RECORD_COUNT records" >> /tmp/statsports_cron.log
        fi
        
    else
        /bin/echo "$(/bin/date): ❌ EXTRACTION FAILED for $LATEST_DATE to $YESTERDAY" >> /tmp/statsports_cron.log
    fi
else
    /bin/echo "$(/bin/date): ✅ NO EXTRACTION NEEDED - Data is current (CSV: $LATEST_DATE, Target: $YESTERDAY)" >> /tmp/statsports_cron.log
    
    # Still log that we checked
    if [ -f "combined_mason_mount.csv" ]; then
        RECORD_COUNT=$($PYTHON_EXEC -c "import pandas as pd; df=pd.read_csv('combined_mason_mount.csv'); print(len(df))")
        /bin/echo "$(/bin/date): Mason Mount dataset remains at $RECORD_COUNT records (no new data)" >> /tmp/statsports_cron.log
    fi
fi

# End logging
/bin/echo "$(/bin/date): ==================== DAILY EXTRACTION END ======================" >> /tmp/statsports_cron.log
/bin/echo "" >> /tmp/statsports_cron.log