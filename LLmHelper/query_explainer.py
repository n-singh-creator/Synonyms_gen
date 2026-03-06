"""
Query Explainer Client for generating human-readable explanations of search queries.
Uses OpenAI-compatible API to explain what users are searching for.
"""

import os
from typing import Optional
from openai import OpenAI
from LLmHelper.config import QueryExplainerProfile


class QueryExplainerClient:
    """
    Client for explaining search queries using LLM.
    Generates clear explanations for human annotators to judge SERP relevance.
    """
    
    def __init__(self, profile: QueryExplainerProfile):
        """
        Initialize the Query Explainer Client.
        
        Args:
            profile: QueryExplainerProfile with model configuration
        """
        self.profile = profile
        self.client = OpenAI(
            api_key=os.getenv("LITELLM_API_KEY"),
            base_url="https://litellm.mercari.in/v1"
        )
    
    def explain_query(self, query: str) -> str:
        """
        Takes a raw user search query and returns a clear explanation.
        
        The explanation describes what item(s) the user is trying to find,
        including likely product category, key attributes (brand/model, size, 
        color, condition, material), and any implied intent.
        
        Args:
            query: The raw user search query from Mercari
        
        Returns:
            A clear, concise explanation (1-2 sentences or bullet points)
            suitable for human annotators
        
        Raises:
            Exception: If the API call fails or returns empty response
        """
        print(f"Explaining query: {query}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.profile.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.profile.system_prompt
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=self.profile.temperature,
                max_tokens=self.profile.max_tokens
            )
            
            explanation = response.choices[0].message.content.strip()
            
            if not explanation:
                raise ValueError("No explanation found in response")
            
            return explanation
            
        except Exception as e:
            raise Exception(f"Failed to generate query explanation: {str(e)}")
