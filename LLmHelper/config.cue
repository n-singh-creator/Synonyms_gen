package config

// Schema definition 
#LLMProfile: {
	model_name:    string
	temperature:   float & >=0.0 & <=2.0
	max_tokens:    int & >0
	system_prompt: string
}

llm_configs: {
	// Current LLM configuration for translating search keywords to Japanese
	explain_query_gpt_5_search: #LLMProfile & {
		model_name:  "openai/gpt-5-search-api-2025-10-14"
		temperature: 0.2
		max_tokens:  128
		system_prompt: """
			You are given a raw user-typed search query from Mercari.
			Your job is to explain, in clear English, what item(s) the user is trying to find.
			
			CRITICAL: Always respond in English, regardless of the input language.
			If the query is in Japanese, Chinese, Korean, or any other language, translate the key terms and explain in English.
			
			The explanation will be used by a human annotator to judge SERP relevance.
			Be concise and concrete: mention the likely product category, key attributes (brand/model, size, color, condition, material), and any intent (buy/sell, bundle, replacement part) if implied.
			If the query is ambiguous, list the 1–2 most likely interpretations.
			Do not add extra recommendations, do not rewrite the query, and do not infer personal details.
			
			Output format:
			1-2 short sentences (or up to 2 bullet points if ambiguous).
			Always in English only.
			"""
	}

}
