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
input_video = "test_videos/sample.mp4"
output_video = "test_videos/processed_opencv_hed.mp4"

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
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
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
        
        # Apply threshold and create binary edge map
        edge_map = (edges > 0.3).astype(np.uint8) * 255
        
        # Convert to 3-channel for visualization
        edge_map_color = cv2.cvtColor(edge_map, cv2.COLOR_GRAY2BGR)
        
        # Apply simple color quantization (for visualization)
        # You can replace this with your color_quantizer if desired
        color_reduced = cv2.bilateralFilter(frame, 9, 75, 75)
        result = color_reduced.copy()
        
        # Add black edges
        result[edge_map > 0] = [0, 0, 0]
        
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