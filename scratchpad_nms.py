import numpy as np
import cv2
import time

def test_numpy_nms():
    # Simulation du output ONNX
    output = np.random.rand(67, 33600).astype(np.float32)
    dw, dh = 10, 10
    scale = 0.5
    
    start_time = time.perf_counter()
    
    # 1. Tranchage du tenseur
    output = output[:35, :] # Ignorer les 32 masques
    output = output.T # (33600, 35)
    
    # 2. Vectorisation Numpy
    scores = output[:, 4:35]
    class_ids = np.argmax(scores, axis=1)
    confidences = np.max(scores, axis=1)
    
    mask = confidences > 0.45
    filtered_output = output[mask]
    filtered_class_ids = class_ids[mask]
    filtered_confidences = confidences[mask]
    
    if len(filtered_output) > 0:
        boxes_np = filtered_output[:, :4]
        xc = boxes_np[:, 0]
        yc = boxes_np[:, 1]
        w = boxes_np[:, 2]
        h = boxes_np[:, 3]
        
        x_tl = (xc - w/2 - dw) / scale
        y_tl = (yc - h/2 - dh) / scale
        w_scaled = w / scale
        h_scaled = h / scale
        
        bboxes_list = np.column_stack((x_tl, y_tl, w_scaled, h_scaled)).tolist()
        scores_list = filtered_confidences.tolist()
        
        indices = cv2.dnn.NMSBoxes(bboxes_list, scores_list, 0.45, 0.45)
        indices = indices.flatten() if len(indices) > 0 else []
        
        # Extract kept
        kept_boxes = [bboxes_list[i] for i in indices]
        kept_class_ids = [filtered_class_ids[i] for i in indices]
        kept_scores = [scores_list[i] for i in indices]
    
    print(f"Time: {time.perf_counter() - start_time:.4f}s")

if __name__ == "__main__":
    test_numpy_nms()
