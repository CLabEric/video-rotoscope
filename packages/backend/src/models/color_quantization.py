#!/usr/bin/env python3
"""
Color quantization module for the Scanner Darkly effect
Implements various methods for color simplification and posterization
"""

import numpy as np
import cv2
from typing import Tuple, List, Optional, Union
import logging

# Set up logging
logger = logging.getLogger(__name__)

class ColorQuantizer:
    """
    Color quantization pipeline for Scanner Darkly effect
    """
    def __init__(
        self,
        method: str = "kmeans",
        num_colors: int = 8,
        smoothing: float = 0.5,
        saturation: float = 1.2,
        preserve_black: bool = True
    ):
        """
        Initialize color quantization with parameters
        
        Args:
            method: Quantization method ('kmeans', 'meanshift', 'bilateral')
            num_colors: Number of colors to use in the quantized output
            smoothing: Amount of smoothing to apply (0.0-1.0)
            saturation: Saturation multiplier (1.0 is original)
            preserve_black: Whether to preserve black edges
        """
        self.method = method.lower()
        self.num_colors = max(2, num_colors)
        self.smoothing = np.clip(smoothing, 0.0, 1.0)
        self.saturation = saturation
        self.preserve_black = preserve_black
        
        # Validate method
        valid_methods = ["kmeans", "meanshift", "bilateral", "posterize"]
        if self.method not in valid_methods:
            logger.warning(f"Invalid method '{method}'. Using 'kmeans' instead.")
            self.method = "kmeans"
    
    def adjust_saturation(self, image: np.ndarray) -> np.ndarray:
        """
        Adjust the saturation of the input image
        
        Args:
            image: Input BGR image
            
        Returns:
            Saturation-adjusted image
        """
        # Convert to HSV for easier saturation adjustment
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
        
        # Adjust saturation
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self.saturation, 0, 255)
        
        # Convert back to BGR
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    
    def apply_smoothing(self, image: np.ndarray) -> np.ndarray:
        """
        Apply smoothing to the image based on the smoothing parameter
        
        Args:
            image: Input BGR image
            
        Returns:
            Smoothed image
        """
        if self.smoothing <= 0:
            return image
        
        # Calculate smoothing parameters based on the smoothing value
        sigma_color = 10 + (40 * self.smoothing)
        sigma_space = 5 + (10 * self.smoothing)
        
        # Apply bilateral filter for edge-preserving smoothing
        return cv2.bilateralFilter(
            image, 
            d=9, 
            sigmaColor=sigma_color, 
            sigmaSpace=sigma_space
        )
    
    def quantize_kmeans(self, image: np.ndarray) -> np.ndarray:
        """
        Apply k-means clustering for color quantization
        
        Args:
            image: Input BGR image
            
        Returns:
            Color-quantized image
        """
        # Reshape the image for k-means
        h, w = image.shape[:2]
        reshapedImage = image.reshape((-1, 3)).astype(np.float32)
        
        # Define criteria and apply k-means
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            reshapedImage, 
            self.num_colors, 
            None, 
            criteria, 
            attempts=10, 
            flags=cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Map pixels to their closest center
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()]
        
        # Reshape back to the original image dimensions
        return quantized.reshape((h, w, 3))
    
    def quantize_meanshift(self, image: np.ndarray) -> np.ndarray:
        """
        Apply mean shift segmentation for color quantization
        
        Args:
            image: Input BGR image
            
        Returns:
            Color-quantized image
        """
        # Calculate parameters based on num_colors
        # Fewer colors = larger spatial radius and range radius
        spatial_radius = max(10, int(50 / (self.num_colors / 8)))
        range_radius = max(10, int(50 / (self.num_colors / 8)))
        
        # Apply mean shift
        quantized = cv2.pyrMeanShiftFiltering(
            image, 
            sp=spatial_radius, 
            sr=range_radius, 
            maxLevel=2
        )
        
        return quantized
    
    def quantize_bilateral(self, image: np.ndarray) -> np.ndarray:
        """
        Apply bilateral filtering for color simplification
        
        Args:
            image: Input BGR image
            
        Returns:
            Color-simplified image
        """
        # Apply strong bilateral filtering multiple times
        result = image.copy()
        iterations = max(1, int(3 * self.smoothing))
        
        for _ in range(iterations):
            result = cv2.bilateralFilter(
                result, 
                d=9, 
                sigmaColor=75, 
                sigmaSpace=75
            )
        
        # Apply posterization to further reduce colors
        result = self.posterize(result)
        
        return result
    
    def posterize(self, image: np.ndarray) -> np.ndarray:
        """
        Apply posterization (reduce number of intensity levels)
        
        Args:
            image: Input BGR image
            
        Returns:
            Posterized image
        """
        # Calculate number of levels per channel based on num_colors
        # (approximated from total colors to per-channel levels)
        levels = max(2, int(np.cbrt(self.num_colors)))
        
        # Create LUT (Look-Up Table) for posterization
        lut = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            lut[i] = np.clip(int(levels * i / 256) * (256 // levels), 0, 255)
        
        # Apply LUT to each channel
        result = image.copy()
        for c in range(3):  # BGR
            result[:, :, c] = cv2.LUT(image[:, :, c], lut)
        
        return result
    
    def merge_with_edges(self, quantized: np.ndarray, edges: np.ndarray) -> np.ndarray:
        """
        Merge quantized colors with edge map
        
        Args:
            quantized: Quantized color image
            edges: Edge map (0-1 range, where 1 is an edge)
            
        Returns:
            Merged image with edges overlaid
        """
        if self.preserve_black and edges is not None:
            # Create a 3-channel edge map (black edges)
            edge_map = np.zeros_like(quantized)
            
            # Convert edges to binary with threshold
            binary_edges = (edges > 0.2).astype(np.uint8) * 255
            
            # Create a mask for the edges
            edge_mask = cv2.cvtColor(binary_edges, cv2.COLOR_GRAY2BGR) / 255.0
            
            # Overlay edges on the quantized image
            result = quantized * (1 - edge_mask) + edge_map * edge_mask
            
            return result.astype(np.uint8)
        else:
            return quantized
    
    def quantize(self, image: np.ndarray, edges: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply color quantization to the input image
        
        Args:
            image: Input BGR image
            edges: Optional edge map to preserve (0-1 range)
            
        Returns:
            Color-quantized image
        """
        # Apply saturation adjustment
        saturated = self.adjust_saturation(image)
        
        # Apply smoothing
        smoothed = self.apply_smoothing(saturated)
        
        # Apply color quantization based on selected method
        if self.method == "kmeans":
            quantized = self.quantize_kmeans(smoothed)
        elif self.method == "meanshift":
            quantized = self.quantize_meanshift(smoothed)
        elif self.method == "bilateral":
            quantized = self.quantize_bilateral(smoothed)
        else:  # posterize
            quantized = self.posterize(smoothed)
        
        # Merge with edges if provided
        if edges is not None:
            return self.merge_with_edges(quantized, edges)
        
        return quantized