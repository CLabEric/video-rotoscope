#!/usr/bin/env python3
"""
Processing pipeline for video effects
"""

import os
import time
import logging
import tempfile
from typing import Dict, Any, Callable, Optional, List

from src.effects.scanner_darkly import ScannerDarklyEffect
from .frame_extractor import FrameExtractor
from .video_assembler import VideoAssembler

# Set up logging
logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """
    Pipeline for video processing with various effects
    """
    def __init__(
        self, 
        config: Dict[str, Any] = None,
        temp_dir: str = None,
        model_dir: str = None
    ):
        """
        Initialize processing pipeline
        
        Args:
            config: Configuration dictionary
            temp_dir: Directory for temporary files
            model_dir: Directory containing model weights
        """
        # Default configuration
        self.config = {
            "use_gpu": True,
            "batch_size": 30,
            "output_quality": "high",
            "max_memory_usage_gb": 4,
            "resize_factor": 1.0,
            "use_ffmpeg": True,
            "scanner_darkly": {
                "edge_strength": 0.8,
                "edge_thickness": 1.5,
                "edge_threshold": 0.3,
                "num_colors": 8,
                "color_method": "kmeans",
                "smoothing": 0.6,
                "saturation": 1.2,
                "temporal_smoothing": 0.3,
                "preserve_black": True
            }
        }
        
        # Update with user config
        if config:
            self._deep_update(self.config, config)
        
        # Set up directories
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.model_dir = model_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "model_weights")
        
        # Ensure directories exist
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Initialize components
        self.frame_extractor = FrameExtractor(
            temp_dir=self.temp_dir,
            max_frames_in_memory=self.config["batch_size"],
            resize_factor=self.config["resize_factor"]
        )
        
        self.video_assembler = VideoAssembler(
            temp_dir=self.temp_dir,
            use_ffmpeg=self.config["use_ffmpeg"],
            quality=self.config["output_quality"]
        )
        
        # Initialize effects
        self.scanner_darkly = None  # Lazy initialization
    
    def _deep_update(self, d: Dict, u: Dict) -> Dict:
        """
        Deep update a dictionary (helper method)
        Updates nested dictionaries without overwriting the entire subtree
        
        Args:
            d: Dictionary to update
            u: Dictionary with updates
            
        Returns:
            Updated dictionary
        """
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self._deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    def _get_scanner_darkly(self) -> ScannerDarklyEffect:
        """
        Get or initialize the Scanner Darkly effect
        
        Returns:
            Initialized Scanner Darkly effect
        """
        if self.scanner_darkly is None:
            # Determine model path
            model_path = os.path.join(self.model_dir, "hed_model.pth")
            
            # Initialize the effect
            self.scanner_darkly = ScannerDarklyEffect(
                config=self.config["scanner_darkly"],
                model_path=model_path if os.path.exists(model_path) else None
            )
        
        return self.scanner_darkly
    
    def process_video(
        self,
        input_path: str,
        output_path: str,
        effect: str = "scanner_darkly",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Process a video with the specified effect
        
        Args:
            input_path: Path to input video
            output_path: Path to save the processed video
            effect: Name of the effect to apply
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if processing was successful, False otherwise
        """
        start_time = time.time()
        logger.info(f"Starting video processing: {input_path} -> {output_path}")
        logger.info(f"Effect: {effect}")
        
        try:
            # Get video info
            video_info = self.frame_extractor.get_video_info(input_path)
            logger.info(f"Video info: {video_info}")
            
            # Determine processing strategy based on video size and config
            total_frames = video_info["total_frames"]
            
            # Estimated memory usage per frame (MB)
            # Assuming BGR format (3 bytes per pixel)
            frame_memory_mb = (video_info["width"] * video_info["height"] * 3) / (1024 * 1024)
            
            # Memory usage for processing (original + processed frames)
            processing_memory_gb = (frame_memory_mb * self.config["batch_size"] * 2) / 1024
            
            logger.info(f"Estimated memory usage per batch: {processing_memory_gb:.2f} GB")
            
            # Select processing method based on memory constraints
            use_disk_frames = (
                processing_memory_gb > self.config["max_memory_usage_gb"] or
                total_frames > 1000  # Large videos go to disk regardless
            )
            
            # Process with the selected method
            if use_disk_frames:
                logger.info("Using disk-based processing for large video")
                return self._process_video_disk(
                    input_path, output_path, effect, video_info, progress_callback
                )
            else:
                logger.info("Using in-memory processing")
                return self._process_video_memory(
                    input_path, output_path, effect, video_info, progress_callback
                )
                
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}", exc_info=True)
            return False
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"Video processing completed in {elapsed_time:.2f} seconds")
    
    def _process_video_memory(
        self,
        input_path: str,
        output_path: str,
        effect: str,
        video_info: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Process a video in memory
        
        Args:
            input_path: Path to input video
            output_path: Path to save the processed video
            effect: Name of the effect to apply
            video_info: Video information dictionary
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if processing was successful, False otherwise
        """

        try:
            # Get the effect processor
            effect_processor = self._get_effect_processor(effect)
            
            # Extract frames in batches
            total_frames = video_info["total_frames"]
            processed_count = 0
            all_processed_frames = []
            
            for batch in self.frame_extractor.extract_frames_batch(
                input_path, batch_size=self.config["batch_size"]
            ):
                # Process batch
				# Process batch
                processed_batch = effect_processor.process_batch(batch)

				# Debug info
                for i, frame in enumerate(processed_batch[:1]):  # Just check first frame
                    logger.warning(f"Processed frame shape: {frame.shape}, dtype: {frame.dtype}")
                    logger.warning(f"Frame stats - min: {frame.min()}, max: {frame.max()}, mean: {frame.mean()}")
					
                all_processed_frames.extend(processed_batch)
                
                # Update progress
                processed_count += len(batch)
                if progress_callback:
                    progress_callback(processed_count, total_frames)
                
                logger.info(f"Processed {processed_count}/{total_frames} frames")
            
            # Assemble video
            success = self.video_assembler.assemble(
                all_processed_frames, 
                output_path, 
                fps=video_info["fps"]
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error in memory-based processing: {str(e)}", exc_info=True)
            return False
    
    def _process_video_disk(
        self,
        input_path: str,
        output_path: str,
        effect: str,
        video_info: Dict[str, Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> bool:
        """
        Process a video using disk storage for frames
        
        Args:
            input_path: Path to input video
            output_path: Path to save the processed video
            effect: Name of the effect to apply
            video_info: Video information dictionary
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Get the effect processor
            effect_processor = self._get_effect_processor(effect)
            
            # Create temporary directories
            frames_dir = os.path.join(
                self.temp_dir, 
                f"frames_{os.path.basename(input_path)}_{os.urandom(4).hex()}"
            )
            processed_dir = os.path.join(
                self.temp_dir, 
                f"processed_{os.path.basename(input_path)}_{os.urandom(4).hex()}"
            )
            
            os.makedirs(frames_dir, exist_ok=True)
            os.makedirs(processed_dir, exist_ok=True)
            
            # Extract all frames to disk
            logger.info(f"Extracting frames to disk: {frames_dir}")
            self.frame_extractor.extract_to_disk(input_path, frames_dir)
            
            # Process frames in batches
            total_frames = video_info["total_frames"]
            processed_count = 0
            frame_batch = []
            frame_files = sorted([
                f for f in os.listdir(frames_dir) 
                if f.startswith("frame_") and f.endswith(".png")
            ])
            
            for i, frame_file in enumerate(frame_files):
                # Load frame
                frame_path = os.path.join(frames_dir, frame_file)
                frame = cv2.imread(frame_path)
                
                if frame is None:
                    logger.warning(f"Could not read frame: {frame_path}")
                    continue
                
                frame_batch.append(frame)
                
                # Process batch if it's full or last frame
                if len(frame_batch) >= self.config["batch_size"] or i == len(frame_files) - 1:
                    # Process batch
                    processed_batch = effect_processor.process_batch(frame_batch)
                    
                    # Save processed frames
                    for j, processed_frame in enumerate(processed_batch):
                        output_idx = processed_count + j
                        output_path = os.path.join(
                            processed_dir, 
                            f"frame_{output_idx:08d}.png"
                        )
                        cv2.imwrite(output_path, processed_frame)
                    
                    # Update progress
                    processed_count += len(frame_batch)
                    if progress_callback:
                        progress_callback(processed_count, total_frames)
                    
                    logger.info(f"Processed {processed_count}/{total_frames} frames")
                    
                    # Clear batch
                    frame_batch = []
                
                # Remove original frame to save space
                os.remove(frame_path)
            
            # Assemble video from processed frames
            logger.info("Assembling final video")
            success = self.video_assembler.assemble_from_disk(
                processed_dir, 
                output_path, 
                fps=video_info["fps"]
            )
            
            # Clean up temporary directories
            self._cleanup_dir(frames_dir)
            self._cleanup_dir(processed_dir)
            
            return success
            
        except Exception as e:
            logger.error(f"Error in disk-based processing: {str(e)}", exc_info=True)
            return False
    
    def _get_effect_processor(self, effect: str):
        """
        Get the appropriate effect processor based on effect name
        
        Args:
            effect: Name of the effect
            
        Returns:
            Effect processor object
            
        Raises:
            ValueError: If the effect is not supported
        """
        effect = effect.lower()
        
        if effect == "scanner_darkly":
            return self._get_scanner_darkly()
        else:
            raise ValueError(f"Unsupported effect: {effect}")
    
    def _cleanup_dir(self, directory: str) -> None:
        """
        Clean up a directory by removing all files and the directory itself
        
        Args:
            directory: Directory to clean up
        """
        try:
            if os.path.exists(directory):
                for f in os.listdir(directory):
                    file_path = os.path.join(directory, f)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        logger.warning(f"Error removing file {file_path}: {e}")
                
                os.rmdir(directory)
                logger.info(f"Cleaned up directory: {directory}")
        except Exception as e:
            logger.warning(f"Error cleaning up directory {directory}: {e}")