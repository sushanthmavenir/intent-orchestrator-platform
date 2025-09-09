"""
Configuration Loader
====================

Loads and manages configuration from YAML files and environment variables.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Configuration loader with environment variable support"""
    
    def __init__(self):
        self.config_dir = Path(__file__).parent
        self._config_cache: Dict[str, Any] = {}
    
    def load_classification_config(self) -> Dict[str, Any]:
        """
        Load classification configuration
        
        Returns:
            Classification configuration dictionary
        """
        if 'classification' in self._config_cache:
            return self._config_cache['classification']
        
        # Load from YAML file
        config_file = self.config_dir / 'classification_config.yaml'
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config)
        
        # Apply development mode adjustments
        config = self._apply_development_mode(config)
        
        # Cache the configuration
        self._config_cache['classification'] = config
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides
        
        Args:
            config: Base configuration
            
        Returns:
            Configuration with environment overrides applied
        """
        # Override Groq API key from environment
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            if 'classification' not in config:
                config['classification'] = {}
            if 'llm' not in config['classification']:
                config['classification']['llm'] = {}
            config['classification']['llm']['api_key'] = groq_api_key
        
        # Override classification mode from environment
        classification_mode = os.getenv('CLASSIFICATION_MODE')
        if classification_mode and classification_mode in ['pattern', 'llm', 'hybrid']:
            if 'classification' not in config:
                config['classification'] = {}
            config['classification']['mode'] = classification_mode
        
        # Override debug mode from environment
        debug_classification = os.getenv('DEBUG_CLASSIFICATION')
        if debug_classification:
            if 'development' not in config:
                config['development'] = {}
            config['development']['debug_classification'] = debug_classification.lower() == 'true'
        
        return config
    
    def _apply_development_mode(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply development mode adjustments
        
        Args:
            config: Configuration with environment overrides
            
        Returns:
            Configuration with development adjustments
        """
        dev_config = config.get('development', {})
        classification_config = config.get('classification', {})
        
        # Force pattern mode if no API key is available and development setting is enabled
        if dev_config.get('force_pattern_without_api_key', True):
            api_key = classification_config.get('llm', {}).get('api_key')
            if not api_key and classification_config.get('mode') in ['llm', 'hybrid']:
                config['classification']['mode'] = 'pattern'
                print("INFO: No API key found, switching to pattern mode")
        
        return config
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM-specific configuration
        
        Returns:
            LLM configuration dictionary
        """
        config = self.load_classification_config()
        return config.get('classification', {}).get('llm', {})
    
    def get_pattern_config(self) -> Dict[str, Any]:
        """
        Get pattern matching configuration
        
        Returns:
            Pattern configuration dictionary
        """
        config = self.load_classification_config()
        return config.get('classification', {}).get('pattern', {})
    
    def get_hybrid_config(self) -> Dict[str, Any]:
        """
        Get hybrid mode configuration
        
        Returns:
            Hybrid configuration dictionary
        """
        config = self.load_classification_config()
        return config.get('classification', {}).get('hybrid', {})
    
    def is_debug_mode(self) -> bool:
        """
        Check if debug mode is enabled
        
        Returns:
            True if debug mode is enabled
        """
        config = self.load_classification_config()
        return config.get('development', {}).get('debug_classification', False)
    
    def is_test_mode(self) -> bool:
        """
        Check if test mode is enabled
        
        Returns:
            True if test mode is enabled
        """
        config = self.load_classification_config()
        return config.get('development', {}).get('test_mode', False)
    
    def get_classification_mode(self) -> str:
        """
        Get the current classification mode
        
        Returns:
            Classification mode: 'pattern', 'llm', or 'hybrid'
        """
        config = self.load_classification_config()
        return config.get('classification', {}).get('mode', 'pattern')
    
    def clear_cache(self):
        """Clear configuration cache (useful for testing)"""
        self._config_cache.clear()


# Global config loader instance
config_loader = ConfigLoader()