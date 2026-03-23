package Bigquery

import (
	"bufio"
	"encoding/json"
	"fmt"
	Convertor "nayan/m/Convertor"
	"os"
	"strings"
)

// BigQueryEntry represents a single entry from the BigQuery dump
type BigQueryEntry struct {
	OriginalQuery     string              `json:"original_query"`
	MatchedQueriesMap []MatchedQueryEntry `json:"matched_queries_map"`
	QueryLanguageCode string              `json:"query_language_code"`
	UserID            string              `json:"user_id"`
}

// MatchedQueryEntry represents a key-value pair in matched_queries_map
type MatchedQueryEntry struct {
	Key   string            `json:"key"`
	Value MatchedQueryValue `json:"value"`
}

// MatchedQueryValue contains the products array
type MatchedQueryValue struct {
	Products []Product `json:"products"`
}

// Product represents a single product with ID and score
type Product struct {
	ProductID string  `json:"product_id"`
	Score     float64 `json:"score"`
}

// EnhancedSynonymEntry represents a synonym entry with product match counts
type EnhancedSynonymEntry struct {
	InputText       string         `json:"input_text"`
	OutputSynonyms  []string       `json:"output_synonyms"`
	ProductsMatched map[string]int `json:"products_matched"`
	Annotated       bool           `json:"annotated"`
}

// LoadBigQueryJSON loads and parses the BigQuery JSON dump file in NDJSON format
// (newline-delimited JSON where each line is a separate JSON object)
func LoadBigQueryJSON(filePath string) ([]BigQueryEntry, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open BigQuery JSON file: %w", err)
	}
	defer file.Close()

	var entries []BigQueryEntry
	scanner := bufio.NewScanner(file)

	// Increase buffer size for large lines (up to 10MB per line)
	const maxCapacity = 10 * 1024 * 1024
	buf := make([]byte, maxCapacity)
	scanner.Buffer(buf, maxCapacity)

	lineNum := 0
	for scanner.Scan() {
		lineNum++
		line := strings.TrimSpace(scanner.Text())

		// Skip empty lines
		if line == "" {
			continue
		}

		// Parse each line as a JSON object
		var entry BigQueryEntry
		if err := json.Unmarshal([]byte(line), &entry); err != nil {
			// Log warning but continue processing other lines
			fmt.Printf("Warning: Failed to parse line %d: %v\n", lineNum, err)
			continue
		}

		entries = append(entries, entry)
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading file: %w", err)
	}

	if len(entries) == 0 {
		return nil, fmt.Errorf("no valid entries found in BigQuery JSON file")
	}

	fmt.Printf("Successfully loaded %d entries from BigQuery dump\n", len(entries))
	return entries, nil
}

// ExtractQueryFromKey extracts the query portion from a matched_queries_map key
// Example: "name_ngram_match_phrase_僕のヒーローアカデミア" -> "僕のヒーローアカデミア"
func ExtractQueryFromKey(key string) string {

	parts := strings.Split(key, "_")
	if len(parts) < 1 {
		return ""
	}
	// The query is everything after the last underscore

	return parts[len(parts)-1]
}

// FindProductMatchCounts searches the BigQuery data for matching queries and counts products
func FindProductMatchCounts(inputQuery string, synonyms []string, bigQueryData []BigQueryEntry) map[string]int {
	productsMatched := make(map[string]int)

	// Create a set of all queries to search for (input + synonyms)
	allQueries := []string{inputQuery}
	allQueries = append(allQueries, synonyms...)

	// Search through BigQuery data
	for _, bqEntry := range bigQueryData { //TODO: optimize by creating a map of original_query to entries for O(1) lookup instead of O(n) scan
		// Check if this entry's original_query matches any of our queries
		for _, searchQuery := range allQueries {
			if bqEntry.OriginalQuery == searchQuery {
				// Found a match, now process matched_queries_map
				for _, matchedEntry := range bqEntry.MatchedQueriesMap {
					// Extract the query from the key
					extractedQuery := ExtractQueryFromKey(matchedEntry.Key)

					// Check if the extracted query matches the search query
					if extractedQuery == searchQuery {
						// Count the products
						productCount := len(matchedEntry.Value.Products)

						// Store or update the max count for this query
						if existingCount, exists := productsMatched[searchQuery]; !exists || productCount > existingCount {
							productsMatched[searchQuery] = productCount
						}
					}

				}
			}
		}
	}

	return productsMatched
}

// ProcessCSVWithBigQueryData processes the CSV file with BigQuery data to generate enhanced output
func ProcessCSVWithBigQueryData(csvPath, bigQueryJSONPath, outputDir string) error {
	// Construct output path to preserve annotations if file exists
	outputPath := outputDir + "/translator_gemini_3_synonyms_gen_zh_to_jp.json"

	// Load CSV data (preserving annotations from existing output file if it exists)
	csvEntries, err := Convertor.LoadCSVAndConvert(csvPath, outputPath)
	if err != nil {
		return fmt.Errorf("failed to load CSV: %w", err)
	}

	// Load BigQuery data
	bigQueryData, err := LoadBigQueryJSON(bigQueryJSONPath)
	if err != nil {
		return fmt.Errorf("failed to load BigQuery JSON: %w", err)
	}

	// Process each CSV entry
	var enhancedEntries []EnhancedSynonymEntry
	for _, csvEntry := range csvEntries {
		productsMatched := FindProductMatchCounts(csvEntry.InputText, csvEntry.OutputSynonyms, bigQueryData)

		enhancedEntry := EnhancedSynonymEntry{
			InputText:       csvEntry.InputText,
			OutputSynonyms:  csvEntry.OutputSynonyms,
			ProductsMatched: productsMatched,
			Annotated:       csvEntry.Annotated,
		}
		enhancedEntries = append(enhancedEntries, enhancedEntry)
	}

	// Create output directory if it doesn't exist
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Save to JSON file
	jsonData, err := json.MarshalIndent(enhancedEntries, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal enhanced entries: %w", err)
	}

	if err := os.WriteFile(outputPath, jsonData, 0644); err != nil {
		return fmt.Errorf("failed to write output file: %w", err)
	}

	return nil
}
