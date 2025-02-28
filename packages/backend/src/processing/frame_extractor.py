#!/usr/bin/env python3
"""
Frame extractor for video processing
"""

import os
import subprocess
import numpy as np
import cv2
import logging
import tempfile
from typing import List, Dict, Any, Tuple, Optional, Generator

# Set up logging
logger = logging.getLogger(__name__)

class FrameExtractor:
    """
    Extract frames from video files for processing
    """
    def __init__(
        self, 
        temp_dir: str = None,
        max_frames_in_memory: int = 30,
        resize_factor: float = 1.0
    ):
        """
        Initialize frame extractor
        
        Args:
            temp_dir: Directory to store temporary files
            max_frames_in_memory: Maximum number of frames to keep in memory
            resize_factor: Factor to resize frames (1.0 = original size)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_frames_in_memory = max_frames_in_memory
        self.resize_factor = resize_factor
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video information (resolution, fps, etc.)
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            # Get codec info
            fourcc_int = int(cap.get(cv2.CAP_PROP_FOURCC))
            fourcc = chr(fourcc_int & 0xFF) + chr((fourcc_int >> 8) & 0xFF) + chr((fourcc_int >> 16) & 0xFF) + chr((fourcc_int >> 24) & 0xFF)
            
            cap.release()
            
            return {
                "width": width,
                "height": height,
                "fps": fps,
                "total_frames": total_frames,
                "duration": duration,
                "fourcc": fourcc
            }
        
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise
    
    def extract_all_frames(self, video_path: str) -> List[np.ndarray]:
        """
        Extract all frames from a video file into memory
        Warning: This can use a lot of memory for long videos
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of frames as numpy arrays
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize if needed
                if self.resize_factor != 1.0:
                    h, w = frame.shape[:2]
                    new_h, new_w = int(h * self.resize_factor), int(w * self.resize_factor)
                    frame = cv2.resize(frame, (new_w, new_h))
                
                frames.append(frame)
            
            cap.release()
            logger.info(f"Extracted {len(frames)} frames from {video_path}")
            
            return frames
        
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            if 'cap' in locals() and cap is not None:
                cap.release()
            raise
    
    def extract_to_disk(self, video_path: str, output_dir: str = None) -> str:
        """
        Extract all frames from a video to disk
        Useful for long videos that don't fit in memory
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save frames (defaults to a temp dir)
            
        Returns:
            Path to directory containing frames
        """
        try:
            # Create output directory
            output_dir = output_dir or os.path.join(
                self.temp_dir, 
                f"frames_{os.path.basename(video_path)}_{os.urandom(4).hex()}"
            )
            os.makedirs(output_dir, exist_ok=True)
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            # Get frame count for padding frame numbers
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_digits = len(str(total_frames)) + 1
            
            # Extract frames
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize if needed
                if self.resize_factor != 1.0:
                    h, w = frame.shape[:2]
                    new_h, new_w = int(h * self.resize_factor), int(w * self.resize_factor)
                    frame = cv2.resize(frame, (new_w, new_h))
                
                # Save frame to disk
                frame_path = os.path.join(
                    output_dir, 
                    f"frame_{frame_count:0{frame_digits}d}.png"
                )
                cv2.imwrite(frame_path, frame)
                
                frame_count += 1
                
                # Log progress periodically
                if frame_count % 100 == 0:
                    logger.info(f"Extracted {frame_count} frames to {output_dir}")
            
            cap.release()
            logger.info(f"Extracted {frame_count} frames to {output_dir}")
            
            return output_dir
        
        except Exception as e:
            logger.error(f"Error extracting frames to disk: {str(e)}")
            if 'cap' in locals() and cap is not None:
                cap.release()
            raise
    
    def extract_frames_batch(
        self, 
        video_path: str, 
        batch_size: int = None
    ) -> Generator[List[np.ndarray], None, None]:
        """
        Extract frames in batches to avoid memory issues
        
        Args:
            video_path: Path to video file
            batch_size: Number of frames per batch
            
        Yields:
            Batches of frames
        """
        batch_size = batch_size or self.max_frames_in_memory
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_count = 0
            
            current_batch = []
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Resize if needed
                if self.resize_factor != 1.0:
                    h, w = frame.shape[:2]
                    new_h, new_w = int(h * self.resize_factor), int(w * self.resize_factor)
                    frame = cv2.resize(frame, (new_w, new_h))
                
                current_batch.append(frame)
                frame_count += 1
                
                # If we've reached the batch size, yield the batch
                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []
                
                # Log progress periodically
                if frame_count % 100 == 0:
                    logger.info(f"Extracted {frame_count}/{total_frames} frames")
            
            # Yield any remaining frames
            if current_batch:
                yield current_batch
            
            cap.release()
            logger.info(f"Finished extracting {frame_count} frames in batches")
        
        except Exception as e:
            logger.error(f"Error extracting frames in batches: {str(e)}")
            if 'cap' in locals() and cap is not None:
                cap.release()
            raise
    
    def load_frames_from_disk(self, frames_dir: str) -> Generator[np.ndarray, None, None]:
        """
        Load frames from disk in order
        
        Args:
            frames_dir: Directory containing frame images
            
        Yields:
            Frames as numpy arrays
        """
        try:
            # Get all frame files and sort them
            frame_files = [f for f in os.listdir(frames_dir) if f.startswith("frame_") and f.endswith(".png")]
            frame_files.sort(key=lambda f: int(f.split("_")[1].split(".")[0]))
            
            logger.info(f"Loading {len(frame_files)} frames from {frames_dir}")
            
            # Load frames one by one
            for frame_file in frame_files:
                frame_path = os.path.join(frames_dir, frame_file)
                frame = cv2.imread(frame_path)
                
                if frame is None:
                    logger.warning(f"Could not read frame: {frame_path}")
                    continue
                
                yield frame
                
                # Delete file after loading to save space
                os.remove(frame_path)
            
            logger.info(f"Finished loading frames from {frames_dir}")
            
            # Clean up directory
            try:
                os.rmdir(frames_dir)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Error loading frames from disk: {str(e)}")
            raise
    
    def extract_with_ffmpeg(self, video_path: str, output_dir: str = None) -> str:
        """
        Extract frames using FFmpeg (faster than OpenCV for some videos)
        
        Args:
            video_path: Path to video file
            output_dir: Directory to save frames
            
        Returns:
            Path to directory containing frames
        """
        try:
            # Create output directory
            output_dir = output_dir or os.path.join(
                self.temp_dir, 
                f"frames_{os.path.basename(video_path)}_{os.urandom(4).hex()}"
            )
            os.makedirs(output_dir, exist_ok=True)
            
            # Construct FFmpeg command
            output_pattern = os.path.join(output_dir, "frame_%04d.png")
            
            # Resize if needed
            resize_option = ""
            if self.resize_factor != 1.0:
                resize_option = f"-vf scale=iw*{self.resize_factor}:ih*{self.resize_factor}"
            
            cmd = [
                "ffmpeg", 
                "-i", video_path, 
                "-q:v", "1", 
                resize_option,
                output_pattern
            ]
            
            # Run FFmpeg
            subprocess.run(
                " ".join([str(c) for c in cmd if c]), 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Count extracted frames
            frame_count = len([f for f in os.listdir(output_dir) if f.endswith(".png")])
            logger.info(f"Extracted {frame_count} frames to {output_dir} using FFmpeg")
            
            return output_dir
            
        except Exception as e:
            logger.error(f"Error extracting frames with FFmpeg: {str(e)}")
            raise