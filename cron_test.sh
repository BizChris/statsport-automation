#!/bin/bash
# Simple cron test script - explicitly use absolute paths
# Note: This script is no longer needed since we switched to launchd
/bin/echo "$(/bin/date): 🧪 CRON TEST - This proves cron is working with Full Disk Access" >> /tmp/statsports_cron.log