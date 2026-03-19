import os
import sys
import unittest
import time
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
import json
import pandas as pd 
import csv
import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from searchers.duckduckgo_search import duckduckgoSearch
from LLmHelper import load_query_explainer_config, QueryExplainerClient
# -------- Configuration Variables --------

# Load configuration LLM explainer configration 
profile = load_query_explainer_config("explain_query_gpt_5_search")



# Get the script's directory and construct absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Input JSON file path containing translation data with BigQuery product match counts
INPUT_JSON_FILE = os.path.join(PROJECT_ROOT, "bigQueryOutput/translator_gemini_3_synonyms_gen_zh_to_jp.json")

# Output CSV file path for storing annotation results
OUTPUT_CSV_FILE = os.path.join(PROJECT_ROOT, "Annotated_result/search_results.csv")

# Appium server URL for connecting to the Android automation server
APPIUM_SERVER_URL = "http://127.0.0.1:4723"

# CSV column names for the output file
CSV_FIELDNAMES = ["input_col", "synonyms_col", "relevancy", "length change", "comment"]

# -------- Appium Capabilities --------
# Configuration for Android device/emulator connection
capabilities = {
    "platformName": "Android",
    "automationName": "UIAutomator2",
    "deviceName": "Android Emulator",
    "platformVersion": "16",
    "appPackage": "com.mercari.global",
    "noReset": True,
    "newCommandTimeout": 300
}


class TestMercariSearch(unittest.TestCase):

    def appendToResultCSVFile(self,file_path, row):
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        file_exists = os.path.isfile(file_path)

        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=CSV_FIELDNAMES
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

    def setUp(self):
        options = UiAutomator2Options().load_capabilities(capabilities)
        self.driver = webdriver.Remote(APPIUM_SERVER_URL, options=options)
        self.duckduckgo_searcher = duckduckgoSearch()
    
    def tearDown(self):
        if self.driver:
            self.driver.quit()
        self.duckduckgo_searcher.teardown()

    def searchPreconditionSetup(self):
        """
        Precondition:
        - Open Mercari app
        - Tap Search
        - Enter search term
        - Submit search
        """

        # 1️⃣ Tap Search button
        search_button = self.driver.find_element(
            AppiumBy.ACCESSIBILITY_ID,
            "Search input box"
        )
        search_button.click()

        # 2️⃣ Locate search input (stable locator)
        search_input = self.driver.find_element(
            AppiumBy.ANDROID_UIAUTOMATOR,
            'new UiSelector().className("android.widget.EditText").instance(0)'
        )
        search_input.send_keys("psa10")

        # 3️⃣ Submit (Enter key)
        self.driver.execute_script(
            "mobile: pressKey",
            {"keycode": 66}
        )

        # 4️⃣ Wait for results to load
        time.sleep(1)

        # 🔍 Assertion placeholder (replace later)
        # Example:
        # self.driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, "new UiSelector().textContains('psa10')")
    def searchInApp(self, text: str):
        """
        Enters text into the search EditText and submits it.
        """

        # Locate search input
        search_input = self.driver.find_element(
            by=AppiumBy.CLASS_NAME,
            value="android.widget.EditText"
        )

        # Focus the field
        search_input.click()
        search_input.clear()
        # Enter search text
        search_input.send_keys(text)

        # Press Enter (submit)
        self.driver.execute_script(
            "mobile: pressKey",
            {"keycode": 66}
        )
    def test_searchFunctionality(self):
        """
        Test the search functionality using the searchInApp helper method.
        Loads data from BigQuery output and uses product match counts as length scores.
        """
        # Create client
        explainer = QueryExplainerClient(profile)

        # Explain a query
        
        try:
            with open(INPUT_JSON_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
                currentTime = datetime.datetime.now()
                time_string = currentTime.strftime("%B %d %Y_%I:%M %p")

                # print(data)  # For demonstration, print the content
                # self.searchPreconditionSetup()
                for row in data:
                    inputText = row["input_text"]
                    AnnotationArray = row["output_synonyms"]
                    
                   
                    isAnnotated = row["annotated"]
                    productsMatched = row.get("products_matched", {})
                    
                    if(isAnnotated):
                        continue #Skip annotated rows
                    
                    print(f"\n{'='*60}")
                    print(f"Input Text: {inputText}")
                    print(f"Products Matched for Input: {productsMatched.get(inputText, 0)}")
                    
                    self.duckduckgo_searcher.searchDuckduckgo(inputText)
                    explanation = explainer.explain_query(inputText)
                    print(explanation)
                    print(f"Synonyms:")
                    InputSearchTermRecall = productsMatched.get(inputText, 0)
                    for query in AnnotationArray:
                        print(f"\n{'-'*40}")
                        print(f"Searching -  {query}")
                        
                        # Get the length from products_matched for this synonym
                        synSearchLength = productsMatched.get(query, 0)
                        print(f"Product Match Count (from BigQuery): {synSearchLength}")
                        
                        self.searchInApp(query)
                        # time.sleep(1)  # Wait for results to load
                        
                        relevancy = input("Enter relevancy score 0-3: ")
                        comment = input("Enter comment (if any): ")
                   
                        if comment:
                            print(f"Comment for '{query}': {comment}")
                        print(f"Relevancy score for '{query}': {relevancy}")
                        
                        row_data = {
                            "input_col": inputText,
                            "synonyms_col": query,
                            "relevancy": relevancy,
                            "length change": (synSearchLength-InputSearchTermRecall),
                            "comment": comment
                        }
                        self.appendToResultCSVFile(OUTPUT_CSV_FILE, row_data)
                    
                    #Updated the annotated field in the JSON data
                    row["annotated"] = True
                    
                # Write back the updated JSON data
        except FileNotFoundError:
            print(f"The file '{INPUT_JSON_FILE}' was not found.")
        except json.JSONDecodeError:
            print("Error decoding JSON from the file.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            # Write back the updated annotated status
            try:
                with open(INPUT_JSON_FILE, "w", encoding="utf-8") as file:    
                    json.dump(data, file, ensure_ascii=False, indent=2)
                print(f"\n{'='*60}")
                print(f"Results saved to: {OUTPUT_CSV_FILE}")
                print(f"Updated JSON saved to: {INPUT_JSON_FILE}")
            except Exception as e:
                print(f"Error writing updated JSON: {e}")

if __name__ == "__main__":
    unittest.main()
