"""
Configuration loader for Query Explainer LLM profiles.
Loads configuration from CUE files for explaining search queries.
"""

import subprocess
import json
from typing import Dict, Any


class QueryExplainerProfile:
    """Represents the configuration for a query explanation LLM."""
    
    def __init__(self, model_name: str, temperature: float, max_tokens: int, system_prompt: str):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
    
    def __repr__(self):
        return f"QueryExplainerProfile(model={self.model_name}, temp={self.temperature})"


def load_query_explainer_config(profile_key: str) -> QueryExplainerProfile:
    """
    Loads the LLM configuration for query explanation from CUE config.
    
    Args:
        profile_key: The key of the profile to load (e.g., 'explain_query_gpt_5_search')
    
    Returns:
        QueryExplainerProfile object with the loaded configuration
    
    Raises:
        RuntimeError: If CUE evaluation fails
        KeyError: If the profile key is not found
    """
    try:
        # Export CUE config to JSON
        result = subprocess.run(
            ["cue", "export", "./LLmHelper/config.cue"],
            capture_output=True,
            text=True,
            check=True
        )
        
        config_data = json.loads(result.stdout)
        
        # Navigate to the specific profile
        if "llm_configs" not in config_data:
            raise KeyError("llm_configs not found in CUE configuration")
        
        if profile_key not in config_data["llm_configs"]:
            raise KeyError(f"Profile '{profile_key}' not found in llm_configs")
        
        profile_data = config_data["llm_configs"][profile_key]
        
        # Create and return profile object
        return QueryExplainerProfile(
            model_name=profile_data["model_name"],
            temperature=profile_data["temperature"],
            max_tokens=profile_data["max_tokens"],
            system_prompt=profile_data["system_prompt"]
        )
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to load CUE config: {e.stderr}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse CUE output as JSON: {e}")
