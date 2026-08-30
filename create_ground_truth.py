"""
Ground Truth Creation Tool for Aswan-SmartCurbs-AI

This professional tool allows manual annotation of vehicles while 
visualizing the smart parking zones for high-accuracy evaluation.
"""

import cv2
import json
import os
import numpy as np
from pathlib import Path

# Import project settings to ensure system integration
try:
    from occupancy import PARKING_SPACES
except ImportError:
    # Fallback if the occupancy module is not found
    PARKING_SPACES = {}

class AnnotationTool:
    """Interactive annotation tool for vehicle detection with SmartCurbs support."""
    
    # Mapping vehicle classes to specific BGR colors for visualization
    CLASS_COLORS = {
        "car": (0, 255, 0),        # Green
        "bus": (0, 165, 255),      # Orange
        "truck": (255, 0, 0),      # Blue
        "motorcycle": (255, 255, 0), # Cyan
        None: (0, 255, 255)        # Yellow (for pending/unconfirmed boxes)
    }
    
    # Keyboard shortcut mapping for classes
    CLASS_MAP = {
        'c': 'car',
        'b': 'bus',
        't': 'truck',
        'm': 'motorcycle'
    }
    
    def __init__(self, frame, frame_number):
        """Initialize the annotation tool with a specific video frame."""
        self.original_frame = frame.copy()
        self.frame = frame.copy()
        self.frame_number = frame_number
        self.confirmed_boxes = []  # Stores finalized annotations: {bbox, class_name}
        self.pending_box = None    # Temporarily stores a box until a class is assigned
        self.drawing = False       # Flag to track if the mouse is currently dragging
        self.start_x = 0
        self.start_y = 0
        self.quit_flag = False     # Flag to signal early exit
        
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing bounding boxes."""
        
        # Start drawing when left mouse button is pressed
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_x = x
            self.start_y = y
            
        # Update the box preview while moving the mouse
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                # Reset frame to clean state and redraw all elements
                self.frame = self.original_frame.copy()
                self._draw_parking_layout() # Draw parking zones in the background
                self._draw_confirmed_boxes()
                # Draw the current rectangle being dragged
                cv2.rectangle(self.frame, (self.start_x, self.start_y), (x, y), (0, 255, 255), 2)
                self._draw_instructions()
                cv2.imshow("SmartCurbs Annotation Tool", self.frame)
                
        # Finalize the box dimensions when the button is released
        elif event == cv2.EVENT_LBUTTONUP:
            if self.drawing:
                self.drawing = False
                # Calculate coordinates (ensuring x1,y1 is top-left and x2,y2 is bottom-right)
                x1, y1 = min(self.start_x, x), min(self.start_y, y)
                x2, y2 = max(self.start_x, x), max(self.start_y, y)
                
                # Minimum size check to avoid accidental clicks
                if (x2 - x1) > 5 and (y2 - y1) > 5:
                    self.pending_box = [x1, y1, x2, y2]
                    print(f"✓ Box drawn. Select class: C=Car, B=Bus, T=Truck, M=Motorcycle")
                
                self._update_display()

    def _draw_parking_layout(self):
        """Draw parking polygons to ensure Ground Truth Alignment with existing zones."""
        for space_id, polygon in PARKING_SPACES.items():
            pts = np.array(polygon, np.int32)
            # Draw the parking slot in light gray as a visual reference guide
            cv2.polylines(self.frame, [pts], True, (150, 150, 150), 1)
            cv2.putText(self.frame, f"Slot {space_id}", tuple(pts[0]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    def _draw_confirmed_boxes(self):
        """Draw all finalized bounding boxes with their respective class labels."""
        for i, item in enumerate(self.confirmed_boxes):
            bbox = item["bbox"]
            class_name = item["class_name"]
            color = self.CLASS_COLORS.get(class_name, (255, 255, 255))
            x1, y1, x2, y2 = bbox
            cv2.rectangle(self.frame, (x1, y1), (x2, y2), color, 2)
            label = f"{class_name}"
            cv2.putText(self.frame, label, (x1, y1 - 8), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def _draw_pending_box(self):
        """Draw the box currently awaiting a class assignment from the user."""
        if self.pending_box is not None:
            x1, y1, x2, y2 = self.pending_box
            color = self.CLASS_COLORS[None]
            cv2.rectangle(self.frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(self.frame, "SELECT CLASS", (x1, y1 - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def _draw_instructions(self):
        """Render UI instructions and metadata overlay on the frame."""
        instructions = [
            f"FRAME: {self.frame_number}",
            "C: Car | B: Bus | T: Truck | M: Moto",
            "R: Remove Last | N: Next Frame",
            "Q: Save and Quit"
        ]
        # Draw a semi-transparent black background for better text readability
        cv2.rectangle(self.frame, (5, 5), (280, 110), (0,0,0), -1) 
        y_offset = 25
        for instruction in instructions:
            cv2.putText(self.frame, instruction, (15, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 22
    
    def _update_display(self):
        """Refresh the UI by redrawing all static and dynamic layers."""
        self.frame = self.original_frame.copy()
        self._draw_parking_layout() # Add the parking map layer
        self._draw_confirmed_boxes()
        self._draw_pending_box()
        self._draw_instructions()
        cv2.imshow("SmartCurbs Annotation Tool", self.frame)
    
    def _assign_class_to_pending(self, class_name):
        """Bind a vehicle class to the pending box and move it to confirmed boxes."""
        if self.pending_box is not None:
            self.confirmed_boxes.append({"bbox": self.pending_box, "class_name": class_name})
            self.pending_box = None
            self._update_display()
    
    def run(self):
        """Execute the main tool loop for the current frame."""
        window_name = "SmartCurbs Annotation Tool"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        self._update_display()
        
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 255: continue # No key pressed
            key_char = chr(key).lower()
            
            # Logic for keyboard shortcuts
            if key_char in self.CLASS_MAP:
                self._assign_class_to_pending(self.CLASS_MAP[key_char])
            elif key_char == 'n': # Next Frame
                break
            elif key_char == 'q': # Quit and Save
                self.quit_flag = True; 
                break
            elif key_char == 'r' and self.confirmed_boxes: # Undo last annotation
                self.confirmed_boxes.pop()
                self._update_display()
        
        cv2.destroyWindow(window_name)
        return self.confirmed_boxes, self.quit_flag

# --- Functions for File Handling and Data Processing ---

def get_project_root():
    """Navigate to the project's base directory regardless of script location."""
    return Path(__file__).parent.parent.parent.parent

def create_ground_truth(video_path, evaluation_frames, output_path):
    """Iterate through selected video frames and collect annotations to save as JSON."""
    print(f"\n[START] Annotating {len(evaluation_frames)} frames for SmartCurbs-AI...")
    cap = cv2.VideoCapture(video_path)
    
    # Data structure for the final JSON output
    ground_truth = {"video": video_path, "annotations": []}
    class_counts = {"car": 0, "bus": 0, "truck": 0, "motorcycle": 0}
    
    for frame_number in evaluation_frames:
        # Seek to the specific frame in the video
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = cap.read()
        if not ret: break
        
        # Launch UI for this specific frame
        tool = AnnotationTool(frame, frame_number)
        confirmed_boxes, quit_flag = tool.run()
        
        if quit_flag: break
        
        # Format the frame results
        frame_annotation = {"frame_number": frame_number, "objects": []}
        for item in confirmed_boxes:
            frame_annotation["objects"].append({
                "class_name": item["class_name"], 
                "bounding_box": item["bbox"]
            })
            class_counts[item["class_name"]] += 1
            
        ground_truth["annotations"].append(frame_annotation)
        print(f"  ✓ Frame {frame_number}: {len(confirmed_boxes)} objects saved.")
    
    cap.release()
    
    # Save the gathered data to a JSON file
    with open(output_path, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    # Print a summary of the session
    print("\n" + "="*30 + "\nANNOTATION SUMMARY\n" + "="*30)
    for cls, count in class_counts.items(): 
        print(f"{cls.capitalize()}s: {count}")
    print(f"Results saved to: {output_path}\n" + "="*30)

def main():
    """Main entry point: Setup paths and list of frames for scientific evaluation."""
    # Use absolute path resolution to ensure the script works from any directory
    project_root = get_project_root()
    video_path = str(project_root / "ai" / "vehicle_detection" / "data" / "input.mp4")
    output_path = str(project_root / "ai" / "vehicle_detection" / "outputs" / "ground_truth.json")
    
    # Selection of distributed frames for a statistically sound evaluation
    evaluation_frames = [0, 150, 300, 450, 600, 740]
    
    create_ground_truth(video_path, evaluation_frames, output_path)

if __name__ == "__main__":
    main()