#!/usr/bin/env python3
"""
Scanner Darkly effect using HED (Holistically-Nested Edge Detection)
Creates a rotoscoping effect similar to the one used in the movie "A Scanner Darkly"
"""

import os
import sys
try:
    import cv2
    import numpy as np
except ImportError:
    print("ERROR: Missing required packages. Please install with:")
    print("pip install opencv-python-headless numpy")
    sys.exit(1)

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
        edge_strength: float = 0.9,
        edge_thickness: float = 1.8,
        num_colors: int = 6,
        color_method: str = "kmeans",
        smoothing: float = 0.7,
        saturation: float = 1.3,
        temporal_smoothing: float = 0.4,
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
            # Absolute paths
            "/opt/video-processor/model_weights",
            "/opt/video-processor",
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
            # Try to import boto3 only when needed
            try:
                import boto3
                from botocore.exceptions import ClientError
            except ImportError:
                logger.error("boto3 not available, cannot download model files")
                return
            
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
            
            # Make a copy of the frame for pre-processing
            processed_frame = frame.copy()
            
            # Apply a slight bilateral filter to reduce noise while preserving edges
            processed_frame = cv2.bilateralFilter(processed_frame, 5, 30, 30)
            
            # Prepare the input blob for the network
            blob = cv2.dnn.blobFromImage(
                processed_frame, 
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
            
            # Apply a power function to enhance edge contrast
            edges = np.power(edges, 1.0 - self.edge_strength * 0.7)
            
            return edges
            
        except Exception as e:
            logger.error(f"Error detecting edges: {str(e)}")
            return np.zeros((height, width), dtype=np.float32)
    
    def _enhance_edges(self, edges):
        """
        Enhance and thicken edges for the Scanner Darkly look
        
        Args:
            edges: Edge map (0-1)
            
        Returns:
            Enhanced binary edge map
        """
        try:
            # Scale to 8-bit for processing
            edges_8bit = (edges * 255).astype(np.uint8)
            
            # Apply adaptive thresholding for more detailed edge extraction
            # This helps get more consistent edges across different lighting conditions
            try:
                binary_edges = cv2.adaptiveThreshold(
                    edges_8bit,
                    255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY,
                    11,  # Block size
                    -2   # Constant subtracted from mean
                )
            except:
                # Fall back to simple thresholding if adaptive fails
                _, binary_edges = cv2.threshold(
                    edges_8bit, 
                    int(40 * (1 - self.edge_strength)),  # Adaptive threshold
                    255, 
                    cv2.THRESH_BINARY
                )
            
            # Apply dilation to thicken edges - using edge_thickness as parameter
            if self.edge_thickness > 1.0:
                kernel_size = max(1, int(self.edge_thickness * 1.8))
                kernel = np.ones((kernel_size, kernel_size), np.uint8)
                binary_edges = cv2.dilate(binary_edges, kernel, iterations=1)
                
                # Apply slight Gaussian blur to soften edge artifacts
                binary_edges = cv2.GaussianBlur(binary_edges, (3, 3), 0.5)
            
            # Apply thinning if needed for a more precise hand-drawn look
            if self.edge_thickness < 1.0:
                try:
                    binary_edges = cv2.ximgproc.thinning(binary_edges)
                except:
                    # Fall back if ximgproc not available
                    kernel = np.ones((3, 3), np.uint8)
                    binary_edges = cv2.erode(binary_edges, kernel, iterations=1)
            
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
            # Apply bilateral blur for edge-preserving smoothing
            if self.smoothing > 0:
                sigma_color = 20 * self.smoothing
                sigma_space = 10 * self.smoothing
                d = int(5 * self.smoothing) * 2 + 1
                frame = cv2.bilateralFilter(frame, d, sigma_color, sigma_space)
            
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
        """Apply k-means clustering for color quantization with Scanner Darkly aesthetics"""
        try:
            # Convert to LAB color space for better perceptual color clustering
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
                    np.int16(quantized_lab[:, :, 1]) * self.saturation, 
                    -128, 
                    127
                ).astype(np.uint8)
                
                quantized_lab[:, :, 2] = np.clip(
                    np.int16(quantized_lab[:, :, 2]) * self.saturation, 
                    -128, 
                    127
                ).astype(np.uint8)
            
            # Enhanced Scanner Darkly color treatment:
            # Increase contrast in the lightness channel for more dramatic colors
            quantized_lab[:, :, 0] = np.clip(
                (quantized_lab[:, :, 0] - 50) * 1.2 + 50,  # Contrast boost
                0, 
                255
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
        """Apply bilateral filtering for color simplification with artistic adjustment"""
        try:
            # Apply strong bilateral filtering multiple times for flat color regions
            result = frame.copy()
            iterations = max(1, int(4 * self.smoothing))
            
            for _ in range(iterations):
                result = cv2.bilateralFilter(
                    result, 
                    d=9, 
                    sigmaColor=100,
                    sigmaSpace=100
                )
            
            # Convert to HSV for better color manipulation
            hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
            
            # Increase saturation for more vivid colors
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.saturation, 0, 255).astype(np.uint8)
            
            # Adjust value channel for more contrast
            hsv[:, :, 2] = np.clip((hsv[:, :, 2] - 30) * 1.2 + 30, 0, 255).astype(np.uint8)
            
            # Convert back to BGR
            result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            
            # Apply posterization to further reduce colors
            result = self._quantize_posterize(result)
            
            # Apply temporal smoothing
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
            logger.error(f"Error in bilateral quantization: {str(e)}")
            return frame
    
    def _quantize_posterize(self, frame):
        """Apply posterization for flat color regions like in the Scanner Darkly movie"""
        try:
            # Calculate number of levels per channel based on num_colors
            levels = max(2, int(np.cbrt(self.num_colors)))
            
            # Create LUT (Look-Up Table) for posterization with Scanner Darkly aesthetics
            lut = np.zeros(256, dtype=np.uint8)
            for i in range(256):
                # Add slight non-linearity for more artistic feel
                adjusted_level = int(np.power(i / 255.0, 0.9) * levels) * (255 // levels)
                lut[i] = np.clip(adjusted_level, 0, 255)
            
            # Apply LUT to each channel
            result = frame.copy()
            for c in range(3):  # BGR
                result[:, :, c] = cv2.LUT(frame[:, :, c], lut)
            
            # Apply saturation adjustment
            if self.saturation != 1.0:
                # Convert to HSV for saturation adjustment
                hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
                hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.saturation, 0, 255)
                
                # Also slightly adjust the value channel for Scanner Darkly contrast
                hsv[:, :, 2] = np.clip(
                    (hsv[:, :, 2] - 50) * 1.1 + 50,  # Contrast boost
                    0, 
                    255
                )
                
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
        Merge edge map with the color quantized frame for the Scanner Darkly rotoscoped look
        
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
            
            # Overlay edges - in Scanner Darkly they were pure black
            if self.preserve_black:
                # Pure black for strong edges
                result[edges_mask] = [0, 0, 0]  # Black edges
            
            # Optional: Create a slight border effect around the edges
            # This creates a subtle transition between color regions
            kernel = np.ones((3, 3), np.uint8)
            edges_dilated = cv2.dilate(edges_binary, kernel, iterations=1)
            edges_border = edges_dilated & ~edges_mask
            
            # Darken the border slightly for a more artistic look
            result[edges_border] = (result[edges_border] * 0.7).astype(np.uint8)
            
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
        Process a batch of frames with the Scanner Darkly effect
        
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
        for i, frame in enumerate(frames):
            try:
                logger.info(f"Processing frame {i+1}/{len(frames)}")
                
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
                logger.error(f"Error processing frame {i+1} in batch: {str(e)}")
                results.append(frame)  # Add original frame if processing fails
        
        return results
    
    def reset(self):
        """
        Reset the effect's state (for processing a new video)
        This clears any cached frames used for temporal smoothing
        """
        self.prev_edges = None
        self.prev_colors = None
        logger.info("Scanner Darkly effect state reset")

def get_command(input_path, output_path, params=None):
    """
    Generate a command for applying the Scanner Darkly effect using the neural implementation
    
    This creates a temporary Python script that processes the video with the
    HED neural network-based edge detection and color quantization techniques
    to create a look similar to the film "A Scanner Darkly".
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        params: Optional parameters for customization
        
    Returns:
        Command string to execute the script
    """
    import os
    import tempfile
    
    # Check if model files exist in common locations
    model_locations = [
        ("/opt/video-processor/model_weights/hed.caffemodel", 
         "/opt/video-processor/model_weights/hed.prototxt"),
        ("/opt/video-processor/hed.caffemodel", 
         "/opt/video-processor/hed.prototxt"),
        (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "model_weights", "hed.caffemodel"),
         os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "model_weights", "hed.prototxt"))
    ]
    
    model_found = False
    model_path = ""
    prototxt_path = ""
    
    for model_p, prototxt_p in model_locations:
        if os.path.exists(model_p) and os.path.exists(prototxt_p):
            logger.info(f"Found HED model files at {model_p}")
            model_found = True
            model_path = model_p
            prototxt_path = prototxt_p
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
import time

def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    model_path = sys.argv[3]
    prototxt_path = sys.argv[4]
    
    print(f"Processing with Scanner Darkly effect v1.0.0")
    print(f"Loading model from {model_path}")
    
    # Start timer
    start_time = time.time()
    
    # Load HED model
    try:
        net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
        print("Model loaded successfully")
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return 1
    
    # Open the video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {input_path}")
        return 1
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames")
    
    # Create output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Parameters for Scanner Darkly look
    edge_strength = 0.9
    edge_thickness = 1.8
    num_colors = 6
    smoothing = 0.7
    saturation = 1.3
    temporal_smoothing = 0.4
    
    # Process frames
    prev_edges = None
    prev_colors = None
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Print progress every 10 frames
        frame_count += 1
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            fps_processing = frame_count / elapsed if elapsed > 0 else 0
            percent_complete = (frame_count / total_frames * 100) if total_frames > 0 else 0
            print(f"Processing frame {frame_count}/{total_frames} ({percent_complete:.1f}%) - {fps_processing:.2f} fps")
        
        # Pre-process: Bilateral filter to reduce noise while preserving edges
        preprocessed = cv2.bilateralFilter(frame, 5, 30, 30)
        
        # ---------- Edge Detection ----------
        # HED neural network edge detection
        blob = cv2.dnn.blobFromImage(
            preprocessed, 
            scalefactor=1.0, 
            size=(width, height),
            mean=(104.00698793, 116.66876762, 122.67891434),
            swapRB=False, 
            crop=False
        )
        
        net.setInput(blob)
        edges = net.forward()[0, 0]
        
        # Temporal smoothing for edges
        if prev_edges is not None:
            edges = edges * (1 - temporal_smoothing) + prev_edges * temporal_smoothing
        prev_edges = edges.copy()
        
        # Normalize and enhance edges
        edges = cv2.normalize(edges, None, 0, 1, cv2.NORM_MINMAX)
        edges = np.power(edges, 1.0 - edge_strength * 0.7)
        
        # Create binary edge map with adaptive thresholding
        edges_8bit = (edges * 255).astype(np.uint8)
        try:
            # Try adaptive thresholding first
            binary_edges = cv2.adaptiveThreshold(
                edges_8bit,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                -2
            )
        except:
            # Fall back to simple thresholding
            _, binary_edges = cv2.threshold(edges_8bit, int(40 * (1 - edge_strength)), 255, cv2.THRESH_BINARY)
        
        # Dilate edges for thickness
        kernel_size = max(1, int(edge_thickness * 1.8))
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        binary_edges = cv2.dilate(binary_edges, kernel, iterations=1)
        
        # Slight Gaussian blur to soften edge artifacts
        binary_edges = cv2.GaussianBlur(binary_edges, (3, 3), 0.5)
        
        # ---------- Color Quantization ----------
        # Convert to LAB color space for better perceptual clustering
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Apply bilateral filter for smoothing while preserving edges
        sigma_color = 20 * smoothing
        sigma_space = 10 * smoothing
        d = int(5 * smoothing) * 2 + 1
        lab_smoothed = cv2.bilateralFilter(lab, d, sigma_color, sigma_space)
        
        # Reshape for k-means clustering
        pixels = lab_smoothed.reshape(-1, 3).astype(np.float32)
        
        # Apply k-means for color reduction
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            pixels, 
            num_colors, 
            None, 
            criteria, 
            10, 
            cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Map pixels to their closest center
        centers = centers.astype(np.uint8)
        quantized_lab = centers[labels.flatten()].reshape(frame.shape)
        
        # Enhance color contrast in LAB space
        quantized_lab[:, :, 0] = np.clip((quantized_lab[:, :, 0] - 50) * 1.2 + 50, 0, 255).astype(np.uint8)
        
        # Increase color saturation (a and b channels)
        quantized_lab[:, :, 1] = np.clip(np.int16(quantized_lab[:, :, 1]) * saturation, -128, 127).astype(np.uint8)
        quantized_lab[:, :, 2] = np.clip(np.int16(quantized_lab[:, :, 2]) * saturation, -128, 127).astype(np.uint8)
        
        # Convert back to BGR
        quantized = cv2.cvtColor(quantized_lab, cv2.COLOR_LAB2BGR)
        
        # Temporal smoothing for colors
        if prev_colors is not None:
            quantized = cv2.addWeighted(
                quantized, 
                1 - temporal_smoothing, 
                prev_colors, 
                temporal_smoothing, 
                0
            )
        prev_colors = quantized.copy()
        
        # ---------- Edge Overlay ----------
        # Create the final result by overlaying edges on quantized colors
        result = quantized.copy()
        
        # Create edge mask
        edges_mask = binary_edges > 0
        
        # Apply black edges (like in Scanner Darkly)
        result[edges_mask] = [0, 0, 0]
        
        # Create a subtle border effect around edges
        border_kernel = np.ones((3, 3), np.uint8)
        edges_dilated = cv2.dilate(binary_edges, border_kernel, iterations=1)
        edges_border = cv2.bitwise_and(edges_dilated, cv2.bitwise_not(binary_edges))
        border_mask = edges_border > 0
        
        # Darken the border slightly for a more artistic look
        result[border_mask] = (result[border_mask] * 0.7).astype(np.uint8)
        
        # Write frame to output
        out.write(result)
    
    # Clean up
    cap.release()
    out.release()
    
    # Convert to h264 for better compatibility
    print("Converting to h264 format...")
    try:
        os.system(f'ffmpeg -y -i "{output_path}" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 "{output_path}.tmp.mp4"')
        os.replace(f"{output_path}.tmp.mp4", output_path)
        print("Conversion complete")
    except Exception as e:
        print(f"Warning: H264 conversion failed: {str(e)}")
    
    # Report time
    elapsed_time = time.time() - start_time
    print(f"Processing complete! {frame_count} frames processed in {elapsed_time:.2f} seconds ({frame_count/elapsed_time:.2f} fps)")
    print(f"Output saved to: {output_path}")
    
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python script.py input_path output_path model_path prototxt_path")
        sys.exit(1)
    sys.exit(main())
""")  # Close the write() function
    temp_script.close()
    os.chmod(temp_script.name, 0o755)
    
    # Return command to run the script
    return f"python3 {temp_script.name} '{input_path}' '{output_path}' '{model_path}' '{prototxt_path}'"
