package main

import (
	"context"
	"fmt"
	"log"
	"os"

	Convertor "nayan/m/Convertor"
	synonymgenrator "nayan/m/Synonym_genrator"
	"nayan/m/scripts"
)

func main() {
	ctx := context.Background()

	// Load configuration profile
	profileKey := "translator_gemini_3_synonyms_gen_zh_to_jp"
	profile, err := synonymgenrator.LoadConfig(profileKey)
	if err != nil {
		log.Fatalf("Failed to load config profile '%s': %v", profileKey, err)
	}

	// Create LLM client.
	llmClient := &synonymgenrator.LLMClient{
		Profile: profile,
	}

	// Input CSV file path
	inputPath := "original_query_lists/input.csv"
	// Check if input file exists
	if _, err := os.Stat(inputPath); os.IsNotExist(err) {
		log.Fatalf("Input file '%s' does not exist", inputPath)
	}

	// Output directory
	outputDir := "synonyms_genrator_output"

	// Create translator
	translator, err := scripts.NewTranslator(llmClient, profileKey, inputPath, outputDir, true)
	if err != nil {
		log.Fatalf("Failed to create translator: %v", err)
	}

	// Run translation job
	fmt.Printf("Starting translation job...\n")
	fmt.Printf("Input: %s\n", inputPath)
	fmt.Printf("Output directory: %s\n", outputDir)
	fmt.Printf("Profile: %s\n", profileKey)

	if err := translator.Run(ctx); err != nil {
		log.Fatalf("Translation job failed: %v", err)
	}

	fmt.Println("Translation job completed successfully!")

	// Convert CSV to JSON format
	csvPath := "synonyms_genrator_output/translator_gemini_3_synonyms_gen_zh_to_jp.csv"
	jsonPath := "synonyms_genrator_output/translator_gemini_3_synonyms_gen_zh_to_jp.json"

	fmt.Printf("\nConverting CSV to JSON format...\n")
	fmt.Printf("Input CSV: %s\n", csvPath)
	fmt.Printf("Output JSON: %s\n", jsonPath)

	if err := Convertor.SaveGenratorOutputToJSONFile(csvPath, jsonPath); err != nil {
		log.Fatalf("Failed to convert CSV to JSON: %v", err)
	}

	fmt.Println("CSV to JSON conversion completed successfully!")
}
