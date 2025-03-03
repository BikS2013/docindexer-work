"""Configuration management for DocIndexer."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Configuration:
    """Configuration class for DocIndexer.
    
    This class manages loading and merging configuration from different sources:
    1. Command-line arguments (highest priority)
    2. Local configuration file (./.config.json)
    3. Global configuration file (~/.docindexer/config.json)
    """
    
    def __init__(self):
        """Initialize a new Configuration instance."""
        self._local_config_path = Path("./config.json")
        self._global_config_path = Path.home() / ".docindexer" / "config.json"
        
        # Configuration values from different sources
        self._global_config: Dict[str, Any] = {}
        self._local_config: Dict[str, Any] = {}
        self._cli_args: Dict[str, Any] = {}
        
        # Merged configuration (with command-line taking precedence)
        self._config: Dict[str, Any] = {}
        
    def load_global_config(self) -> None:
        """Load configuration from the global config file."""
        if self._global_config_path.exists():
            try:
                with open(self._global_config_path, 'r') as f:
                    self._global_config = json.load(f)
                logger.debug(f"Loaded global config from {self._global_config_path}")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse global config file at {self._global_config_path}")
            except Exception as e:
                logger.warning(f"Error loading global config: {str(e)}")
    
    def load_local_config(self) -> None:
        """Load configuration from the local config file."""
        if self._local_config_path.exists():
            try:
                with open(self._local_config_path, 'r') as f:
                    self._local_config = json.load(f)
                logger.debug(f"Loaded local config from {self._local_config_path}")
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse local config file at {self._local_config_path}")
            except Exception as e:
                logger.warning(f"Error loading local config: {str(e)}")
    
    def set_cli_args(self, args: Dict[str, Any]) -> None:
        """Set command-line arguments in the configuration.
        
        Args:
            args: Dictionary of command-line arguments
        """
        self._cli_args = {k: v for k, v in args.items() if v is not None}
        self._update_merged_config()
    
    def _update_merged_config(self) -> None:
        """Update the merged configuration with values from all sources."""
        # Start with global config (lowest priority)
        self._config = self._global_config.copy()
        
        # Add local config (overrides global)
        for key, value in self._local_config.items():
            self._config[key] = value
        
        # Add CLI args (highest priority)
        for key, value in self._cli_args.items():
            self._config[key] = value
    
    def create_local_config(self) -> bool:
        """Create a local configuration file with the current effective configuration.
        
        Returns:
            True if the configuration file was created successfully
        """
        try:
            with open(self._local_config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Created local config file at {self._local_config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create local config file: {str(e)}")
            return False
    
    def create_global_config(self) -> bool:
        """Create a global configuration file with the current effective configuration.
        
        Returns:
            True if the configuration file was created successfully
        """
        try:
            # Ensure the directory exists
            self._global_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._global_config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
            logger.info(f"Created global config file at {self._global_config_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create global config file: {str(e)}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key is not found
            
        Returns:
            Configuration value for the key
        """
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary syntax.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value for the key
            
        Raises:
            KeyError: If the key is not found in the configuration
        """
        if key in self._config:
            return self._config[key]
        raise KeyError(f"Configuration key '{key}' not found")
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the configuration.
        
        Args:
            key: Configuration key
            
        Returns:
            True if the key exists in the configuration
        """
        return key in self._config
    
    def keys(self) -> Set[str]:
        """Get all configuration keys.
        
        Returns:
            Set of all configuration keys
        """
        return set(self._config.keys())
    
    def as_dict(self) -> Dict[str, Any]:
        """Get the effective configuration as a dictionary.
        
        Returns:
            Dictionary containing all configuration values
        """
        return self._config.copy()
        
    def load_config(self) -> None:
        """Load configuration from all available sources and update the merged config."""
        self.load_global_config()
        self.load_local_config()
        self._update_merged_config()