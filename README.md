# STATSports Data Extraction & OneDrive Pipeline# STATSports Data Extraction Tool



Automated pipeline for extracting STATSports data, filtering Mason Mount records, and uploading to OneDrive.Efficient Python tool for extracting STATSports session data with smart day→hour fallback strategy and fast empty-day detection.



## 🚀 Quick Start## Quick Example



```bash```bash

# 1. Setup (first time only)# 1. Setup (run once)

./setup.sh./setup.sh



# 2. Run extraction and upload# 2. Configure your API key in .env file

./run.sh 2025-10-19 2025-10-19# Edit STATSPORTS_API_KEY=your-key-here

```

# 3. Extract data

## 📁 Files Structure./run.sh 2025-01-01 2025-01-31

```

### Core Scripts

- `extract_statsports_data.py` - Main data extraction with smart fallbackThat's it! Data will be saved in `runs/TIMESTAMP/` folder as JSON and CSV files.

- `statsports_client.py` - STATSports API client

- `update_player.py` - Updates player dataset  ## Features

- `upload_to_onedrive.py` - Uploads to OneDrive via Microsoft Graph API

- `run.sh` - Automated workflow runner- **Smart fallback strategy**: Tries full day extraction first, then quick 10-second probe for data existence, only attempts hourly fallback if data is detected

- `setup.sh` - Environment setup- **Fast empty-day handling**: Skips empty days in ~10 seconds instead of waiting 24+ minutes

- **Resume capability**: Interrupted extractions can be resumed from checkpoints

### Utilities- **Automatic deduplication**: Removes duplicate sessions within each day

- `combine_runs.py` - Rebuilds Mason Mount dataset from all runs- **Clean output**: Generates JSON and CSV files in timestamped run folders

- `requirements.txt` - Python dependencies- **Progress tracking**: Real-time progress with timing information

- `.env` - Environment variables (API keys, credentials)

## Detailed Setup

### Data

- `combined_mason_mount.csv` - Cumulative Mason Mount dataset### 1. Setup Environment

- `runs/` - Historical extraction runs with raw data```bash

# Run the setup script (creates venv and installs dependencies)

## ⚙️ Configuration./setup.sh

```

### STATSports API

Set in `.env`:### 2. Configure API Access

```Edit `.env` file with your STATSports API credentials:

STATSPORTS_API_KEY=your-api-key```bash

STATSPORTS_BASE_URL=https://statsportsproseries.com/thirdpartyapi/apiSTATSPORTS_API_KEY=your-api-key-here

```STATSPORTS_API_VERSION=7

STATSPORTS_BASE_URL=https://statsportsproseries.com/thirdpartyapi/api

### OneDrive Upload  STATSPORTS_AUTH_MODE=body

Set in `.env`:STATSPORTS_TIMEOUT_SECS=60

```STATSPORTS_DISCOVERY_TIMEOUT_SECS=10

AZURE_TENANT_ID=your-tenant-id```

AZURE_CLIENT_ID=your-client-id  

AZURE_CLIENT_SECRET=your-client-secret### 3. Run Extraction

ONEDRIVE_USER_EMAIL=your-email@domain.com
ONEDRIVE_FOLDER_NAME=Your Data Folder
PLAYER_NAME=player full name
```

### 3. Run Extraction

```bash
# Extract data for a date range (YYYY-MM-DD format)
./run.sh 2025-01-01 2025-01-31

# Or specify a different player name (overrides .env setting)
./run.sh 2025-01-01 2025-01-31 "different player name"

```

## 🔄 Automated Workflow

## Output Files

`./run.sh START_DATE END_DATE` performs:

Each extraction creates a timestamped folder in `runs/` containing:

1. **Data Extraction**: Pulls STATSports data for date range- `sessions_YYYYMMDD_YYYYMMDD.json` - Raw session data

2. **Smart Fallback**: Day→hour extraction for optimal performance  - `players_YYYYMMDD_YYYYMMDD.json` - Raw player details  

3. **Mason Mount Filter**: Extracts player-specific records- `statsports_YYYYMMDD_YYYYMMDD.csv` - Flattened CSV with all data

4. **Dataset Update**: Merges with existing data, removes duplicates- `checkpoint.json` - Run metadata and progress information

5. **OneDrive Upload**: Automatically uploads to cloud storage

## Performance

## 📊 Performance Features

**Tested Performance (Oct 2025):**

- **Smart Timeout**: 60s normal, 10s discovery for empty days- 34 days (June-July 2025): 201 sessions extracted in ~3 minutes

- **144x Speedup**: Day-level fallback for sparse data periods- 31 days (Sept-Oct 2025): 220 sessions extracted in ~2 minutes

- **Deduplication**: Prevents duplicate records across runs- Empty days: ~10 seconds vs 24+ minutes with old approach

- **Incremental Updates**: Only processes new data- **144x faster** for sparse data periods

- **Backup Safety**: Automatic backups before updates

## How It Works

## 🎯 Mason Mount Dataset

### Smart Fallback Strategy

- **Current**: 1,729+ records across 230+ sessions1. **Day-level attempt**: Try to extract full day with normal 60-second timeout

- **Date Range**: July 2024 → Present  2. **Quick probe**: If day fails, do 10-second probe to check if ANY data exists

- **Location**: `combined_mason_mount.csv` + OneDrive3. **Skip or fallback**: If no data detected, skip entirely. If data exists, attempt hourly breakdown

- **Auto-Update**: Each run adds new Mason Mount data4. **Hourly extraction**: Only when necessary, with 0.2s delays between requests



## 🛠️ Maintenance### Resume Capability

- Extractions create checkpoint files as they progress

```bash- Interrupted runs can be resumed by running the same date range again

# Rebuild dataset from all runs- Progress files are automatically cleaned up after successful completion

python combine_runs.py

## Configuration Options

# Manual upload to OneDrive  

python upload_to_onedrive.py### Authentication Modes

- `STATSPORTS_AUTH_MODE=body` - Sends API key in request payload (default)

# Check environment setup- `STATSPORTS_AUTH_MODE=headers` - Sends API key in X-API-KEY header

./setup.sh

```### Timeout Settings

- `STATSPORTS_TIMEOUT_SECS=60` - Normal API request timeout

## 💾 Data Organization- `STATSPORTS_DISCOVERY_TIMEOUT_SECS=10` - Quick probe timeout for empty day detection



```## File Structure

runs/

  20251020_093038/```

    sessions_20251019_20251019.json    # Raw session datastatsports_starter/

    players_20251019_20251019.json     # Player details  ├── extract_statsports_data.py  # Main extraction script

    statsports_20251019_20251019.csv   # Complete extraction├── statsports_client.py        # API client with retry logic

    checkpoint.json                     # Progress tracking├── setup.sh                    # Environment setup script

```├── run.sh                      # Quick run script

├── requirements.txt            # Python dependencies

## 🔧 Azure Setup (OneDrive)├── .env                        # API configuration (edit this)

└── runs/                       # Output folder (created automatically)

1. **Azure Portal**: Create App Registration    └── YYYYMMDD_HHMMSS/        # Timestamped run folders

2. **Permissions**: Add `Files.ReadWrite.All` (Application)```

3. **Credentials**: Create client secret

4. **Configuration**: Add to `.env` file## Troubleshooting



Full setup instructions available in the upload script comments.### Authentication Issues
- **401/403 errors**: Check if your tenant requires `headers` vs `body` auth mode
- **Invalid API key**: Verify your API key in `.env` is correct and active

### Performance Issues
- **Slow extractions**: Most days should complete in 2-6 seconds
- **Timeout errors**: Check your network connection and API service status
- **Empty days taking too long**: Ensure `STATSPORTS_DISCOVERY_TIMEOUT_SECS=10` is set

### Data Issues
- **Missing sessions**: Check the date format (must be YYYY-MM-DD)
- **Duplicate data**: The tool automatically deduplicates within each day
- **Large files**: CSV files can be 10MB+ for busy periods with many players

## API Compatibility

- **API Version**: Tested with STATSports API v7
- **Endpoints**: Uses `/thirdPartyData/getFullSessionsByDateRange` and `/thirdPartyData/getPlayerDetails`
- **Authentication**: Supports both body-based and header-based auth
- **Rate limiting**: Includes automatic retry with exponential backoff

## Requirements

- Python 3.8+
- Dependencies: `requests`, `pandas`, `python-dotenv`
- STATSports API access with valid credentials

## Notes

- Progress files are automatically cleaned up after successful completion
- Each run is isolated in its own timestamped folder
- The tool is designed for bulk historical data extraction
- Real-time data streaming is not supported

---

*Last updated: October 2025*
*Tested on macOS with Python 3.12*
