# Test Automation for Mercari Search

This directory contains Android app test automation for validating search functionality with generated synonyms.

## 📁 Directory Structure

```
test_automation/
├── __init__.py
├── requirements.txt                    # Python dependencies
├── search_helpers.py                   # Helper utilities for logging
└── android_test/
    ├── __init__.py
    └── test_mercari_search.py         # Main test suite
```

## 🚀 Quick Start

### Prerequisites

1. **Android Emulator or Device**
   - Android version 16+
   - Mercari Global app installed (`com.mercari.global`)

2. **Appium Server**
   ```bash
   npm install -g appium
   appium driver install uiautomator2
   appium
   ```

3. **Python Dependencies**
   ```bash
   cd test_automation
   pip install -r requirements.txt
   ```

### Running Tests

From the project root directory:

```bash
# Run all tests
python scripts/run_prod_search.py

# Or run directly
cd test_automation/android_test
python test_mercari_search.py
```

## 📊 How It Works

1. **Loads CSV**: Reads `synonyms_genrator_output/translator_gemini_3_synonyms_gen_zh_to_jp.csv`

2. **For Each Row**:
   - Searches the `original_query` (e.g., "我的英雄學院")
   - Parses `output` column by splitting on `|`
   - Searches each synonym (e.g., "僕のヒーローアカデミア", "ヒロアカ")

3. **Logs Results**: Saves to `search_results/search_log.csv`
   ```csv
   original_query,searched,date
   我的英雄學院,True,06/03/2026
   僕のヒーローアカデミア,True,06/03/2026
   ヒロアカ,True,06/03/2026
   ```

## 🔧 Configuration

Edit `android_test/test_mercari_search.py` to modify:

```python
CAPABILITIES = {
    "platformName": "Android",
    "automationName": "UIAutomator2",
    "deviceName": "Android Emulator",
    "platformVersion": "16",  # Change to your Android version
    "appPackage": "com.mercari.global",
    "noReset": True,
    "newCommandTimeout": 300
}

APPIUM_SERVER_URL = "http://127.0.0.1:4723"  # Change if using remote server
```

## 📝 Example Output

```
============================================================
Row 1/4
Original Query: 我的英雄學院
Output: 僕のヒーローアカデミア|ヒロアカ
============================================================

[1] Searching original query: 我的英雄學院
✓ Logged: 我的英雄學院

[2] Found 2 synonym(s)

[2.1] Searching synonym: 僕のヒーローアカデミア
✓ Logged: 僕のヒーローアカデミア

[2.2] Searching synonym: ヒロアカ
✓ Logged: ヒロアカ

✓ Completed row 1: Total 3 searches
```

## 🐛 Troubleshooting

**Appium Connection Failed**
- Ensure Appium server is running: `appium`
- Check device/emulator is connected: `adb devices`

**Element Not Found**
- App UI may have changed
- Check accessibility IDs in `search_precondition_setup()`

**CSV Not Found**
- Ensure you've run the synonym generation first: `go run main.go`

## 📚 Related Files

- Input: `synonyms_genrator_output/translator_gemini_3_synonyms_gen_zh_to_jp.csv`
- Output: `search_results/search_log.csv`
- Runner: `scripts/run_prod_search.py`
