#!/usr/bin/env python3
"""
Edge detection module using HED (Holistically-Nested Edge Detection)
for the Scanner Darkly effect
"""

import os
import numpy as np
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
from typing import Union, Tuple, Optional

print(cv2.__version__)

# Set up logging
logger = logging.getLogger(__name__)

class HEDNet(nn.Module):
    """
    Holistically-Nested Edge Detection Network
    Based on the paper: https://arxiv.org/abs/1504.06375
    """
    def __init__(self):
        super(HEDNet, self).__init__()
        
        # VGG16 Backbone Layers
        self.conv1_1 = nn.Conv2d(3, 64, 3, padding=1)
        self.conv1_2 = nn.Conv2d(64, 64, 3, padding=1)
        
        self.conv2_1 = nn.Conv2d(64, 128, 3, padding=1)
        self.conv2_2 = nn.Conv2d(128, 128, 3, padding=1)
        
        self.conv3_1 = nn.Conv2d(128, 256, 3, padding=1)
        self.conv3_2 = nn.Conv2d(256, 256, 3, padding=1)
        self.conv3_3 = nn.Conv2d(256, 256, 3, padding=1)
        
        self.conv4_1 = nn.Conv2d(256, 512, 3, padding=1)
        self.conv4_2 = nn.Conv2d(512, 512, 3, padding=1)
        self.conv4_3 = nn.Conv2d(512, 512, 3, padding=1)
        
        self.conv5_1 = nn.Conv2d(512, 512, 3, padding=1)
        self.conv5_2 = nn.Conv2d(512, 512, 3, padding=1)
        self.conv5_3 = nn.Conv2d(512, 512, 3, padding=1)
        
        # Side output layers (edge prediction)
        self.dsn1 = nn.Conv2d(64, 1, 1)
        self.dsn2 = nn.Conv2d(128, 1, 1)
        self.dsn3 = nn.Conv2d(256, 1, 1)
        self.dsn4 = nn.Conv2d(512, 1, 1)
        self.dsn5 = nn.Conv2d(512, 1, 1)
        
        # Fusion layer
        self.fuse = nn.Conv2d(5, 1, 1)
        
        # Max pooling
        self.pool = nn.MaxPool2d(2, stride=2, ceil_mode=True)
    
    def forward(self, x):
        # VGG16 Backbone with side outputs
        # Stage 1
        conv1_1 = F.relu(self.conv1_1(x))
        conv1_2 = F.relu(self.conv1_2(conv1_1))
        side_output1 = self.dsn1(conv1_2)
        pool1 = self.pool(conv1_2)
        
        # Stage 2
        conv2_1 = F.relu(self.conv2_1(pool1))
        conv2_2 = F.relu(self.conv2_2(conv2_1))
        side_output2 = self.dsn2(conv2_2)
        pool2 = self.pool(conv2_2)
        
        # Stage 3
        conv3_1 = F.relu(self.conv3_1(pool2))
        conv3_2 = F.relu(self.conv3_2(conv3_1))
        conv3_3 = F.relu(self.conv3_3(conv3_2))
        side_output3 = self.dsn3(conv3_3)
        pool3 = self.pool(conv3_3)
        
        # Stage 4
        conv4_1 = F.relu(self.conv4_1(pool3))
        conv4_2 = F.relu(self.conv4_2(conv4_1))
        conv4_3 = F.relu(self.conv4_3(conv4_2))
        side_output4 = self.dsn4(conv4_3)
        pool4 = self.pool(conv4_3)
        
        # Stage 5
        conv5_1 = F.relu(self.conv5_1(pool4))
        conv5_2 = F.relu(self.conv5_2(conv5_1))
        conv5_3 = F.relu(self.conv5_3(conv5_2))
        side_output5 = self.dsn5(conv5_3)
        
        # Upsampling side outputs to the original size
        h, w = x.size(2), x.size(3)
        
        side_output1 = F.interpolate(side_output1, size=(h, w), mode='bilinear', align_corners=True)
        side_output2 = F.interpolate(side_output2, size=(h, w), mode='bilinear', align_corners=True)
        side_output3 = F.interpolate(side_output3, size=(h, w), mode='bilinear', align_corners=True)
        side_output4 = F.interpolate(side_output4, size=(h, w), mode='bilinear', align_corners=True)
        side_output5 = F.interpolate(side_output5, size=(h, w), mode='bilinear', align_corners=True)
        
        # Apply sigmoid for each side output
        side_output1 = torch.sigmoid(side_output1)
        side_output2 = torch.sigmoid(side_output2)
        side_output3 = torch.sigmoid(side_output3)
        side_output4 = torch.sigmoid(side_output4)
        side_output5 = torch.sigmoid(side_output5)
        
        # Concatenate side outputs
        fuse_cat = torch.cat((side_output1, side_output2, side_output3, side_output4, side_output5), dim=1)
        
        # Fuse side outputs
        fuse = self.fuse(fuse_cat)
        fuse = torch.sigmoid(fuse)
        
        # Return all outputs for training, or just the fused output for inference
        return (side_output1, side_output2, side_output3, side_output4, side_output5, fuse)


class EdgeDetector:
    """
    Edge detection pipeline with preprocessing and postprocessing
    """
    def __init__(
        self, 
        model_path: str = None, 
        use_gpu: bool = True,
        edge_strength: float = 0.8,
        threshold: float = 0.3
    ):
        """
        Initialize the edge detector with the provided model
        
        Args:
            model_path: Path to the pre-trained model weights
            use_gpu: Whether to use GPU acceleration if available
            edge_strength: Control the strength of detected edges (0.0-1.0)
            threshold: Threshold for edge detection (0.0-1.0)
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() and use_gpu else "cpu")
        self.edge_strength = edge_strength
        self.threshold = threshold
        
        # Initialize the model
        self.model = HEDNet().to(self.device)
        self.model.eval()  # Set to evaluation mode
        
        # Load pre-trained weights if provided
        if model_path and os.path.exists(model_path):
            logger.info(f"Loading pre-trained model from {model_path}")
            try:
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                logger.info("Model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load model: {str(e)}")
                raise
        else:
            logger.warning("No model weights provided, using randomly initialized weights")
    
    def preprocess_image(self, image: np.ndarray) -> torch.Tensor:
        """
        Preprocess the input image for the model
        
        Args:
            image: Input image in BGR format (OpenCV default)
            
        Returns:
            Preprocessed image tensor
        """
        # Convert BGR to RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Normalize to 0-1
        image_rgb = image_rgb.astype(np.float32) / 255.0
        
        # Transpose to CHW format and add batch dimension
        image_tensor = torch.from_numpy(image_rgb.transpose(2, 0, 1)).unsqueeze(0)
        
        return image_tensor.to(self.device)
    
    def postprocess_edges(self, edge_map: torch.Tensor) -> np.ndarray:
        """
        Postprocess the edge map for visualization or further processing
        
        Args:
            edge_map: Raw edge map from the model (tensor)
            
        Returns:
            Processed edge map as numpy array
        """
        # Convert to numpy and remove batch dimension
        edge_map = edge_map.detach().cpu().numpy()[0, 0]
        
        # Apply threshold and adjust edge strength
        edge_map = (edge_map > self.threshold).astype(np.float32) * self.edge_strength
        
        # Ensure values are in 0-1 range
        edge_map = np.clip(edge_map, 0, 1)
        
        return edge_map
    
    def enhance_edges(self, edge_map: np.ndarray, thickness: float = 1.0) -> np.ndarray:
        """
        Enhance edges for the Scanner Darkly look
        
        Args:
            edge_map: Edge map from postprocessing
            thickness: Edge thickness multiplier
            
        Returns:
            Enhanced edge map
        """
        # Convert to 8-bit for OpenCV processing
        edge_map_8bit = (edge_map * 255).astype(np.uint8)
        
        # Apply dilation to thicken edges if needed
        if thickness > 1.0:
            kernel_size = max(1, int(thickness * 1.5))
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            edge_map_8bit = cv2.dilate(edge_map_8bit, kernel)
        
        # Optional: Apply thinning if thickness < 1.0
        if thickness < 1.0:
            edge_map_8bit = cv2.ximgproc.thinning(edge_map_8bit)
        
        # Convert back to float 0-1
        return edge_map_8bit.astype(np.float32) / 255.0
    
    def detect_edges_opencv(self, image: np.ndarray) -> np.ndarray:
        """
        Detect edges using OpenCV's DNN module with HED model
        """
        logger.info("Attempting to use OpenCV DNN for edge detection")
        
        # Prepare paths to model files
        model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                "model_weights", "hed.caffemodel")
        prototxt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                    "model_weights", "hed.prototxt")
        
        logger.info(f"Looking for model at: {model_path}")
        logger.info(f"Looking for prototxt at: {prototxt_path}")
        
        # Check if model files exist
        if not os.path.exists(model_path) or not os.path.exists(prototxt_path):
            logger.warning(f"HED model files not found, falling back to PyTorch")
            return None
        
        try:
            # Load the network
            logger.info("Loading HED model with OpenCV DNN")
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            
            # Prepare the image
            height, width = image.shape[:2]
            blob = cv2.dnn.blobFromImage(
                image, 
                scalefactor=1.0, 
                size=(width, height),
                mean=(104.00698793, 116.66876762, 122.67891434),
                swapRB=False, 
                crop=False
            )
            
            # Forward pass
            logger.info("Running inference with HED model")
            net.setInput(blob)
            hed_output = net.forward()
            
            # Post-process
            edges = hed_output[0, 0]
            
            # Apply threshold and scale
            edges = (edges > self.threshold).astype(np.float32) * self.edge_strength
            logger.info("Successfully detected edges with OpenCV DNN")
            
            return edges
        except Exception as e:
            logger.error(f"Error using OpenCV DNN for edge detection: {str(e)}")
            return None

    @torch.no_grad()  # Disable gradient computation for inference
    def detect_edges(
        self, 
        image: np.ndarray, 
        enhance: bool = True,
        thickness: float = 1.0
    ) -> np.ndarray:
        """
        Detect edges in the input image
        """
        logger.warning("detect_edges called, will try OpenCV DNN first")
        
        # Try OpenCV DNN first
        opencv_edges = self.detect_edges_opencv(image)
        
        if opencv_edges is not None:
            # If OpenCV HED worked, use those edges
            logger.info("Using OpenCV DNN edge detection result")
            edge_map = opencv_edges
        else:
            # Fall back to existing PyTorch implementation
            logger.info("Falling back to PyTorch edge detection")
            
            # Get original image dimensions
            h, w = image.shape[:2]
            
            # Resize large images to improve performance
            max_dim = 512
            if max(h, w) > max_dim:
                scale = max_dim / max(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                image_resized = cv2.resize(image, (new_w, new_h))
            else:
                image_resized = image
                scale = 1.0
            
            # Preprocess image
            input_tensor = self.preprocess_image(image_resized)
            
            # Forward pass
            outputs = self.model(input_tensor)
            
            # Get fused output (last item in tuple)
            fused_output = outputs[-1]
            
            # Postprocess
            edge_map = self.postprocess_edges(fused_output)
            
            # Resize back to original dimensions if needed
            if scale != 1.0:
                edge_map = cv2.resize(edge_map, (w, h))
        
        # Enhance edges if requested
        if enhance:
            edge_map = self.enhance_edges(edge_map, thickness)
        
        return edge_map


def download_model_weights(model_url: str, save_path: str) -> str:
    """
    Download pre-trained model weights if they don't exist
    
    Args:
        model_url: URL to download model weights
        save_path: Path to save the downloaded weights
        
    Returns:
        Path to the downloaded model weights
    """
    if os.path.exists(save_path):
        logger.info(f"Model weights already exist at {save_path}")
        return save_path
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    logger.info(f"Downloading model weights from {model_url}")
    try:
        import requests
        response = requests.get(model_url, stream=True)
        response.raise_for_status()
        
        # Save the model weights
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Model weights downloaded to {save_path}")
        return save_path
    
    except Exception as e:
        logger.error(f"Failed to download model weights: {str(e)}")
        raise