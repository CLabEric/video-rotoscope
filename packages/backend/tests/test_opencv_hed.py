# test_video_opencv_hed.py
import cv2
import os
import numpy as np
import time

# Print OpenCV version
print(f"OpenCV version: {cv2.__version__}")

# Check model files
model_path = "model_weights/hed.caffemodel"
prototxt_path = "model_weights/hed.prototxt"
print(f"Model file exists: {os.path.exists(model_path)}")
print(f"Prototxt file exists: {os.path.exists(prototxt_path)}")

# Input and output paths
input_video = "test_videos/4873446-hd_720_1280_50fps.mp4"
output_video = "test_videos/processed_scanner_darkly.mp4"

# Try to load and run HED model on full video
try:
    # Load model
    net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
    
    # Open input video
    cap = cv2.VideoCapture(input_video)
    if not cap.isOpened():
        print(f"Could not open video: {input_video}")
        exit(1)
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"Video properties: {width}x{height}, {fps} fps, {total_frames} frames")
    
    # Create output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height), isColor=True)
    
    # Process frames
    start_time = time.time()
    frame_count = 0
    
    # Temporal tracking variables
    prev_edges = None
    prev_color_reduced = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Convert to LAB color space for better color manipulation
        lab_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        
        # Process image with HED
        blob = cv2.dnn.blobFromImage(
            frame, 
            scalefactor=1.0, 
            size=(width, height),
            mean=(104.00698793, 116.66876762, 122.67891434),
            swapRB=False, 
            crop=False
        )
        
        net.setInput(blob)
        edges = net.forward()[0, 0]
        
        # Temporal edge smoothing with stronger edge preservation
        if prev_edges is not None:
            edges = edges * 0.6 + prev_edges * 0.4
        prev_edges = edges
        
        # More aggressive edge detection
        binary_edges = (edges > 0.2).astype(np.uint8) * 255
        
        # Dilate edges to make them more pronounced
        kernel = np.ones((3,3), np.uint8)
        binary_edges = cv2.dilate(binary_edges, kernel, iterations=1)
        
        # Color quantization in LAB space
        l_channel = lab_frame[:,:,0]
        pixels = l_channel.reshape((-1, 1)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        
        # Reduce to fewer color levels with more distinct separation
        k = 5  # Reduced color levels
        _, labels, centers = cv2.kmeans(
            pixels, 
            k, 
            None, 
            criteria, 
            10, 
            cv2.KMEANS_RANDOM_CENTERS
        )
        
        # Reconstruct lightness channel
        quantized_l = centers[labels.flatten()].reshape(l_channel.shape)
        
        # Reconstruct LAB image
        lab_frame[:,:,0] = quantized_l
        
        # Optional: Reduce color saturation
        lab_frame[:,:,1] = lab_frame[:,:,1] * 0.7  # Reduce a/b channel saturation
        lab_frame[:,:,2] = lab_frame[:,:,2] * 0.7
        
        # Convert back to BGR
        quantized_frame = cv2.cvtColor(lab_frame, cv2.COLOR_LAB2BGR)
        
        # Temporal color smoothing
        if prev_color_reduced is not None:
            quantized_frame = quantized_frame * 0.7 + prev_color_reduced * 0.3
        prev_color_reduced = quantized_frame
        
        # Create edge overlay with slight color variation
        edge_overlay = np.zeros_like(frame)
        edge_overlay[binary_edges > 0] = [40, 40, 40]  # Slightly varied dark gray
        
        # Blend quantized image with edges
        result = cv2.addWeighted(quantized_frame.astype(np.uint8), 0.9, edge_overlay, 0.1, 0)
        
        # Add slight color bleeding effect
        if frame_count % 2 == 0:
            result = cv2.GaussianBlur(result, (3,3), 0)
        
        # Write to output video
        out.write(result)
        
        frame_count += 1
        if frame_count % 10 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%) - {frame_count/elapsed:.2f} fps")
    
    # Clean up
    cap.release()
    out.release()
    
    # Final report
    total_time = time.time() - start_time
    print(f"Processed {frame_count} frames in {total_time:.2f} seconds ({frame_count/total_time:.2f} fps)")
    print(f"Output saved to {output_video}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    # Clean up if there was an error
    if 'cap' in locals() and cap is not None:
        cap.release()
    if 'out' in locals() and out is not None:
        out.release()