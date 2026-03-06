package scripts

import (
	"context"
	"encoding/csv"
	"fmt"
	"io"
	synonymgenrator "nayan/m/Synonym_genrator"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

// JSONTranslator loads a json array file, translates input_text, and writes back with "<model>_output".
type Translator struct {
	LLMClient  *synonymgenrator.LLMClient
	InputPath  string
	OutputPath string // optional; if empty auto-generates
	HasHeader  bool   // if true, treats first row as header and appends output column header
}

// NewTranslator creates a translator.
func NewTranslator(client *synonymgenrator.LLMClient, profile_id, inputPath, outputFolder string, HasHeader bool) (*Translator, error) {

	inputPath = strings.TrimSpace(inputPath)
	if inputPath == "" {
		return nil, fmt.Errorf("inputPath must not be empty")
	}
	if client == nil {
		return nil, fmt.Errorf("LLM client must not be nil")
	}
	if profile_id == "" {
		return nil, fmt.Errorf("profile_id must not be empty")
	}
	if outputFolder == "" {
		outputFolder = inputPath // same dir, different name
	}
	outputPath := filepath.Join(outputFolder, fmt.Sprintf("%s.csv", profile_id))

	return &Translator{
		LLMClient:  client,
		InputPath:  inputPath,
		OutputPath: outputPath,
		HasHeader:  HasHeader,
	}, nil
}

// If outputPath is "", it will write: "<input_basename>.<ModelName>.json"
func (t *Translator) Run(ctx context.Context) error {
	if t.LLMClient == nil {
		return fmt.Errorf("LLM client is nil")
	}
	if strings.TrimSpace(t.InputPath) == "" {
		return fmt.Errorf("InputPath is empty")
	}
	if strings.TrimSpace(t.OutputPath) == "" {
		return fmt.Errorf("OutputPath is empty")
	}

	// Open input CSV
	inF, err := os.Open(t.InputPath)
	if err != nil {
		return fmt.Errorf("failed to open input CSV: %w", err)
	}
	defer inF.Close()

	cr := csv.NewReader(inF)
	cr.FieldsPerRecord = -1 // allow variable columns

	// Read header to find input_col index
	var inputColIndex int = 0 // default to first column
	if t.HasHeader {
		header, err := cr.Read()
		if err != nil {
			return fmt.Errorf("failed to read header: %w", err)
		}
		// Find input_col column
		inputColIndex = -1
		for i, col := range header {
			if strings.TrimSpace(col) == "input_col" {
				inputColIndex = i
				break
			}
		}
		if inputColIndex == -1 {
			// Fallback to first column if input_col not found
			inputColIndex = 0
		}
	}

	// 1) Load already processed inputs from output file if it exists
	alreadyProcessed := make(map[string]bool)
	existingData := make([][]string, 0)

	if outFile, err := os.Open(t.OutputPath); err == nil {
		defer outFile.Close()
		outReader := csv.NewReader(outFile)
		outReader.FieldsPerRecord = -1
		outReader.LazyQuotes = true

		// Read header
		header, err := outReader.Read()
		if err == nil {
			existingData = append(existingData, header)

			// Read existing rows
			for {
				row, err := outReader.Read()
				if err == io.EOF {
					break
				}
				if err == nil && len(row) > 0 {
					input := strings.TrimSpace(row[inputColIndex])
					if input != "" {
						alreadyProcessed[input] = true
						existingData = append(existingData, row)
					}
				}
			}
		}
	}

	// 2) Create output directory if it doesn't exist
	outputDir := filepath.Dir(t.OutputPath)
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// 3) Open output file for writing (will overwrite)
	outF, err := os.Create(t.OutputPath)
	if err != nil {
		return fmt.Errorf("failed to create output CSV: %w", err)
	}
	defer outF.Close()

	cw := csv.NewWriter(outF)
	defer cw.Flush()

	rowIdx := 0

	seen := make(map[string]struct{}, 1024)
	ordered := make([]string, 0, 1024)

	for {
		record, err := cr.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("failed reading CSV row %d: %w", rowIdx, err)
		}
		rowIdx++

		// Check if record has enough columns
		if len(record) <= inputColIndex {
			continue
		}

		input := strings.TrimSpace(record[inputColIndex])
		if input == "" {
			continue
		}

		// Skip if already processed
		if alreadyProcessed[input] {
			continue
		}

		if _, ok := seen[input]; ok {
			continue
		}
		seen[input] = struct{}{}
		ordered = append(ordered, input)
	}

	// 3) Write existing data first (header + already processed rows)
	for _, row := range existingData {
		if err := cw.Write(row); err != nil {
			return fmt.Errorf("failed writing existing row: %w", err)
		}
	}

	// If no existing data, write header
	if len(existingData) == 0 {
		if err := cw.Write([]string{"input", "output", "latency_ms"}); err != nil {
			return fmt.Errorf("failed writing output header: %w", err)
		}
	}

	// 4) Translate each new unique input and append to output
	processed := 0
	for i, input := range ordered {
		start := time.Now()
		out, trErr := t.LLMClient.Translate(ctx, input)
		latency := time.Since(start).Milliseconds()

		llmOut := strings.TrimSpace(out)
		if trErr != nil || llmOut == "" {
			// Keep pipeline going; optionally include error text in logs, not CSV.
			llmOut = "N/A"
		}

		if err := cw.Write([]string{input, llmOut, strconv.FormatInt(latency, 10)}); err != nil {
			return fmt.Errorf("failed writing output row %d: %w", i+1, err)
		}
		processed++
		fmt.Printf("Processed %d/%d: %s\n", processed, len(ordered), input)
	}

	cw.Flush()
	if err := cw.Error(); err != nil {
		return fmt.Errorf("failed flushing output CSV: %w", err)
	}
	fmt.Printf("Wrote output CSV: %s (new rows=%d, total rows=%d, skipped=%d)\n",
		t.OutputPath, processed, len(existingData)-1+processed, len(alreadyProcessed))

	return nil
}
