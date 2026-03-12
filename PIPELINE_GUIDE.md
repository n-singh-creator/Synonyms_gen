# Pipeline Orchestration Guide

## Overview

The `run_pipeline.py` script orchestrates the entire synonym generation and annotation workflow in three automated phases:

1. **Setup Phase** - Prepares the environment and runs initial translations
2. **Processing Phase** - Processes BigQuery data and analyzes results
3. **Annotation Phase** - Runs the annotation helper script

## Prerequisites

Before running the pipeline, ensure you have:

- ✅ Python 3.x with virtual environment activated
- ✅ Go installed and configured
- ✅ Appium installed (`npm install -g appium`)
- ✅ Android emulator running
- ✅ All required Python packages installed
- ✅ Input data ready in `original_query_lists/input.csv`

## Quick Start

```bash
# Activate your virtual environment (if not already activated)
source .venv/bin/activate

# Run the complete pipeline
python run_pipeline.py
```

## What Happens in Each Phase

### Phase 1: Setup ⚙️

**Automatic Steps:**
1. Starts Appium server (if not already running)
2. Executes `main.go --setup` which:
   - Runs translation job (LLM-based synonym generation)
   - Converts CSV output to JSON format
   - Skips BigQuery processing
3. Runs `test_automation/android_test/test_mercari_search.py` to test searches

**User Interaction:**
- Pipeline pauses with message: **"⏸ Waiting for BigQuery data"**
- At this point, you should prepare/verify your BigQuery data dump
- Press Enter when ready to continue

### Phase 2: Processing 📊

**Automatic Steps:**
1. Executes `main.go --process` which:
   - Processes CSV with BigQuery data
   - Outputs enhanced results to `bigQueryOutput/`
2. Runs `BigQueryOutputAnalyzer/synonyms.py` to analyze the results
   - Provides statistics and metrics on synonym quality

**User Interaction:**
- Pipeline pauses with message: **"⏸ Please verify the BigQueryOutput directory"**
- Review the generated files in `bigQueryOutput/`
- Check the analysis output from synonyms.py
- Press Enter to proceed to annotation

### Phase 3: Annotation ✍️

**Automatic Steps:**
1. (Mannual)Runs `Annotator/annotator_helper_script.py`
   - Opens interactive annotation interface
   - Uses Appium to facilitate manual review
   - Saves results to `Annotated_result/search_results.csv`

**Completion:**
- All phases completed successfully! 🎉

## Manual Phase Execution

If you need to run phases individually:

### Setup Phase Only
```bash
# Start Appium manually
appium &

# Run main.go with setup flag
go run main.go --setup

# Run search tests
python test_automation/android_test/test_mercari_search.py
```

### Processing Phase Only
```bash
# Process BigQuery data
go run main.go --process

# Analyze results
python BigQueryOutputAnalyzer/synonyms.py bigQueryOutput/translator_gemini_3_synonyms_gen_zh_to_jp.json
```

### Annotation Phase Only
```bash
# Make sure Appium is running
python Annotator/annotator_helper_script.py
```

## main.go Command Flags

The updated `main.go` now supports two flags:

- `--setup`: Run translation and conversion only (skip BigQuery processing)
- `--process`: Run BigQuery processing only (skip translation)
- No flags: Run complete workflow (default behavior)

```bash
# Examples:
go run main.go              # Full workflow
go run main.go --setup      # Setup phase only
go run main.go --process    # Processing phase only
```

## Output Locations

| Phase | Output Location | Description |
|-------|----------------|-------------|
| Setup | `synonyms_genrator_output/` | Translation results (CSV & JSON) |
| Setup | `search_results/search_log.csv` | Search test results |
| Processing | `bigQueryOutput/` | BigQuery-enhanced results |
| Annotation | `Annotated_result/search_results.csv` | Manual annotation results |

## Troubleshooting

### Appium Won't Start
```bash
# Check if Appium is installed
which appium

# Install if needed
npm install -g appium

# Check if port 4723 is in use
lsof -i :4723

# Kill existing process if needed
kill -9 $(lsof -t -i:4723)
```

### Python Environment Issues
```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Install required packages
pip install -r test_automation/requirements.txt
```

### Go Build Errors
```bash
# Make sure Go modules are up to date
go mod tidy
go mod download
```

### Android Emulator Not Detected
```bash
# List connected devices
adb devices

# Start emulator if needed
emulator -avd <your_avd_name>
```

## Features

✨ **Color-coded output** - Easy to follow progress
✨ **Error handling** - Graceful failure with cleanup
✨ **Interactive pauses** - Manual verification at key points
✨ **Automatic cleanup** - Appium server stops on completion/failure
✨ **Progress tracking** - Clear phase and step indicators
✨ **Flexible execution** - Run all phases or individual ones

## Pipeline Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│                    START PIPELINE                    │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   PHASE 1: SETUP     │
          ├──────────────────────┤
          │ 1. Start Appium      │
          │ 2. Run main.go       │
          │    --setup           │
          │ 3. Run search tests  │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  USER CHECKPOINT     │
          │  "Wait for BigQuery" │
          │  Press Enter...      │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ PHASE 2: PROCESSING  │
          ├──────────────────────┤
          │ 1. Run main.go       │
          │    --process         │
          │ 2. Analyze synonyms  │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │  USER CHECKPOINT     │
          │  "Verify Output"     │
          │  Press Enter...      │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ PHASE 3: ANNOTATION  │
          ├──────────────────────┤
          │ 1. Run annotator     │
          │    helper script     │
          └──────────┬───────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   CLEANUP & FINISH   │
          │  Stop Appium Server  │
          └──────────────────────┘
```

## Support

If you encounter issues:
1. Check the error messages (color-coded for clarity)
2. Verify all prerequisites are installed
3. Try running phases individually to isolate the problem
4. Check output directories for partial results
