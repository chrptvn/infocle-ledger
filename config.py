import os
import json
from typing import Optional

class Config:
    """Configuration manager for the ledger application."""
    
    def __init__(self, config_file: str = "config.json"):
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Set config file path in data directory
        self.config_file = os.path.join(data_dir, config_file)
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Return default configuration
        return {
            "openai_api_key": "",
            "openai_model": "gpt-4o-mini"
        }
    
    def save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError:
            pass
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        api_key = self.config.get("openai_api_key", "")
        return api_key if api_key else None
    
    def set_openai_api_key(self, api_key: str):
        """Set OpenAI API key."""
        self.config["openai_api_key"] = api_key
        self.save_config()
    
    def get_openai_model(self) -> str:
        """Get OpenAI model name."""
        return self.config.get("openai_model", "gpt-4o-mini")
    
    def set_openai_model(self, model: str):
        """Set OpenAI model name."""
        self.config["openai_model"] = model
        self.save_config()