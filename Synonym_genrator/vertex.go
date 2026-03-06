package synonymgenrator

import (
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/openai/openai-go/v3"
	"github.com/openai/openai-go/v3/option"
	"github.com/openai/openai-go/v3/responses"
)

type LLMClient struct {
	Profile LLMProfile
}

// Translate takes a query string and returns the translation (or N/A).
func (l *LLMClient) Translate(ctx context.Context, query string) (string, error) {
	client := openai.NewClient(
		option.WithAPIKey(os.Getenv("LITELLM_API_KEY")),
		option.WithBaseURL("https://litellm.mercari.in/v1"),
	)

	// Pick a model. You can swap this for another chat-capable model constant as needed.
	model := l.Profile.ModelID
	println("Input - ", query)
	resp, err := client.Responses.New(ctx, responses.ResponseNewParams{
		Model: model,
		Input: responses.ResponseNewParamsInputUnion{
			OfString: openai.String(query),
		},

		// System prompt equivalent
		Instructions: openai.String(l.Profile.SystemPrompt),

		Temperature:     openai.Float(l.Profile.Temperature),
		MaxOutputTokens: openai.Int(int64(l.Profile.MaxTokens)),
	})
	if err != nil {
		return "", fmt.Errorf("failed to generate content: %w", err)
	}

	out := strings.TrimSpace(resp.OutputText())
	if out == "" {
		return "", fmt.Errorf("no translation found in response")
	}
	println("output - ", out)

	return out, nil
}
