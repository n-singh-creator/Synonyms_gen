package main

import (
	"context"
	"fmt"
	"log"
	"os"

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
}
