#!/usr/bin/env python3
"""
Video assembler for processed frames
"""

import os
import subprocess
import numpy as np
import cv2
import logging
import tempfile
from typing import List, Dict, Any, Optional, Union

# Set up logging
logger = logging.getLogger(__name__)

class VideoAssembler:
    """
    Assemble processed frames into a video file
    """
    def __init__(
        self, 
        temp_dir: str = None,
        use_ffmpeg: bool = True,
        quality: str = "high"
    ):
        """
        Initialize video assembler
        
        Args:
            temp_dir: Directory for temporary files
            use_ffmpeg: Whether to use FFmpeg for assembly (better quality)
            quality: Video quality preset ("low", "medium", "high")
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.use_ffmpeg = use_ffmpeg
        self.quality = quality
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Determine available FFmpeg
        self.ffmpeg_available = False
        if self.use_ffmpeg:
            try:
                subprocess.run(
                    ["ffmpeg", "-version"], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                self.ffmpeg_available = True
                logger.info("FFmpeg available for video assembly")
            except:
                logger.warning("FFmpeg not available, falling back to OpenCV")
    
    def frames_to_video_opencv(
        self, 
        frames: List[np.ndarray], 
        output_path: str, 
        fps: float = 30.0,
        fourcc: str = "mp4v"
    ) -> bool:
        """
        Assemble frames into a video using OpenCV
        
        Args:
            frames: List of frames to assemble
            output_path: Path to save the video
            fps: Frames per second
            fourcc: Four character code for the codec
            
        Returns:
            True if successful, False otherwise
        """
        if not frames:
            logger.error("No frames to assemble")
            return False
        
        try:
            # Get dimensions from first frame
            height, width = frames[0].shape[:2]
            
            # Create video writer
            fourcc_code = cv2.VideoWriter_fourcc(*fourcc)
            out = cv2.VideoWriter(output_path, fourcc_code, fps, (width, height))
            
            # Write frames
            frame_count = 0
            for frame in frames:
                out.write(frame)
                frame_count += 1
                
                # Log progress periodically
                if frame_count % 100 == 0:
                    logger.info(f"Assembled {frame_count}/{len(frames)} frames")
            
            out.release()
            logger.info(f"Video assembled to {output_path} ({frame_count} frames)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error assembling video with OpenCV: {str(e)}")
            if 'out' in locals() and out is not None:
                out.release()
            return False
    
    def frames_to_video_ffmpeg(
        self, 
        frames: List[np.ndarray], 
        output_path: str, 
        fps: float = 30.0
    ) -> bool:
        """
        Assemble frames into a video using FFmpeg
        
        Args:
            frames: List of frames to assemble
            output_path: Path to save the video
            fps: Frames per second
            
        Returns:
            True if successful, False otherwise
        """
        if not frames:
            logger.error("No frames to assemble")
            return False
        
        if not self.ffmpeg_available:
            logger.warning("FFmpeg not available, falling back to OpenCV")
            return self.frames_to_video_opencv(frames, output_path, fps)
        
        try:
            # Create temp directory for frames
            temp_frames_dir = os.path.join(
                self.temp_dir, 
                f"frames_to_video_{os.urandom(4).hex()}"
            )
            os.makedirs(temp_frames_dir, exist_ok=True)
            
            # Write frames to disk
            frame_count = 0
            for i, frame in enumerate(frames):
                frame_path = os.path.join(temp_frames_dir, f"frame_{i:08d}.png")
                cv2.imwrite(frame_path, frame)
                frame_count += 1
                
                # Log progress periodically
                if frame_count % 100 == 0:
                    logger.info(f"Saved {frame_count}/{len(frames)} frames for FFmpeg")
            
            # Determine quality settings
            if self.quality == "high":
                crf = "18"  # Lower is better quality
                preset = "slow"
            elif self.quality == "medium":
                crf = "23"
                preset = "medium"
            else:  # low
                crf = "28"
                preset = "faster"
            
            # Construct FFmpeg command
            input_pattern = os.path.join(temp_frames_dir, "frame_%08d.png")
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-r", str(fps),  # Input frame rate
                "-i", input_pattern,  # Input files
                "-c:v", "libx264",  # Codec
                "-crf", crf,  # Quality
                "-preset", preset,  # Encoding speed/quality tradeoff
                "-pix_fmt", "yuv420p",  # Pixel format
                "-vf", "pad=width=ceil(iw/2)*2:height=ceil(ih/2)*2:color=black",  # Ensure even dimensions
                "-r", str(fps),  # Output frame rate
                output_path
            ]
            
            # Run FFmpeg
            process = subprocess.run(
                " ".join([str(c) for c in cmd]), 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            logger.info(f"Video assembled to {output_path} ({frame_count} frames)")
            
            # Clean up temp directory
            for f in os.listdir(temp_frames_dir):
                os.remove(os.path.join(temp_frames_dir, f))
            os.rmdir(temp_frames_dir)
            
            return True
            
        except Exception as e:
            logger.error(f"Error assembling video with FFmpeg: {str(e)}")
            # Try to clean up temp directory
            try:
                if 'temp_frames_dir' in locals() and os.path.exists(temp_frames_dir):
                    for f in os.listdir(temp_frames_dir):
                        os.remove(os.path.join(temp_frames_dir, f))
                    os.rmdir(temp_frames_dir)
            except:
                pass
            
            # Fall back to OpenCV
            logger.info("Falling back to OpenCV for video assembly")
            return self.frames_to_video_opencv(frames, output_path, fps)
    
    def assemble_from_disk(
        self, 
        frames_dir: str, 
        output_path: str, 
        fps: float = 30.0,
        pattern: str = "frame_*.png"
    ) -> bool:
        """
        Assemble frames from disk into a video
        
        Args:
            frames_dir: Directory containing frames
            output_path: Path to save the video
            fps: Frames per second
            pattern: Pattern to match frame files
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(frames_dir):
            logger.error(f"Frames directory does not exist: {frames_dir}")
            return False
        
        if not self.ffmpeg_available:
            logger.warning("FFmpeg not available, will read frames into memory and use OpenCV")
            # Load frames into memory
            frame_files = sorted([
                f for f in os.listdir(frames_dir) 
                if f.endswith(".png") and f.startswith("frame_")
            ], key=lambda f: int(f.split("_")[1].split(".")[0]))
            
            frames = []
            for frame_file in frame_files:
                frame_path = os.path.join(frames_dir, frame_file)
                frame = cv2.imread(frame_path)
                if frame is not None:
                    frames.append(frame)
            
            return self.frames_to_video_opencv(frames, output_path, fps)
        
        try:
            # Determine quality settings
            if self.quality == "high":
                crf = "18"  # Lower is better quality
                preset = "slow"
            elif self.quality == "medium":
                crf = "23"
                preset = "medium"
            else:  # low
                crf = "28"
                preset = "faster"
            
            # Construct FFmpeg command
            input_pattern = os.path.join(frames_dir, pattern.replace("*", "%08d"))
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file if it exists
                "-framerate", str(fps),  # Input frame rate
                "-i", input_pattern,  # Input files
                "-c:v", "libx264",  # Codec
                "-crf", crf,  # Quality
                "-preset", preset,  # Encoding speed/quality tradeoff
                "-pix_fmt", "yuv420p",  # Pixel format
                "-vf", "pad=width=ceil(iw/2)*2:height=ceil(ih/2)*2:color=black",  # Ensure even dimensions
                output_path
            ]
            
            # Run FFmpeg
            process = subprocess.run(
                " ".join([str(c) for c in cmd]), 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            logger.info(f"Video assembled to {output_path} from {frames_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error assembling video from disk: {str(e)}")
            return False
    
    def assemble(
        self, 
        frames: Union[List[np.ndarray], str], 
        output_path: str, 
        fps: float = 30.0
    ) -> bool:
        """
        Assemble frames into a video (convenience method)
        
        Args:
            frames: List of frames or directory containing frames
            output_path: Path to save the video
            fps: Frames per second
            
        Returns:
            True if successful, False otherwise
        """
        if isinstance(frames, str):
            # frames is a directory
            return self.assemble_from_disk(frames, output_path, fps)
        elif isinstance(frames, list) and len(frames) > 0:
            # frames is a list of numpy arrays
            if self.ffmpeg_available and self.use_ffmpeg:
                return self.frames_to_video_ffmpeg(frames, output_path, fps)
            else:
                return self.frames_to_video_opencv(frames, output_path, fps)
        else:
            logger.error("Invalid frames input")
            return False