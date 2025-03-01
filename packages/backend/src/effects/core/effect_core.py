#!/usr/bin/env python3
"""
Core framework for video effects
Provides a standardized interface for all effect types
"""

import os
import json
import logging
import subprocess
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class VideoEffect:
    """Base class for all video effects"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """
        Initialize the video effect
        
        Args:
            name: Name of the effect
            version: Version of the effect
        """
        self.name = name
        self.version = version
        logger.info(f"Initializing {self.name} effect (v{self.version})")
    
    def get_command(self, input_path: str, output_path: str, params: Dict[str, Any] = None) -> str:
        """
        Get the FFmpeg command for this effect
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            params: Additional parameters for the effect
            
        Returns:
            FFmpeg command string
        """
        raise NotImplementedError("Subclasses must implement get_command()")
    
    def process(self, input_path: str, output_path: str, params: Dict[str, Any] = None) -> bool:
        """
        Process a video with this effect
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            params: Additional parameters for the effect
            
        Returns:
            True if successful, False otherwise
        """
        try:
            command = self.get_command(input_path, output_path, params)
            logger.info(f"Running FFmpeg command: {command}")
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
            
            logger.info(f"Successfully processed {input_path} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return False


class EffectRegistry:
    """Registry for video effects"""
    
    def __init__(self, s3_bucket: str, effects_prefix: str = "effects/"):
        """
        Initialize the registry
        
        Args:
            s3_bucket: S3 bucket containing effects
            effects_prefix: Prefix for effects in S3
        """
        self.s3_bucket = s3_bucket
        self.effects_prefix = effects_prefix
        self.s3_client = boto3.client('s3')
        self.effects_cache = {}
        self.manifest = None
    
    def load_manifest(self) -> Dict[str, Any]:
        """
        Load the effects manifest from S3
        
        Returns:
            Manifest dictionary
        """
        try:
            manifest_key = f"{self.effects_prefix}manifest.json"
            logger.info(f"Loading effects manifest from s3://{self.s3_bucket}/{manifest_key}")
            
            response = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=manifest_key
            )
            
            manifest_data = json.loads(response['Body'].read().decode('utf-8'))
            self.manifest = manifest_data
            logger.info(f"Loaded manifest with {len(manifest_data['effects'])} effects")
            
            return manifest_data
        
        except ClientError as e:
            logger.warning(f"Could not load manifest: {str(e)}")
            # Return a basic manifest if we can't load one
            return {
                "version": "1.0.0",
                "effects": {
                    "silent-movie": {
                        "type": "ffmpeg",
                        "path": "silent_movie.py",
                        "version": "1.0.0"
                    },
                    "grindhouse": {
                        "type": "ffmpeg",
                        "path": "grindhouse.py",
                        "version": "1.0.0"
                    },
                    "technicolor": {
                        "type": "ffmpeg",
                        "path": "technicolor.py",
                        "version": "1.0.0"
                    }
                }
            }
        
        except Exception as e:
            logger.error(f"Error loading manifest: {str(e)}")
            return {"version": "1.0.0", "effects": {}}
    
    def download_effect(self, effect_id: str) -> Optional[str]:
        """
        Download an effect module from S3
        
        Args:
            effect_id: ID of the effect
            
        Returns:
            Path to the downloaded effect module, or None if failed
        """
        if not self.manifest:
            self.load_manifest()
        
        if effect_id not in self.manifest["effects"]:
            logger.error(f"Effect not found in manifest: {effect_id}")
            return None
        
        effect_info = self.manifest["effects"][effect_id]
        effect_path = effect_info["path"]
        effect_key = f"{self.effects_prefix}{effect_path}"
        
        try:
            # Create local directory for effects if it doesn't exist
            local_dir = os.path.join("/tmp", "video_effects")
            os.makedirs(local_dir, exist_ok=True)
            
            # Download effect module
            local_path = os.path.join(local_dir, os.path.basename(effect_path))
            logger.info(f"Downloading effect from s3://{self.s3_bucket}/{effect_key}")
            
            self.s3_client.download_file(
                self.s3_bucket,
                effect_key,
                local_path
            )
            
            # Make executable
            os.chmod(local_path, 0o755)
            logger.info(f"Downloaded effect to {local_path}")
            
            return local_path
        
        except Exception as e:
            logger.error(f"Error downloading effect: {str(e)}")
            return None
    
    def get_effect_command(self, effect_id: str, input_path: str, output_path: str) -> Optional[str]:
        """
        Get the command for an effect
        
        Args:
            effect_id: ID of the effect
            input_path: Path to input video
            output_path: Path to output video
            
        Returns:
            FFmpeg command for the effect, or None if failed
        """
        # Normalize effect ID (handle variations in naming)
        effect_id = self._normalize_effect_id(effect_id)
        
        # Try to download the effect if not already cached
        if effect_id not in self.effects_cache:
            effect_path = self.download_effect(effect_id)
            if not effect_path:
                logger.error(f"Failed to download effect: {effect_id}")
                # Fall back to silent-movie if we can't find the requested effect
                if effect_id != "silent-movie":
                    logger.warning(f"Falling back to silent-movie effect")
                    return self.get_effect_command("silent-movie", input_path, output_path)
                return None
            
            self.effects_cache[effect_id] = effect_path
        
        # Import and use the effect module
        try:
            import importlib.util
            import sys
            
            effect_path = self.effects_cache[effect_id]
            module_name = f"video_effect_{effect_id}"
            
            # Load module from file
            spec = importlib.util.spec_from_file_location(module_name, effect_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # Get command from module
            if hasattr(module, "get_command"):
                return module.get_command(input_path, output_path)
            else:
                logger.error(f"Effect module {effect_id} does not have get_command() function")
                return None
            
        except Exception as e:
            logger.error(f"Error using effect {effect_id}: {str(e)}")
            return None
    
    def _normalize_effect_id(self, effect_id: str) -> str:
        """
        Normalize effect ID to handle variations in naming
        
        Args:
            effect_id: Input effect ID
            
        Returns:
            Normalized effect ID
        """
        effect_id = str(effect_id).strip().lower()
        
        # Map variations to standard IDs
        effect_map = {
            "silent": "silent-movie",
            "movie": "silent-movie",
            "silent_movie": "silent-movie",
            "silentmovie": "silent-movie",
            
            "grind": "grindhouse",
            "house": "grindhouse",
            "grind_house": "grindhouse",
            "grindhouse": "grindhouse",
            
            "tech": "technicolor",
            "color": "technicolor",
            "techni": "technicolor",
            "technicolor": "technicolor",
        }
        
        # Try exact match first
        if effect_id in self.manifest["effects"]:
            return effect_id
        
        # Try mapping
        for key, value in effect_map.items():
            if key in effect_id:
                return value
        
        # Default to silent-movie if no match
        logger.warning(f"Unknown effect ID: {effect_id}, defaulting to silent-movie")
        return "silent-movie"