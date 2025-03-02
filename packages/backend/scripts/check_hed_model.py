#!/usr/bin/env python3
"""
Script to verify HED model files are present and properly formatted.
Run this script after deploying to confirm the Scanner Darkly effect can work.
"""

import os
import sys
import cv2
import numpy as np
from pathlib import Path

def check_model_files():
    """Check if HED model files exist and are properly formatted."""
    print("Checking HED model files...")
    
    # Define possible locations for model files
    model_locations = [
        "/opt/video-processor/model_weights",
        "model_weights",
        "../model_weights",
        os.path.expanduser("~/.cache/scanner_darkly")
    ]
    
    caffemodel_found = False
    prototxt_found = False
    caffemodel_path = None
    prototxt_path = None
    
    # Check each location
    for location in model_locations:
        cm_path = os.path.join(location, "hed.caffemodel")
        pt_path = os.path.join(location, "hed.prototxt")
        
        if os.path.exists(cm_path):
            caffemodel_found = True
            caffemodel_path = cm_path
            print(f"Found caffemodel at: {cm_path}")
            print(f"File size: {os.path.getsize(cm_path) / (1024*1024):.2f} MB")
        
        if os.path.exists(pt_path):
            prototxt_found = True
            prototxt_path = pt_path
            print(f"Found prototxt at: {pt_path}")
            print(f"File size: {os.path.getsize(pt_path)} bytes")
    
    if not caffemodel_found:
        print("ERROR: hed.caffemodel not found in any of the expected locations!")
        return False
    
    if not prototxt_found:
        print("ERROR: hed.prototxt not found in any of the expected locations!")
        return False
    
    # Try to load model with OpenCV
    print("\nAttempting to load model with OpenCV...")
    try:
        net = cv2.dnn.readNetFromCaffe(prototxt_path, caffemodel_path)
        print("Successfully loaded model with OpenCV!")
        
        # Create a small test image
        print("\nTesting inference on a small image...")
        test_img = np.zeros((100, 100, 3), dtype=np.uint8)
        test_img[25:75, 25:75] = 255  # White square in center
        
        # Run inference
        blob = cv2.dnn.blobFromImage(
            test_img, 
            scalefactor=1.0, 
            size=(100, 100),
            mean=(104.00698793, 116.66876762, 122.67891434),
            swapRB=False, 
            crop=False
        )
        
        net.setInput(blob)
        edges = net.forward()[0, 0]
        
        print(f"Inference successful: output shape = {edges.shape}")
        print("Test PASSED!")
        return True
        
    except Exception as e:
        print(f"ERROR loading or using model: {str(e)}")
        return False

def main():
    """Main function"""
    print(f"OpenCV version: {cv2.__version__}")
    
    if check_model_files():
        print("\n✅ Model files check PASSED - Scanner Darkly effect should work correctly!")
        sys.exit(0)
    else:
        print("\n❌ Model files check FAILED - Scanner Darkly effect will not work correctly!")
        print("\nDiagnostic steps:")
        print("1. Ensure model files are properly uploaded to S3")
        print("2. Check that user-data script downloads files correctly")
        print("3. Verify permissions on model directories and files")
        print("4. Check that OpenCV is properly installed with DNN support")
        sys.exit(1)

if __name__ == "__main__":
    main()