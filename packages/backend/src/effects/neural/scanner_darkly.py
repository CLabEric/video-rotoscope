#!/usr/bin/env python3
"""
Scanner Darkly effect with optical flow for improved temporal consistency
"""

import os
import cv2
import numpy as np
import logging
from typing import List, Tuple, Optional

# Set up logging
logger = logging.getLogger(__name__)

VERSION = "6.0.0-FLOW"

class ScannerDarklyEffect:
    """
    Scanner Darkly rotoscoping effect with optical flow for consistent edges
    between frames, producing results similar to the film's artistic style
    """
    
    def __init__(
        self,
        model_path: str = None,         # For compatibility, not used
        prototxt_path: str = None,      # For compatibility, not used
        edge_strength: float = 0.8,     # Edge strength
        edge_thickness: float = 0.4,    # Line thickness
        edge_threshold: float = 0.75,   # Threshold for edge detection
        num_colors: int = 5,            # Number of colors in quantization
        color_method: str = "kmeans",   # For compatibility
        smoothing: float = 0.9,         # Smoothing strength
        saturation: float = 1.2,        # Saturation adjustment
        temporal_smoothing: float = 0.4, # Increased for better consistency
        preserve_black: bool = True,    # Whether to use black for edges
        flow_weight: float = 0.7        # Weight for optical flow edges
    ):
        """Initialize with parameters tuned for movie-like results"""
        self.edge_strength = edge_strength
        self.edge_thickness = edge_thickness
        self.edge_threshold = edge_threshold
        self.num_colors = num_colors
        self.smoothing = smoothing
        self.saturation = saturation
        self.temporal_smoothing = temporal_smoothing
        self.preserve_black = preserve_black
        self.flow_weight = flow_weight
        
        # For tracking between frames
        self.prev_frame = None        # Previous frame for optical flow
        self.prev_gray = None         # Grayscale version for flow calculation
        self.prev_edges = None        # Previous detected edges
        self.prev_colors = None       # Previous color quantization
        self.prev_result = None       # Previous result for consistency
        
        # For face detection
        self.face_cascade = None
        try:
            haar_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
            if os.path.exists(haar_path):
                self.face_cascade = cv2.CascadeClassifier(haar_path)
                logger.info("Face detection enabled for better feature preservation")
        except:
            logger.warning("Face detection not available - will rely on edge detection only")
        
        # Parameters for optical flow
        self.flow_params = dict(
            pyr_scale=0.5,    # Image pyramid scale
            levels=3,         # Number of pyramid levels
            winsize=15,       # Averaging window size
            iterations=3,     # Number of iterations at each pyramid level
            poly_n=5,         # Size of pixel neighborhood for polynomial expansion
            poly_sigma=1.2,   # Std dev of Gaussian for polynomial expansion
            flags=0           # Flags
        )
        
        logger.info(f"*** INITIALIZED SCANNER DARKLY EFFECT WITH OPTICAL FLOW v{VERSION} ***")
    
    def _apply_optical_flow(self, current_frame, current_edges):
        """
        Apply optical flow to warp previous edges to current frame
        
        Args:
            current_frame: Current frame
            current_edges: Currently detected edges
            
        Returns:
            Flow-warped edges from previous frame
        """
        if self.prev_frame is None or self.prev_edges is None:
            return current_edges
            
        try:
            # Convert current frame to grayscale for flow calculation
            current_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate optical flow between previous and current frame
            flow = cv2.calcOpticalFlowFarneback(
                self.prev_gray, 
                current_gray, 
                None, 
                **self.flow_params
            )
            
            # Create a grid of coordinates
            h, w = current_frame.shape[:2]
            y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)
            
            # Calculate new coordinates based on flow
            # Invert flow direction to warp from prev to current
            warp_x = (x_coords - flow[..., 0]).clip(0, w - 1)
            warp_y = (y_coords - flow[..., 1]).clip(0, h - 1)
            
            # Prepare coordinate maps
            coords = np.stack([warp_x, warp_y], axis=-1)
            
            # Remap previous edges using flow
            warped_edges = cv2.remap(
                self.prev_edges, 
                coords, 
                None, 
                cv2.INTER_LINEAR
            )
            
            # Blend current and flow-warped edges
            # Adjust weight to favor warped edges from previous frames
            flow_weight = self.flow_weight
            blended_edges = cv2.addWeighted(
                current_edges.astype(np.float32), 
                1.0 - flow_weight,
                warped_edges.astype(np.float32),
                flow_weight,
                0
            )
            
            # Convert back to binary edges
            result_edges = (blended_edges > 127).astype(np.uint8) * 255
            
            # Update previous frame and edges for next iteration
            self.prev_gray = current_gray.copy()
            
            return result_edges
            
        except Exception as e:
            logger.error(f"Error applying optical flow: {str(e)}")
            return current_edges
    
    def _detect_artistic_lines(self, frame):
        """
        Refined line detection with attention to important features
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Binary line map with artistic quality
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply bilateral filter for noise reduction
            bilateral = cv2.bilateralFilter(gray, 9, 25, 25)
            bilateral_strong = cv2.bilateralFilter(bilateral, 15, 40, 40)
            
            # Apply Canny with selective thresholds
            high_threshold = int(200 * self.edge_threshold)
            low_threshold = int(high_threshold * 0.4)
            edges_canny = cv2.Canny(bilateral, low_threshold, high_threshold)
            
            # Apply Laplacian for additional detail
            laplacian = cv2.Laplacian(bilateral_strong, cv2.CV_8U, ksize=3)
            _, edges_laplacian = cv2.threshold(laplacian, 25, 255, cv2.THRESH_BINARY)
            
            # Combine edges
            edges_combined = cv2.bitwise_or(edges_canny, edges_laplacian)
            
            # Apply face detection for better feature preservation
            face_regions = np.zeros_like(gray)
            if self.face_cascade is not None:
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    # Extended region to include neck and hair
                    extended_y = max(0, y - int(h * 0.2))
                    extended_h = min(gray.shape[0] - extended_y, int(h * 1.4))
                    
                    # Apply specific edge detection for facial features
                    face_gray = gray[extended_y:extended_y + extended_h, x:x + w]
                    if face_gray.size > 0:
                        face_edges = cv2.Canny(face_gray, low_threshold * 0.7, high_threshold * 0.7)
                        face_regions[extended_y:extended_y + extended_h, x:x + w] = face_edges
            
            # Combine face edges with general edges
            edges_combined = cv2.bitwise_or(edges_combined, face_regions)
            
            # Clean up noise and small segments
            num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(edges_combined, connectivity=8)
            
            min_size = 40
            max_size = int(frame.shape[0] * frame.shape[1] * 0.3)
            filtered_edges = np.zeros_like(edges_combined)
            
            for i in range(1, num_labels):
                component_size = stats[i, cv2.CC_STAT_AREA]
                if min_size <= component_size <= max_size:
                    filtered_edges[labels == i] = 255
            
            # Remove horizontal/vertical artifacts
            h_kernel = np.ones((1, 7), np.uint8)
            v_kernel = np.ones((7, 1), np.uint8)
            
            h_runs = cv2.morphologyEx(filtered_edges, cv2.MORPH_OPEN, h_kernel)
            v_runs = cv2.morphologyEx(filtered_edges, cv2.MORPH_OPEN, v_kernel)
            
            h_v_runs = cv2.bitwise_or(h_runs, v_runs)
            dilated_important = cv2.dilate(filtered_edges, np.ones((3,3), np.uint8))
            unwanted_lines = cv2.bitwise_and(h_v_runs, cv2.bitwise_not(dilated_important))
            filtered_edges = cv2.bitwise_and(filtered_edges, cv2.bitwise_not(unwanted_lines))
            
            # Apply thinning and controlled dilation for consistent lines
            try:
                edges_thinned = cv2.ximgproc.thinning(filtered_edges)
                thin_kernel = np.ones((2, 2), np.uint8)
                edges_stylized = cv2.dilate(edges_thinned, thin_kernel, iterations=1)
            except:
                kernel = np.ones((int(2 * self.edge_thickness), int(2 * self.edge_thickness)), np.uint8)
                edges_stylized = cv2.dilate(filtered_edges, kernel, iterations=1)
            
            # Apply optical flow for temporal consistency if we have previous data
            if self.prev_frame is not None and self.prev_edges is not None:
                edges_stylized = self._apply_optical_flow(frame, edges_stylized)
            
            # Additional temporal smoothing (along with optical flow)
            if self.prev_edges is not None and self.temporal_smoothing > 0:
                weight = self.temporal_smoothing
                edges_float = edges_stylized.astype(np.float32)
                prev_float = self.prev_edges.astype(np.float32)
                blended = cv2.addWeighted(edges_float, 1-weight, prev_float, weight, 0)
                edges_result = (blended > 127).astype(np.uint8) * 255
            else:
                edges_result = edges_stylized
            
            # Store the current frame and edges for next iteration
            self.prev_frame = frame.copy()
            self.prev_gray = gray.copy()
            self.prev_edges = edges_result.copy()
            
            return edges_result
            
        except Exception as e:
            logger.error(f"Error detecting artistic lines: {str(e)}")
            return np.zeros_like(frame[:,:,0])
    
    def _quantize_colors(self, frame):
        """
        Apply color quantization with parameters for flat color regions
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Color quantized frame
        """
        try:
            # Convert to LAB color space for better perceptual results
            lab_image = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
            
            # Apply bilateral filter for flat regions
            if self.smoothing > 0:
                d = int(12 * self.smoothing)
                sigma_color = 50 * self.smoothing
                sigma_space = 50 * self.smoothing
                lab_filtered = np.zeros_like(lab_image)
                
                for i in range(3):
                    if i == 0:  # L channel
                        sig_c = sigma_color
                    else:  # A and B channels
                        sig_c = sigma_color * 2.2
                        
                    lab_filtered[:,:,i] = cv2.bilateralFilter(lab_image[:,:,i], d, sig_c, sigma_space)
                
                lab_smoothed = lab_filtered
            else:
                lab_smoothed = lab_image
            
            # Boost saturation
            if self.saturation != 1.0:
                lab_saturated = lab_smoothed.copy().astype(np.float32)
                mean_a = np.mean(lab_saturated[:,:,1])
                mean_b = np.mean(lab_saturated[:,:,2])
                
                lab_saturated[:,:,1] = (lab_saturated[:,:,1] - mean_a) * self.saturation + mean_a
                lab_saturated[:,:,2] = (lab_saturated[:,:,2] - mean_b) * self.saturation + mean_b
                
                lab_saturated[:,:,1] = np.clip(lab_saturated[:,:,1], 0, 255)
                lab_saturated[:,:,2] = np.clip(lab_saturated[:,:,2], 0, 255)
                
                lab_prepared = lab_saturated.astype(np.uint8)
            else:
                lab_prepared = lab_smoothed
            
            # Apply k-means clustering for color quantization
            h, w = frame.shape[:2]
            pixels = lab_prepared.reshape(-1, 3).astype(np.float32)
            
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 0.2)
            k = self.num_colors
            
            # Generate initial centers for better quantization
            attempts = 30
            _, labels, centers = cv2.kmeans(
                pixels, 
                k, 
                None, 
                criteria, 
                attempts,
                cv2.KMEANS_PP_CENTERS  
            )
            
            # Map pixels to centers
            centers = centers.astype(np.uint8)
            quantized_lab = centers[labels.flatten()].reshape(lab_prepared.shape)
            
            # Convert back to BGR
            quantized = cv2.cvtColor(quantized_lab, cv2.COLOR_LAB2BGR)
            
            # Apply bilateral filter for smoother regions
            quantized = cv2.bilateralFilter(quantized, 7, 35, 35)
            
            # Apply optical flow warping to colors for consistency
            if self.prev_frame is not None and self.prev_colors is not None and self.prev_gray is not None:
                # Calculate optical flow
                current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                flow = cv2.calcOpticalFlowFarneback(
                    self.prev_gray,
                    current_gray,
                    None,
                    **self.flow_params
                )
                
                # Create a grid of coordinates
                h, w = frame.shape[:2]
                y_coords, x_coords = np.mgrid[0:h, 0:w].astype(np.float32)
                
                # Calculate warped coordinates
                warp_x = (x_coords - flow[..., 0]).clip(0, w - 1)
                warp_y = (y_coords - flow[..., 1]).clip(0, h - 1)
                
                # Prepare coordinate maps
                coords = np.stack([warp_x, warp_y], axis=-1)
                
                # Remap previous colors using flow
                warped_colors = cv2.remap(
                    self.prev_colors,
                    coords,
                    None,
                    cv2.INTER_LINEAR
                )
                
                # Blend with lower weight than edges
                flow_weight = self.flow_weight * 0.8  # Lower weight for colors
                quantized = cv2.addWeighted(
                    quantized,
                    1.0 - flow_weight,
                    warped_colors,
                    flow_weight,
                    0
                )
            
            # Apply additional temporal smoothing
            if self.prev_colors is not None and self.temporal_smoothing > 0:
                weight = self.temporal_smoothing
                quantized = cv2.addWeighted(
                    quantized,
                    1-weight,
                    self.prev_colors,
                    weight,
                    0
                )
            
            # Store for next frame
            self.prev_colors = quantized.copy()
            
            return quantized
            
        except Exception as e:
            logger.error(f"Error quantizing colors: {str(e)}")
            return frame
    
    def process_frame(self, frame):
        """
        Process a single frame with the Scanner Darkly effect
        
        Args:
            frame: Input BGR frame
            
        Returns:
            Processed frame
        """
        try:
            # 1. Apply color quantization
            quantized = self._quantize_colors(frame)
            
            # 2. Detect artistic lines with optical flow consistency
            lines = self._detect_artistic_lines(frame)
            
            # 3. Combine lines with quantized colors
            result = quantized.copy()
            
            # Apply lines using appropriate color
            lines_mask = lines > 0
            
            if self.preserve_black:
                edge_color = [0, 0, 0]  # Black
            else:
                edge_color = [30, 30, 30]  # Darker gray
                
            result[lines_mask] = edge_color
            
            # 4. Subtle darkening effect around edges
            edge_expansion = cv2.dilate(lines_mask.astype(np.uint8), np.ones((2,2), np.uint8)) - lines_mask.astype(np.uint8)
            edge_expansion_mask = edge_expansion > 0
            
            result[edge_expansion_mask] = np.clip(result[edge_expansion_mask] * 0.9, 0, 255).astype(np.uint8)
            
            # 5. Overall result consistency through optical flow
            if self.prev_result is not None:
                # Apply a final temporal blend with previous result
                # This ensures overall consistency
                final_weight = min(0.3, self.temporal_smoothing)  # Cap at 0.3 to avoid oversmoothing
                result = cv2.addWeighted(
                    result,
                    1 - final_weight,
                    self.prev_result,
                    final_weight,
                    0
                )
            
            # Store result for next frame
            self.prev_result = result.copy()
            
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
        logger.info(f"*** PROCESSING BATCH OF {len(frames)} FRAMES WITH SCANNER DARKLY v{VERSION} ***")
        
        # Reset state at the beginning of each batch
        self.prev_frame = None
        self.prev_gray = None
        self.prev_edges = None
        self.prev_colors = None
        self.prev_result = None
        
        results = []
        for i, frame in enumerate(frames):
            logger.info(f"Processing frame {i+1}/{len(frames)}")
            result = self.process_frame(frame)
            results.append(result)
        
        logger.info(f"*** COMPLETED BATCH PROCESSING WITH SCANNER DARKLY v{VERSION} ***")
        return results

# Command generation function that uses the ScannerDarklyEffect class
def get_command(input_path, output_path, params=None):
    """
    Generate a shell command for applying the Scanner Darkly effect
    Uses a minimal launcher script that imports the ScannerDarklyEffect class
    """
    logger.info(f"*** SCANNER DARKLY v{VERSION} - GENERATING COMMAND ***")
    
    import tempfile
    import os
    
    # Create a minimal launcher script that imports the class
    temp_script = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False)
    
    # Get the full path to this file for importing
    current_file_path = os.path.abspath(__file__)
    
    # Write a simple launcher script that imports and uses our class
    script_content = f"""#!/usr/bin/env python3
import sys
import os
import cv2
import numpy as np
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Add the directory containing scanner_darkly.py to the Python path
sys.path.append(os.path.dirname("{current_file_path}"))

# Import the ScannerDarklyEffect class
from scanner_darkly import ScannerDarklyEffect

def main():
    # Get input and output paths from command-line arguments
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    logger.info(f"Processing video: {{input_path}} -> {{output_path}}")
    
    try:
        # Create an instance of ScannerDarklyEffect with optimized parameters
        effect = ScannerDarklyEffect(
            edge_strength=0.9,
            edge_thickness=0.7,
            edge_threshold=0.65,
            num_colors=5,
            smoothing=0.9,
            saturation=1.15,
            temporal_smoothing=0.2,
            preserve_black=True
        )
        
        # Open the input video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            logger.error(f"Could not open video: {{input_path}}")
            return 1
            
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Video specs: {{width}}x{{height}} at {{fps}} fps, {{total_frames}} frames")
        
        # Create output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        if not out.isOpened():
            logger.error(f"Could not create output video: {{output_path}}")
            return 1
        
        # Process video in batches
        batch_size = 30
        frames = []
        processed_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frames.append(frame)
            
            # Process when batch is full or end of video
            if len(frames) >= batch_size or processed_count + len(frames) >= total_frames:
                # Process the batch using our class
                logger.info(f"Processing batch of {{len(frames)}} frames")
                processed_frames = effect.process_batch(frames)
                
                # Write processed frames
                for processed_frame in processed_frames:
                    out.write(processed_frame)
                    
                # Log progress
                processed_count += len(frames)
                logger.info(f"Processed {{processed_count}}/{{total_frames}} frames ({{processed_count/total_frames*100:.1f}}%)")
                
                # Clear batch
                frames = []
        
        # Clean up
        cap.release()
        out.release()
        
        # Convert to h264 using FFmpeg for better compatibility
        logger.info("Converting output to h264")
        os.system(f'ffmpeg -y -i "{{output_path}}" -c:v libx264 -pix_fmt yuv420p -preset medium -crf 18 "{{output_path}}.tmp.mp4"')
        os.replace(f"{{output_path}}.tmp.mp4", output_path)
        
        logger.info(f"Successfully processed {{processed_count}} frames. Output saved to {{output_path}}")
        return 0
        
    except Exception as e:
        logger.error(f"Error processing video: {{str(e)}}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    # Write the script to the file
    temp_script.write(script_content)
    temp_script.close()
    os.chmod(temp_script.name, 0o755)
    
    # Return command to run the script
    return f"python3 {temp_script.name} '{input_path}' '{output_path}'"