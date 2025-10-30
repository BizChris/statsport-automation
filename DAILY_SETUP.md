# Daily Automated Extraction Setup

## 🕐 **Cron Setup (Already Configured)**

Your Mac is now set to run STATSports extraction **daily at 1:00 AM** for yesterday's data.

### Current Cron Job:
```bash
0 1 * * * /Users/christopherdickson/Documents/GitHub/statsports_starter/daily_extract.sh
```

### Check Status:
```bash
# View current cron jobs
crontab -l

# Check extraction logs
tail -f /tmp/statsports_cron.log
```

## 🔧 **Alternative: macOS LaunchAgent (More Robust)**

If you prefer better logging and more reliability:

```bash
# 1. Copy the launch agent file
cp com.statsports.daily-extract.plist ~/Library/LaunchAgents/

# 2. Load the launch agent
launchctl load ~/Library/LaunchAgents/com.statsports.daily-extract.plist

# 3. Remove cron job (optional)
crontab -r

# 4. Check logs
tail -f /tmp/statsports_daily.log
tail -f /tmp/statsports_daily_error.log
```

## 📋 **What Happens Daily**

1. **1:00 AM**: Script runs automatically
2. **Checks CSV**: Finds the latest session date in `combined_mason_mount.csv`
3. **Calculates Gap**: Extracts from latest date to **yesterday** (not today)
4. **Smart Logic**: Skips if data is already current to yesterday
5. **Extracts**: STATSports data for any missing date range
6. **Updates**: Mason Mount dataset with new records
7. **Uploads**: Updated CSV to OneDrive
8. **Logs**: Results to `/tmp/statsports_cron.log`

### 🛡️ **Gap Protection Examples:**
- **CSV current to yesterday**: Skips extraction (no gap)
- **CSV missing 1 day**: Extracts that 1 missing day
- **Mac off 3 days**: Extracts 3 missing days to catch up
- **CSV from last week**: Extracts full week to catch up

### 🕐 **Why "Yesterday" Logic:**
At 1 AM, "today" just started, so we extract completed days up to yesterday. This ensures we capture full day's worth of sessions that finished the day before.

## 🛠️ **Management Commands**

```bash
# Test the daily script manually
./daily_extract.sh

# View/edit cron jobs
crontab -e

# Remove cron job
crontab -r

# Check if Mac is sleeping (affects scheduling)
pmset -g sched
```

## ⚠️ **Important Notes**

- **Mac must be awake** at 1 AM for cron to run
- **Power settings**: Ensure Mac doesn't sleep completely
- **Permissions**: May need to grant Terminal "Full Disk Access" in System Preferences → Security & Privacy
- **Testing**: Run `./daily_extract.sh` manually first to verify it works

## 📊 **Monitoring**

Check if it's working:
```bash
# Check recent runs
ls -la runs/ | head -5

# Check Mason Mount updates
ls -la combined_mason_mount*.csv

# Check OneDrive uploads (should see recent uploads)
```

## 🔄 **Troubleshooting**

If daily runs fail:
1. Check logs: `cat /tmp/statsports_cron.log`
2. Test manually: `./daily_extract.sh`
3. Verify permissions and paths
4. Check Mac sleep settings