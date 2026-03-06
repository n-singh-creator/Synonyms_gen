"""
Mercari Android App Search Test

This module tests the search functionality of the Mercari Android app
using Appium automation. It loads synonyms from CSV and performs searches
for original queries and their generated synonyms.
"""
import os
import unittest
import time
import csv
import pandas as pd
from datetime import datetime
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy


# -------- Appium Capabilities --------
CAPABILITIES = {
    "platformName": "Android",
    "automationName": "UIAutomator2",
    "deviceName": "Android Emulator",
    "platformVersion": "16",
    "appPackage": "com.mercari.global",
    "noReset": True,
    "newCommandTimeout": 300
}

APPIUM_SERVER_URL = "http://127.0.0.1:4723"

# -------- File Paths --------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
INPUT_CSV = os.path.join(PROJECT_ROOT, "synonyms_genrator_output", "translator_gemini_3_synonyms_gen_zh_to_jp.csv")
OUTPUT_CSV = os.path.join(PROJECT_ROOT, "search_results", "search_log.csv")


class TestMercariSearch(unittest.TestCase):
    """
    Test suite for Mercari app search functionality with synonym testing.
    """

    def setUp(self):
        """Initialize Appium driver before each test."""
        options = UiAutomator2Options().load_capabilities(CAPABILITIES)
        self.driver = webdriver.Remote(APPIUM_SERVER_URL, options=options)
        
    def tearDown(self):
        """Clean up Appium driver after each test."""
        if self.driver:
            self.driver.quit()

    def log_search(self, original_query, searched_query, searched=True):
        """
        Log search activity to CSV file.
        
        Args:
            original_query: The original query from input CSV
            searched_query: The actual query being searched (original or synonym)
            searched: Boolean indicating if search was performed
        """
        file_exists = os.path.isfile(OUTPUT_CSV)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
        
        with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["original_query", "searched", "date"]
            )
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                "original_query": searched_query,
                "searched": str(searched),
                "date": datetime.now().strftime("%d/%m/%Y")
            })

    def search_in_app(self, text: str):
        """
        Enters text into the Mercari search EditText and submits it.
        
        Args:
            text: The search query to enter
        """
        try:
            # Locate search input using UiAutomator for more reliable selection
            search_input = self.driver.find_element(
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().className("android.widget.EditText").instance(0)'
            )
            
            # Focus the field
            search_input.click()
            search_input.clear()
            search_input.clear() # Clear twice to ensure field is empty (sometimes one clear may not work)
            # Enter search text
            search_input.send_keys(text)
            
            # Press Enter (submit)
            self.driver.execute_script(
                "mobile: pressKey",
                {"keycode": 66}
            )
            
            # Wait for results to load
            time.sleep(3)
            
        except Exception as e:
            print(f"Error searching for '{text}': {str(e)}")
            raise

    def test_synonym_search(self):
        """
        Main test: Load CSV, search original queries and their synonyms.
        
        For each row in the CSV:
        1. Search the original_query
        2. Parse output column (split by |)
        3. Search each synonym
        4. Log all searches to output CSV
        """
        try:
            # Load input CSV
            if not os.path.exists(INPUT_CSV):
                self.fail(f"Input CSV not found: {INPUT_CSV}")
            
            df = pd.read_csv(INPUT_CSV)
            print(f"\nLoaded {len(df)} rows from {INPUT_CSV}")
            print(f"Columns: {df.columns.tolist()}\n")
            
        
            # Process each row
            for index, row in df.iterrows():
                original_query = row['original_query']
                output = row['output']
                
                print(f"\n{'='*60}")
                print(f"Row {index + 1}/{len(df)}")
                print(f"Original Query: {original_query}")
                print(f"Output: {output}")
                print(f"{'='*60}")
                
                # 1. Search original query
                print(f"\n[1] Searching original query: {original_query}")
                self.search_in_app(original_query)
                self.log_search(original_query, original_query, searched=True)
                print(f"✓ Logged: {original_query}")
                
                # 2. Parse and search synonyms
                synonyms = [s.strip() for s in output.split('|') if s.strip()]
                print(f"\n[2] Found {len(synonyms)} synonym(s)")
                
                for i, synonym in enumerate(synonyms, 1):
                    print(f"\n[2.{i}] Searching synonym: {synonym}")
                    self.search_in_app(synonym)
                    self.log_search(original_query, synonym, searched=True)
                    print(f"✓ Logged: {synonym}")
                
                print(f"\n✓ Completed row {index + 1}: Total {1 + len(synonyms)} searches")
            
            print(f"\n{'='*60}")
            print(f"All searches completed!")
            print(f"Results saved to: {OUTPUT_CSV}")
            print(f"{'='*60}\n")
            
        except FileNotFoundError as e:
            self.fail(f"File not found: {e}")
        except pd.errors.EmptyDataError:
            self.fail("Input CSV is empty")
        except Exception as e:
            self.fail(f"An unexpected error occurred: {str(e)}")


if __name__ == "__main__":
    unittest.main()
