import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from torchvision.models.segmentation import deeplabv3_resnet50
from typing import List, Tuple

class ScannerDarklyEffect:
    def __init__(self, style='artistic'):
        """
        Initialize advanced rotoscoping with different style options
        
        Args:
            style: 'artistic', 'comic', 'watercolor', 'sketch'
        """
        self.style = style
        
        # Load pre-trained semantic segmentation model
        self.segmentation_model = deeplabv3_resnet50(pretrained=True)
        self.segmentation_model.eval()
        
        # Image preprocessing transform
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406], 
                std=[0.229, 0.224, 0.225]
            )
        ])
    
    def _segment_subject(self, frame: np.ndarray) -> np.ndarray:
        """
        Use semantic segmentation to isolate the subject
        
        Args:
            frame: Input BGR image
            
        Returns:
            Binary mask of the primary subject (person)
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Preprocess image
        input_tensor = self.transform(frame_rgb).unsqueeze(0)
        
        # Run inference
        with torch.no_grad():
            output = self.segmentation_model(input_tensor)['out'][0]
            output_predictions = output.argmax(0)
        
        # Create binary mask for person (class index 15 is typically person)
        person_mask = (output_predictions == 15).numpy().astype(np.uint8) * 255
        
        # Refine mask with morphological operations
        kernel = np.ones((5,5), np.uint8)
        person_mask = cv2.morphologyEx(person_mask, cv2.MORPH_CLOSE, kernel)
        person_mask = cv2.GaussianBlur(person_mask, (5,5), 0)
        
        return person_mask
    
    def _stylize_edges(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Apply artistic edge stylization
        
        Args:
            frame: Input BGR image
            mask: Binary mask of the subject
            
        Returns:
            Stylized image
        """
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect edges with Canny
        edges = cv2.Canny(gray, 50, 150)
        
        # Combine edges with person mask
        masked_edges = cv2.bitwise_and(edges, edges, mask=mask)
        
        # Style selection
        if self.style == 'comic':
            # Bold, defined lines
            edges_color = cv2.cvtColor(masked_edges, cv2.COLOR_GRAY2BGR)
            edges_color[np.where(edges_color > 0)] = [0, 0, 0]  # Black lines
            blended = cv2.addWeighted(frame, 0.7, edges_color, 0.3, 0)
        
        elif self.style == 'watercolor':
            # Soft, blended edges
            blurred = cv2.GaussianBlur(frame, (5,5), 0)
            edges_color = cv2.cvtColor(masked_edges, cv2.COLOR_GRAY2BGR)
            edges_color[np.where(edges_color > 0)] = [200, 200, 200]  # Light edges
            blended = cv2.addWeighted(blurred, 0.8, edges_color, 0.2, 0)
        
        elif self.style == 'sketch':
            # Pencil-like effect
            inv_edges = 255 - masked_edges
            sketch = cv2.merge([inv_edges, inv_edges, inv_edges])
            blended = cv2.addWeighted(frame, 0.6, sketch, 0.4, 0)
        
        else:  # artistic (default)
            # Softer, painterly edges
            edges_color = cv2.cvtColor(masked_edges, cv2.COLOR_GRAY2BGR)
            edges_color[np.where(edges_color > 0)] = [50, 50, 50]  # Dark gray edges
            blended = cv2.addWeighted(frame, 0.9, edges_color, 0.1, 0)
        
        return blended
    
    def _color_simplification(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """
        Simplify colors while preserving subject details
        
        Args:
            frame: Input BGR image
            mask: Binary mask of the subject
            
        Returns:
            Color-simplified image
        """
        # Convert to LAB color space for better color quantization
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Apply k-means clustering
        pixels = lab.reshape((-1, 3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        
        # Reduce to 6-8 colors
        k = 6
        _, labels, centers = cv2.kmeans(
            pixels, 
            k, 
            None, 
            criteria, 
            10, 
            cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Reconstruct image with reduced colors
        centers = centers.astype(np.uint8)
        quantized = centers[labels.flatten()].reshape(frame.shape)
        quantized = cv2.cvtColor(quantized, cv2.COLOR_LAB2BGR)
        
        # Blend with original masked region
        result = frame.copy()
        result[mask > 0] = quantized[mask > 0]
        
        return result
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray: