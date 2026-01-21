"""Simple pose estimation using face detection and contours."""
import cv2
import numpy as np
from typing import Tuple, Optional


class PoseAnalyzer:
    """Simplified pose analyzer using face detection and body contours."""
    
    def __init__(self):
        # Load face cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # HSV ranges for skin detection (for body tracking)
        self.lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        self.upper_skin = np.array([20, 255, 255], dtype=np.uint8)
    
    def detect_landmarks(self, frame: np.ndarray) -> dict:
        """Detect face and body regions.
        
        Returns:
            dict with detected regions
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Also detect skin regions for body
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_skin, self.upper_skin)
        
        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        return {'faces': faces, 'contours': contours, 'mask': mask, 'gray': gray}
    
    def get_key_points(self, detection: dict) -> dict:
        """Extract key points from detected face and body regions.
        
        Returns:
            dict with head, shoulders, hips
        """
        kp = {}
        faces = detection.get('faces', [])
        contours = detection.get('contours', [])
        
        # Head from face detection
        if len(faces) > 0:
            # Get largest face (assumed to be the person)
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, w, h = faces[0]
            kp['head'] = (x + w // 2, y + h // 2)
        
        # Body parts from contours
        if len(contours) > 0:
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]
            boxes = [cv2.boundingRect(c) for c in contours]
            boxes = sorted(boxes, key=lambda b: b[1])  # Sort by Y
            
            if len(boxes) > 1:
                # Shoulders (upper-middle region)
                x, y, w, h = boxes[len(boxes) // 2]
                kp['left_shoulder'] = (x, y + h // 2)
                kp['right_shoulder'] = (x + w, y + h // 2)
            
            if len(boxes) > 2:
                # Hips (bottom region)
                x, y, w, h = boxes[-1]
                kp['left_hip'] = (x, y + h)
                kp['right_hip'] = (x + w, y + h)
        
        # Fallback: if no face but have contours, use top contour as head
        if 'head' not in kp and len(boxes) > 0:
            x, y, w, h = boxes[0]
            kp['head'] = (x + w // 2, y + h // 2)
        
        return kp
    
    def compute_spine_line(self, kp: dict) -> Optional[Tuple]:
        """Compute spine axis from shoulder-hip midpoints.
        
        Returns:
            ((x1, y1), (x2, y2)) representing spine line or None
        """
        if not all(k in kp for k in ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']):
            return None
        
        # Midpoint of shoulders
        shoulder_mid = (
            (kp['left_shoulder'][0] + kp['right_shoulder'][0]) // 2,
            (kp['left_shoulder'][1] + kp['right_shoulder'][1]) // 2
        )
        # Midpoint of hips
        hip_mid = (
            (kp['left_hip'][0] + kp['right_hip'][0]) // 2,
            (kp['left_hip'][1] + kp['right_hip'][1]) // 2
        )
        return (shoulder_mid, hip_mid)
    
    def compute_head_circle(self, kp: dict, radius: int = 50) -> Optional[Tuple]:
        """Compute head circle (center and radius).
        
        Returns:
            (center, radius) or None
        """
        if 'head' not in kp:
            return None
        return (kp['head'], radius)
    
    def head_outside_circle(self, head_center: tuple, circle_center: tuple, radius: int) -> bool:
        """Check if head moves outside the circle.
        
        Returns:
            True if head is outside circle
        """
        if not head_center or not circle_center:
            return False
        dist = np.sqrt((head_center[0] - circle_center[0])**2 + (head_center[1] - circle_center[1])**2)
        return dist > radius
