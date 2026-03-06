package synonymgenrator

import (
	"fmt"
	"log"

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

	// Load the package "example" from the current directory.
	// We don't need to specify a config in this example.
	insts := load.Instances([]string{"./LLM"}, nil)

	// The current directory just has one file without any build tags,
	// and that file belongs to the example package.
	// So we get a single instance as a result.
	v := ctx.BuildInstance(insts[0])
	if err := v.Err(); err != nil {
		log.Fatal(err)
	}
	path := cue.ParsePath(fmt.Sprintf(`llm_configs["%s"]`, profileKey))

	// Lookup the 'output' field and print it out
	profileKeyConfig := v.LookupPath(path)
	if profileKeyConfig.Err() != nil {
		log.Fatalf("Error loading config for profile %s: %v", profileKey, profileKeyConfig.Err())
		return LLMProfile{}, profileKeyConfig.Err()
	}
	fmt.Println(profileKeyConfig)
	var profile LLMProfile
	if err := profileKeyConfig.Decode(&profile); err != nil {
		log.Fatalf("Error decoding config for profile %s: %v", profileKey, err)
		return LLMProfile{}, err
	}
	return profile, nil
}
