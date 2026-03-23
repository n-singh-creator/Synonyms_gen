package Convertor

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
)

// SynonymEntry represents a single synonym record
type SynonymEntry struct {
	InputText      string   `json:"input_text"`
	OutputSynonyms []string `json:"output_synonyms"`
	Annotated      bool     `json:"annotated"`
}

// LoadCSVAndConvert reads the CSV file and converts it to the target JSON format
// It preserves annotation status from existing JSON file if synonyms haven't changed
func LoadCSVAndConvert(csvPath string, existingJSONPath string) ([]SynonymEntry, error) {
	// Load existing JSON data to preserve annotation status
	existingData := make(map[string]SynonymEntry)
	if existingJSONPath != "" {
		if jsonFile, err := os.Open(existingJSONPath); err == nil {
			defer jsonFile.Close()
			var existingEntries []SynonymEntry
			decoder := json.NewDecoder(jsonFile)
			if err := decoder.Decode(&existingEntries); err == nil {
				for _, entry := range existingEntries {
					existingData[entry.InputText] = entry
				}
			}
		}
	}

	file, err := os.Open(csvPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open CSV file: %w", err)
	}
	defer file.Close()

	reader := csv.NewReader(file)

	// Skip header row
	_, err = reader.Read()
	if err != nil {
		return nil, fmt.Errorf("failed to read header: %w", err)
	}

	var entries []SynonymEntry

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, fmt.Errorf("failed to read CSV record: %w", err)
		}

		// Ensure we have at least 2 columns
		if len(record) < 2 {
			continue
		}

		inputText := record[0]
		outputText := record[1]

		// Split the output by "|" to get synonyms
		rawSynonyms := strings.Split(outputText, "|")

		// Trim leading and trailing spaces from each synonym
		synonyms := make([]string, 0, len(rawSynonyms))
		for _, syn := range rawSynonyms {
			trimmed := strings.TrimSpace(syn)
			if trimmed != "" {
				synonyms = append(synonyms, trimmed)
			}
		}

		// Check if this entry existed before and if synonyms changed
		annotated := false
		if existingEntry, exists := existingData[inputText]; exists {
			// Compare synonyms to see if they changed
			if synonymsEqual(existingEntry.OutputSynonyms, synonyms) {
				// Synonyms are the same, preserve annotation status
				annotated = existingEntry.Annotated
			}
			// If synonyms changed, annotated stays false (needs re-annotation)
		}

		entry := SynonymEntry{
			InputText:      inputText,
			OutputSynonyms: synonyms,
			Annotated:      annotated,
		}

		entries = append(entries, entry)
	}

	return entries, nil
}

// synonymsEqual compares two synonym slices for equality (order-independent, case-insensitive, trimmed)
func synonymsEqual(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}

	// Check if all elements in 'a' exist in 'b' (case-insensitive, trimmed)
	for _, elemA := range a {
		normalizedA := strings.ToLower(strings.TrimSpace(elemA))
		found := false
		for _, elemB := range b {
			normalizedB := strings.ToLower(strings.TrimSpace(elemB))
			if normalizedA == normalizedB {
				found = true
				break
			}
		}
		if !found {
			return false
		}
	}

	return true
}

// ConvertCSVToJSON reads the CSV file and returns JSON bytes
// Pass existingJSONPath to preserve annotation status, or empty string for new conversion
func ConvertCSVToJSON(csvPath string, existingJSONPath string) ([]byte, error) {
	entries, err := LoadCSVAndConvert(csvPath, existingJSONPath)
	if err != nil {
		return nil, err
	}

	jsonData, err := json.MarshalIndent(entries, "", "  ")
	if err != nil {
		return nil, fmt.Errorf("failed to marshal JSON: %w", err)
	}

	return jsonData, nil
}

// SaveGenratorOutputToJSONFile reads the CSV and saves it as a JSON file
// It preserves annotation status from the existing JSON file if it exists
func SaveGenratorOutputToJSONFile(csvPath, jsonPath string) error {
	// Try to use the existing JSON file to preserve annotations
	jsonData, err := ConvertCSVToJSON(csvPath, jsonPath)
	if err != nil {
		return err
	}

	err = os.WriteFile(jsonPath, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}

	return nil
}
