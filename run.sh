#!/bin/bash
# run.sh - Quick runner that handles venv activation automatically

set -e

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Run './setup.sh' first."
    exit 1
fi

# Set Python executable from virtual environment
PYTHON_EXEC="/Users/christopherdickson/Documents/GitHub/statsports_starter/.venv/bin/python"

if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    echo "Usage: ./run.sh START_DATE END_DATE [PLAYER_NAME]"
    echo "Example: ./run.sh 2024-01-01 2024-01-31"
    echo "Example: ./run.sh 2024-01-01 2024-01-31 'mason mount'"
    echo "Note: If PLAYER_NAME is not provided, uses PLAYER_NAME from .env file"
    exit 1
fi

# Set player name if provided as third parameter
if [ $# -eq 3 ]; then
    export PLAYER_NAME="$3"
    echo "Running extraction: $1 to $2 (Player: $3)"
else
    echo "Running extraction: $1 to $2"
fi

$PYTHON_EXEC extract_statsports_data.py "$1" "$2"

# Check if extraction was successful and if player update script exists
if [ $? -eq 0 ] && [ -f "update_player.py" ]; then
    echo ""
    echo "🔄 Extraction complete - checking for player updates..."
    
    # Check if there's an existing player CSV to update
    if [ -f "combined_mason_mount.csv" ]; then
        echo "📊 Updating player dataset..."
        $PYTHON_EXEC update_player.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Player dataset updated successfully!"
            
            # Try automatic OneDrive upload if Azure is configured
            echo ""
            echo "📤 Uploading to OneDrive..."
            
            if $PYTHON_EXEC upload_to_onedrive.py; then
                echo "🎉 File successfully uploaded to OneDrive!"
            else
                echo "❌ OneDrive upload failed - showing manual options:"
                echo ""
                echo "💡 Quick manual upload:"
                echo "   File: $PWD/combined_mason_mount.csv"
                echo "   OneDrive: https://netorgft16957735-my.sharepoint.com/:f:/g/personal/chris_e-d_ltd/EiiO0I9sqxZEs9VZcv2Q06cBuqpmu94HxX7_3aHSUuzxqw?e=NA2AnT"
            fi
        else
            echo "⚠️  Player update failed, but extraction data is still available."
        fi
    else
        echo "📋 No existing player dataset found (combined_mason_mount.csv)."
        echo "💡 To create one, run: $PYTHON_EXEC combine_runs.py"
    fi
else
    if [ ! -f "update_player.py" ]; then
        echo "⚠️  Player update script not found - skipping auto-update"
    fi
fi