#!/bin/bash
# Check cron status and manually test daily extraction

echo "🔍 CRON STATUS CHECK"
echo "===================="

# Check if cron is running
echo "📋 Current cron jobs:"
crontab -l

echo ""
echo "🕐 Cron service status:"
sudo launchctl list | grep cron || echo "Cron service info not available"

echo ""
echo "📅 Recent cron log entries (last 10):"
tail -10 /tmp/statsports_cron.log

echo ""
echo "🔍 Checking for entries from today ($(date '+%b %d')):"
grep "$(date '+%b %d')" /tmp/statsports_cron.log || echo "No entries found for today"

echo ""
echo "⚡ Testing daily extraction script now:"
echo "======================================"
/Users/christopherdickson/Documents/GitHub/statsports_starter/daily_extract.sh

echo ""
echo "📊 Latest log entries after test:"
tail -5 /tmp/statsports_cron.log