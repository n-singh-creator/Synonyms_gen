package synonymgenrator

import (
	"fmt"

	"cuelang.org/go/cue"
	"cuelang.org/go/cue/cuecontext"
	"cuelang.org/go/cue/load"
)

type Config struct {
	LLMConfigs map[string]LLMProfile `json:"llm_configs"`
}

type LLMProfile struct {
	ModelID      string  `json:"model_name"`
	Temperature  float64 `json:"temperature"`
	MaxTokens    int32   `json:"max_tokens"`
	SystemPrompt string  `json:"system_prompt"`
}

func LoadConfig(profileKey string) (LLMProfile, error) {

	ctx := cuecontext.New()

	// Load the CUE config from the Synonym_genrator directory
	insts := load.Instances([]string{"./Synonym_genrator"}, nil)

	// Build the CUE instance
	v := ctx.BuildInstance(insts[0])
	if err := v.Err(); err != nil {
		return LLMProfile{}, fmt.Errorf("failed to build CUE instance: %w", err)
	}
	path := cue.ParsePath(fmt.Sprintf(`llm_configs["%s"]`, profileKey))

	// Lookup the profile configuration
	profileKeyConfig := v.LookupPath(path)
	if profileKeyConfig.Err() != nil {
		return LLMProfile{}, fmt.Errorf("error loading config for profile %s: %w", profileKey, profileKeyConfig.Err())
	}
	fmt.Println(profileKeyConfig)
	var profile LLMProfile
	if err := profileKeyConfig.Decode(&profile); err != nil {
		return LLMProfile{}, fmt.Errorf("error decoding config for profile %s: %w", profileKey, err)
	}
	return profile, nil
}
