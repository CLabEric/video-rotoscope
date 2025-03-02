#!/usr/bin/env python3
"""
Scanner Darkly effect using HED (Holistically-Nested Edge Detection)
Creates a rotoscoping effect similar to the one used in the movie "A Scanner Darkly"
"""

import os
import cv2
import numpy as np
import logging
import tempfile
import subprocess
from typing import List, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

class ScannerDarklyEffect:
    """
    Neural network-based rotoscoping effect using edge detection
    and color quantization
    """
    
    def __init__(
        self,
        model_path: str = None,
        prototxt_path: str = None,
        edge_strength: float = 0.8,
        edge_thickness: float = 1.5,
        num_colors: int = 8,
        color_method: str = "kmeans",
        smoothing: float = 0.6,
        saturation: float = 1.2,
        temporal_smoothing: float = 0.3,
        preserve_black: bool = True
    ):
        """
        Initialize Scanner Darkly effect
        
        Args:
            model_path: Path to the HED model weights (.caffemodel)
            prototxt_path: Path to the HED model definition (.prototxt)
            edge_strength: Strength of edges (0.0-1.0)
            edge_thickness: Thickness of edges (0.5-3.0)
            num_colors: Number of colors in output (2-16)
            color_method: Method for color quantization ('kmeans', 'bilateral', 'posterize')
            smoothing: Amount of smoothing (0.0-1.0)
            saturation: Color saturation multiplier
            temporal_smoothing: Smoothing between frames (0.0-0.9)
            preserve_black: Whether to preserve black edges
        """
        self.edge_strength = edge_strength
        self.edge_thickness = edge_thickness
        self.num_colors = num_colors
        self.color_method = color_method
        self.smoothing = smoothing
        self.saturation = saturation
        self.temporal_smoothing = temporal_smoothing
        self.preserve_black = preserve_black
        
        # Initialize model paths
        self.model_path = model_path
        self.prototxt_path = prototxt_path
        
        # For temporal smoothing
        self.prev_edges = None
        self.prev_colors = None
        
        # Try to find model files if not provided
        if not self.model_path or not self.prototxt_path:
            self._find_model_files()
        
        logger.info(f"Initialized Scanner Darkly effect (v{VERSION})")
        logger.info(f"Using model: {self.model_path}")
        logger.info(f"Using prototxt: {self.prototxt_path}")
    
    def _find_model_files(self):
        """Find HED model files in common locations"""
        # Check common locations
        search_paths = [
            # Current directory
            os.path.dirname(os.path.abspath(__file__)),
            # Model weights directory
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "model_weights"),
            # /opt/video-processor
            "/opt/video-processor",
            # /opt/video-processor/models
            "/opt/video-processor/models",
            # /tmp/video-processor
            "/tmp/video-processor"
        ]
        
        for path in search_paths:
            potential_caffemodel = os.path.join(path, "hed.caffemodel")
            potential_prototxt = os.path.join(path, "hed.prototxt")
            
            if os.path.exists(potential_caffemodel) and os.path.exists(potential_prototxt):
                logger.info(f"Found model files in {path}")
                self.model_path = potential_caffemodel
                self.prototxt_path = potential_prototxt
                return
        
        # If not found, try to download from S3 to a temporary location
        logger.warning("Model files not found in common locations, will try to download from S3")
        self._download_model_files()
    
    def _download_model_files(self):
        """Download model files from S3 if available"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Create a temporary directory for models
            model_dir = os.path.join(tempfile.gettempdir(), "scanner_darkly_models")
            os.makedirs(model_dir, exist_ok=True)
            
            # Get the current S3 bucket from environment
            bucket_name = os.environ.get("BUCKET_NAME")
            if not bucket_name:
                logger.error("BUCKET_NAME environment variable not set")
                return
            
            # Initialize S3 client
            s3 = boto3.client("s3")
            
            # Try to download model files
            model_s3_key = "effects/neural/models/hed.caffemodel"
            prototxt_s3_key = "effects/neural/models/hed.prototxt"
            
            model_path = os.path.join(model_dir, "hed.caffemodel")
            prototxt_path = os.path.join(model_dir, "hed.prototxt")
            
            logger.info(f"Downloading model from s3://{bucket_name}/{model_s3_key}")
            s3.download_file(bucket_name, model_s3_key, model_path)
            
            logger.info(f"Downloading prototxt from s3://{bucket_name}/{prototxt_s3_key}")
            s3.download_file(bucket_name, prototxt_s3_key, prototxt_path)
            
            logger.info("Model files downloaded successfully")
            self.model_path = model_path
            self.prototxt_path = prototxt_path
            
        except ImportError:
            logger.error("boto3 not available, cannot download model files")
        except ClientError as e:
            logger.error(f"Error downloading model files: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error downloading model files: {str(e)}")
    
    def _load_neural_network(self):
        """
        Load the HED neural network model
        
        Returns:
            OpenCV DNN model or None if failed
        """
        try:
            if not self.model_path or not self.prototxt_path:
                logger.error("Model paths not set")
                return None
            
            if not os.path.exists(self.model_path) or not os.path.exists(self.prototxt_path):
                logger.error(f"Model file not found: {self.model_path}")
                logger.error(f"Prototxt file not found: {self.prototxt_path}")
                return None
            
            logger.info("Loading HED model")
            net = cv2.dnn.readNetFromCaffe(self.prototxt_path, self.model_path)
            logger.info("HED model loaded successfully")
            return net
        
        except Exception as e:
            logger.error(f"Error loading neural network: {str(e)}")
            return None
    
    def _detect_edges(self, frame, net):
        """
        Detect edges using HED neural network
        
        Args:
            frame: Input frame
            net: Neural network model
            
        Returns:
            Edge map normalized to 0-1
        """
        try:
            height, width = frame.shape[:2]
            
            # Prepare the input blob for the network
            blob = cv2.dnn.blobFromImage(
                frame, 
                scalefactor=1.0, 
                size=(width, height),
                mean=(104.00698793, 116.66876762, 122.67891434),
                swapRB=False, 
                crop=False
            )
            
            # Set the input and run forward pass
            net.setInput(blob)
            edges = net.forward()[0, 0]
            
            # Apply temporal smoothing if enabled
            if self.prev_edges is not None and self.temporal_smoothing > 0:
                edges = (1 - self.temporal_smoothing) * edges + self.temporal_smoothing * self.prev_edges
            
            # Update previous edges
            self.prev_edges = edges.copy()
            
            # Normalize and amplify edges
            edges = cv2.normalize(edges, None, 0, 1, cv2.NORM_MINMAX)
            edges = np.power(edges, 1.0 - self.edge_strength * 0.5)  # Adjust edge strength
            
            return edges
            
        except Exception as e:
            logger.error(f"Error detecting edges: {str(e)}")
            return np.zeros((height, width), dtype=np.float32)
    
    def _enhance_edges(self, edges):
        """
        Enhance and thicken edges
        
        Args:
            edges: Edge map (0-1)
            
        Returns:
            Enhanced binary edge map
        """
        try:
            # Threshold edges to create binary mask
            _, binary_edges = cv2.threshold(
                (edges * 255).astype(np.uint8), 
                int(50 * (1 - self.edge_strength)),  # Adaptive threshold based on edge strength
                255, 
                cv2.THRESH_BINARY
            )
            
            # Apply dilation to thicken edges
            if self.edge_thickness > 1.0:
                kernel_size = max(1, int(self.edge_thickness * 1.5))
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                binary_edges = cv2.dilate(binary_edges, kernel, iterations=1)
            
            # Apply thinning if needed
            if self.edge_thickness < 1.0:
                try:
                    binary_edges = cv2.ximgproc.thinning(binary_edges)
                except:
                    pass  # Ignore if ximgproc not available
            
            return binary_edges
            
        except Exception as e:
            logger.error(f"Error enhancing edges: {str(e)}")
            return np.zeros_like(edges, dtype=np.uint8)
    
    def _quantize_colors(self, frame):
        """
        Apply color quantization to reduce the number of colors
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Color quantized frame
        """
        try:
            # Apply bilateral blur for smoothing if enabled
            if self.smoothing > 0:
                sigma = 15 * self.smoothing
                d = int(5 * self.smoothing) * 2 + 1
                frame = cv2.bilateralFilter(frame, d, sigma, sigma)
            
            # Choose quantization method
            if self.color_method == "kmeans":
                return self._quantize_kmeans(frame)
            elif self.color_method == "bilateral":
                return self._quantize_bilateral(frame)
            else:  # posterize
                return self._quantize_posterize(frame)
                
        except Exception as e:
            logger.error(f"Error quantizing colors: {str(e)}")
            return frame
    
    def _quantize_kmeans(self, frame):
        """Apply k-means clustering for color quantization"""
        try:
            # Convert to LAB color space for better color quantization
            lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            
            # Reshape for k-means
            pixels = lab.reshape(-1, 3).astype(np.float32)
            
            # Set up k-means parameters
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            k = self.num_colors
            
            # Apply k-means clustering
            _, labels, centers = cv2.kmeans(
                pixels, 
                k, 
                None, 
                criteria, 
                10, 
                cv2.KMEANS_RANDOM_CENTERS
            )
            
            # Map pixels to their closest center
            centers = centers.astype(np.uint8)
            quantized_lab = centers[labels.flatten()].reshape(frame.shape)
            
            # Apply saturation adjustment in LAB space
            if self.saturation != 1.0:
                # LAB: L (0-100), a (-128 to 127), b (-128 to 127)
                # Adjust a, b channels (color components)
                quantized_lab[:, :, 1] = np.clip(
                    quantized_lab[:, :, 1] * self.saturation, 
                    -128, 
                    127
                ).astype(np.uint8)
                
                quantized_lab[:, :, 2] = np.clip(
                    quantized_lab[:, :, 2] * self.saturation, 
                    -128, 
                    127
                ).astype(np.uint8)
            
            # Convert back to BGR
            quantized = cv2.cvtColor(quantized_lab, cv2.COLOR_LAB2BGR)
            
            # Apply temporal smoothing if enabled
            if self.prev_colors is not None and self.temporal_smoothing > 0:
                quantized = cv2.addWeighted(
                    quantized, 
                    1 - self.temporal_smoothing, 
                    self.prev_colors, 
                    self.temporal_smoothing, 
                    0
                )
            
            # Update previous colors
            self.prev_colors = quantized.copy()
            
            return quantized
            
        except Exception as e:
            logger.error(f"Error in k-means quantization: {str(e)}")
            return frame
    
    def _quantize_bilateral(self, frame):
        """Apply bilateral filtering for color simplification"""
        try:
            # Apply strong bilateral filtering multiple times
            result = frame.copy()
            iterations = max(1, int(3 * self.smoothing))
            
            for _ in range(iterations):
                result = cv2.bilateralFilter(
                    result, 
                    d=9, 
                    sigmaColor=75, 
                    sigmaSpace=75
                )
            
            # Apply posterization to further reduce colors
            return self._quantize_posterize(result)
            
        except Exception as e:
            logger.error(f"Error in bilateral quantization: {str(e)}")
            return frame
    
    def _quantize_posterize(self, frame):
        """Apply posterization (reduce number of intensity levels)"""
        try:
            # Calculate number of levels per channel based on num_colors
            levels = max(2, int(np.cbrt(self.num_colors)))
            
            # Create LUT (Look-Up Table) for posterization
            lut = np.zeros(256, dtype=np.uint8)
            for i in range(256):
                lut[i] = np.clip(int(levels * i / 256) * (256 // levels), 0, 255)
            
            # Apply LUT to each channel
            result = frame.copy()
            for c in range(3):  # BGR
                result[:, :, c] = cv2.LUT(frame[:, :, c], lut)
            
            # Apply saturation adjustment
            if self.saturation != 1.0:
                # Convert to HSV for saturation adjustment
                hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
                hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.saturation, 0, 255)
                result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
            
            # Apply temporal smoothing if enabled
            if self.prev_colors is not None and self.temporal_smoothing > 0:
                result = cv2.addWeighted(
                    result, 
                    1 - self.temporal_smoothing, 
                    self.prev_colors, 
                    self.temporal_smoothing, 
                    0
                )
            
            # Update previous colors
            self.prev_colors = result.copy()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in posterize quantization: {str(e)}")
            return frame
    
    def _merge_edges_with_colors(self, frame, edges_binary):
        """
        Merge edge map with the color quantized frame
        
        Args:
            frame: Color quantized frame
            edges_binary: Binary edge map
            
        Returns:
            Frame with edges overlaid
        """
        try:
            # Create a mask for the edges
            edges_mask = edges_binary > 0
            
            # Create the result image
            result = frame.copy()
            
            # Overlay edges
            if self.preserve_black:
                result[edges_mask] = [0, 0, 0]  # Black edges
            
            return result
            
        except Exception as e:
            logger.error(f"Error merging edges with colors: {str(e)}")
            return frame
    
    def process_frame(self, frame):
        """
        Process a single frame with the Scanner Darkly effect
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Processed frame with Scanner Darkly effect
        """
        try:
            # Load the neural network if not already loaded
            net = self._load_neural_network()
            if net is None:
                logger.error("Failed to load neural network, returning original frame")
                return frame
            
            # Step 1: Detect edges using neural network
            edges = self._detect_edges(frame, net)
            
            # Step 2: Enhance and thicken edges
            edges_binary = self._enhance_edges(edges)
            
            # Step 3: Apply color quantization
            quantized_frame = self._quantize_colors(frame)
            
            # Step 4: Merge edges with quantized colors
            result = self._merge_edges_with_colors(quantized_frame, edges_binary)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing frame: {str(e)}")
            return frame
    
    def process_batch(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """
        Process a batch of frames
        
        Args:
            frames: List of input BGR frames
            
        Returns:
            List of processed frames
        """
        results = []
        
        # Load the neural network once for all frames
        net = self._load_neural_network()
        if net is None:
            logger.error("Failed to load neural network, returning original frames")
            return frames
        
        # Process each frame
        for frame in frames:
            try:
                # Step 1: Detect edges using neural network
                edges = self._detect_edges(frame, net)
                
                # Step 2: Enhance and thicken edges
                edges_binary = self._enhance_edges(edges)
                
                # Step 3: Apply color quantization
                quantized_frame = self._quantize_colors(frame)
                
                # Step 4: Merge edges with quantized colors
                result = self._merge_edges_with_colors(quantized_frame, edges_binary)
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing frame in batch: {str(e)}")
                results.append(frame)  # Add original frame if processing fails
        
        return results

def get_command(input_path, output_path, params=None):
    """
    Generate a shell command for applying the Scanner Darkly effect
    
    This version tries to use the neural implementation first
    """
    import os
    import tempfile
    
    # Check if model files exist in common locations
    model_locations = [
        ("/opt/video-processor/model_weights/hed.caffemodel", 
         "/opt/video-processor/model_weights/hed.prototxt"),
        ("/opt/video-processor/hed.caffemodel", 
         "/opt/video-processor/hed.prototxt")
    ]
    
    model_found = False
    for model_path, prototxt_path in model_locations:
        if os.path.exists(model_path) and os.path.exists(prototxt_path):
            logger.info(f"Found HED model files at {model_path}")
            model_found = True
            break
    
    if model_found:
        # Create a temporary script file to run the neural implementation
        temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
        
        # Write the necessary imports and processing code
        temp_script.write("""
#!/usr/bin/env python3
import cv2
import numpy as np
import os
import sys

def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    model_path = sys.argv[3]
    prototxt_path = sys.argv[4]
    
    print(f"Loading model from {model_path}")
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    
    # Open the video
    cap = cv2.VideoCapture(input_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    # Create output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Process frames
    prev_edges = None
    prev_colors = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Edge detection
        blob = cv2.dnn.blobFromImage(frame, 1.0, (width, height), (104.00698793, 116.66876762, 122.67891434), swapRB=False)
        net.setInput(blob)
        edges = net.forward()[0, 0]
        
        # Temporal smoothing
        if prev_edges is not None:
            edges = edges * 0.7 + prev_edges * 0.3
        prev_edges = edges.copy()
        
        # Threshold edges
        edges = (edges > 0.2).astype(np.uint8) * 255
        
        # Enhance edges
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Color quantization
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        pixels = lab[:,:,0].reshape((-1, 1)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(pixels, 5, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        lab[:,:,0] = centers[labels.flatten()].reshape(lab[:,:,0].shape)
        quantized = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Temporal color smoothing
        if prev_colors is not None:
            quantized = cv2.addWeighted(quantized, 0.7, prev_colors, 0.3, 0)
        prev_colors = quantized.copy()
        
        # Apply edges
        edges_mask = (edges > 0)
        result = quantized.copy()
        result[edges_mask] = [0, 0, 0]
        
        # Write frame
        out.write(result)
    
    # Clean up
    cap.release()
    out.release()
    
    # Convert to h264
    os.system(f'ffmpeg -y -i "{output_path}" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 "{output_path}.tmp.mp4"')
    os.replace(f"{output_path}.tmp.mp4", output_path)
    
    return 0

if __name__ == "__main__":
    main()
""")
        temp_script.close()
        os.chmod(temp_script.name, 0o755)
        
        # Return command to run the script
        return f"python3 {temp_script.name} '{input_path}' '{output_path}' '{model_path}' '{prototxt_path}'"
    
    # Fallback to FFmpeg
    logger.info(f"Using SCANNER DARKLY fallback FFmpeg command (v{VERSION})")
    
    return (
        f'ffmpeg -y -i "{input_path}" '
        f'-vf "'
        # Edge detection using FFmpeg filters
        f'split=2[a][b];'
        f'[a]edgedetect=mode=colormix:high=0.15:low=0.1[edges];'
        
        # Color quantization
        f'[b]eq=saturation=1.3,'  # Increase saturation
        f'boxblur=10:5,'  # Simplify colors
        f'eq=gamma=1.5[colors];'  # Boost colors
        
        # Combine edges with colors
        f'[colors][edges]blend=all_mode=multiply'
        f'" '
        
        # Output settings
        f'-c:v libx264 '
        f'-pix_fmt yuv420p '
        f'-preset medium '
        f'-crf 18 '
        f'-metadata title="Scanner Darkly Effect" '
        f'"{output_path}"'
    )