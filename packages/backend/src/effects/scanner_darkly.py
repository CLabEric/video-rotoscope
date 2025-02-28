#!/usr/bin/env python3
"""
Scanner Darkly effect implementation
Combines edge detection and color quantization to create a rotoscoped look
similar to the movie "A Scanner Darkly"
"""

import os
import numpy as np
import cv2
import logging
from typing import Dict, Any, Optional, List, Tuple

# Import our modules
from ..models.edge_detection import EdgeDetector
from ..models.color_quantization import ColorQuantizer

# Set up logging
logger = logging.getLogger(__name__)

class ScannerDarklyEffect:
    """
    Implements the Scanner Darkly rotoscoping effect
    """
    def __init__(
        self,
        config: Dict[str, Any] = None,
        model_path: str = None
    ):
        """
        Initialize the Scanner Darkly effect with parameters
        
        Args:
            config: Configuration dict with effect parameters
            model_path: Path to the pre-trained edge detection model
        """
        # Default configuration
        self.config = {
            # Edge detection parameters
            "edge_strength": 0.8,
            "edge_thickness": 1.5,
            "edge_threshold": 0.3,
            
            # Color quantization parameters
            "num_colors": 8,
            "color_method": "kmeans",
            "smoothing": 0.6,
            "saturation": 1.2,
            
            # Temporal parameters
            "temporal_smoothing": 0.3,
            
            # General parameters
            "preserve_black": True,
            "use_gpu": True
        }
        
        # Update with user-provided config
        if config:
            self.config.update(config)
        
        # Initialize edge detector
        self.edge_detector = EdgeDetector(
            model_path=model_path,
            use_gpu=self.config["use_gpu"],
            edge_strength=self.config["edge_strength"],
            threshold=self.config["edge_threshold"]
        )
        
        # Initialize color quantizer
        self.color_quantizer = ColorQuantizer(
            method=self.config["color_method"],
            num_colors=self.config["num_colors"],
            smoothing=self.config["smoothing"],
            saturation=self.config["saturation"],
            preserve_black=self.config["preserve_black"]
        )
        
        # Previous edge frames for temporal smoothing
        self.previous_edges = []
        self.max_previous_frames = 5
    
    def apply_temporal_smoothing(self, edges: np.ndarray) -> np.ndarray:
        """
        Apply temporal smoothing to edge frames to reduce flickering
        
        Args:
            edges: Current frame edge map
            
        Returns:
            Temporally smoothed edge map
        """
        # If no previous frames or smoothing disabled, return current edges
        if len(self.previous_edges) == 0 or self.config["temporal_smoothing"] <= 0:
            self.previous_edges.append(edges)
            if len(self.previous_edges) > self.max_previous_frames:
                self.previous_edges.pop(0)
            return edges
        
        # Create a weighted average of previous frames
        # More recent frames have higher weights
        smoothed = edges.copy() * (1.0 - self.config["temporal_smoothing"])
        
        total_weight = 0
        for i, prev in enumerate(self.previous_edges):
            # Resize previous frame if dimensions don't match
            if prev.shape != edges.shape:
                prev = cv2.resize(prev, (edges.shape[1], edges.shape[0]))
            
            # Calculate weight (more recent frames have higher weight)
            weight = self.config["temporal_smoothing"] * (i + 1) / len(self.previous_edges)
            smoothed += prev * weight
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            smoothed /= (1.0 - self.config["temporal_smoothing"] + total_weight)
        
        # Add current frame to history
        self.previous_edges.append(edges)
        if len(self.previous_edges) > self.max_previous_frames:
            self.previous_edges.pop(0)
        
        return smoothed
        
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a single frame with the Scanner Darkly effect
        Uses OpenCV DNN directly for edge detection
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Processed frame with Scanner Darkly effect
        """
        # Direct OpenCV HED implementation
        try:
            # Define paths to model files
            model_path = "model_weights/hed.caffemodel"
            prototxt_path = "model_weights/hed.prototxt"
            
            if os.path.exists(model_path) and os.path.exists(prototxt_path):
                # Load the network
                net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
                
                # Prepare the image
                height, width = frame.shape[:2]
                blob = cv2.dnn.blobFromImage(
                    frame, 
                    scalefactor=1.0, 
                    size=(width, height),
                    mean=(104.00698793, 116.66876762, 122.67891434),
                    swapRB=False, 
                    crop=False
                )
                
                # Forward pass
                net.setInput(blob)
                hed_output = net.forward()
                
                # Get edge map
                edges = hed_output[0, 0]
                
                # Apply threshold and scale
                edges = (edges > self.config["edge_threshold"]).astype(np.float32) * self.config["edge_strength"]
                
                # Apply temporal smoothing
                smoothed_edges = self.apply_temporal_smoothing(edges)
                
                # Apply color quantization with the smoothed edges
                quantized = self.color_quantizer.quantize(frame, smoothed_edges)
                
                return quantized
                
            else:
                # Fall back to simple Canny edge detection if model files not found
                logger.warning("HED model files not found, using Canny edge detection")
                
                # Convert to grayscale
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply Canny edge detection
                edges = cv2.Canny(gray, 50, 150)
                
                # Normalize to 0-1 range
                edges = edges.astype(np.float32) / 255.0
                
                # Apply temporal smoothing
                smoothed_edges = self.apply_temporal_smoothing(edges)
                
                # Apply color quantization
                quantized = self.color_quantizer.quantize(frame, smoothed_edges)
                
                return quantized
                
        except Exception as e:
            logger.error(f"Error in Scanner Darkly effect: {str(e)}")
            
            # If there's an error, return the frame with basic color quantization
            return self.color_quantizer.quantize(frame)

    def process_video(
        self, 
        input_path: str, 
        output_path: str,
        progress_callback=None
    ) -> bool:
        """
        Process a video file with the Scanner Darkly effect
        
        Args:
            input_path: Path to input video
            output_path: Path to save processed video
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Open the input video
            cap = cv2.VideoCapture(input_path)
            if not cap.isOpened():
                logger.error(f"Could not open input video: {input_path}")
                return False
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"Processing video: {width}x{height} @ {fps}fps, {total_frames} frames")
            
            # Create output video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Reset temporal smoothing
            self.previous_edges = []
            
            # Process frames
            frame_count = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process the frame
                processed = self.process_frame(frame)
                
                # Write to output
                out.write(processed)
                
                # Update progress
                frame_count += 1
                if progress_callback:
                    progress_callback(frame_count, total_frames)
                
                # Log progress periodically
                if frame_count % 100 == 0:
                    logger.info(f"Processed {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")
            
            # Release resources
            cap.release()
            out.release()
            logger.info(f"Video processing complete: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            # Clean up if there was an error
            if 'cap' in locals() and cap is not None:
                cap.release()
            if 'out' in locals() and out is not None:
                out.release()
            return False
            
    def process_batch(
        self, 
        frames: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Process a batch of frames with the Scanner Darkly effect
        Useful for parallel processing
        
        Args:
            frames: List of BGR frames
            
        Returns:
            List of processed frames
        """
        # Reset temporal smoothing if needed
        if len(frames) > 0 and (len(self.previous_edges) > self.max_previous_frames or len(self.previous_edges) == 0):
            self.previous_edges = []
        
        # Process each frame
        processed_frames = []
        for frame in frames:
            processed = self.process_frame(frame)
            processed_frames.append(processed)
            
        return processed_frames