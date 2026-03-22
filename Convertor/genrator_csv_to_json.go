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
func LoadCSVAndConvert(csvPath string) ([]SynonymEntry, error) {
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

		entry := SynonymEntry{
			InputText:      inputText,
			OutputSynonyms: synonyms,
			Annotated:      false,
		}

		entries = append(entries, entry)
	}

	return entries, nil
}

// ConvertCSVToJSON reads the CSV file and returns JSON bytes
func ConvertCSVToJSON(csvPath string) ([]byte, error) {
	entries, err := LoadCSVAndConvert(csvPath)
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
func SaveGenratorOutputToJSONFile(csvPath, jsonPath string) error {
	jsonData, err := ConvertCSVToJSON(csvPath)
	if err != nil {
		return err
	}

	err = os.WriteFile(jsonPath, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("failed to write JSON file: %w", err)
	}

	return nil
}
