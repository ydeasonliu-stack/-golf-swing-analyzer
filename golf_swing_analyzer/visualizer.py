"""Video processing and visualization."""
import cv2
import numpy as np
from typing import Tuple, List


def draw_spine_line(frame: np.ndarray, spine_line: Tuple, color: Tuple = (0, 255, 0), thickness: int = 2) -> np.ndarray:
    """Draw spine line on frame.
    
    Args:
        frame: video frame
        spine_line: ((x1, y1), (x2, y2))
        color: BGR color tuple
        thickness: line thickness
    
    Returns:
        frame with spine line drawn
    """
    if spine_line:
        pt1, pt2 = spine_line
        cv2.line(frame, pt1, pt2, color, thickness)
    return frame


def draw_head_circle(frame: np.ndarray, circle: Tuple, color: Tuple = (255, 0, 0), thickness: int = 2) -> np.ndarray:
    """Draw head circle on frame.
    
    Args:
        frame: video frame
        circle: (center, radius)
        color: BGR color tuple
        thickness: line thickness (-1 for filled)
    
    Returns:
        frame with circle drawn
    """
    if circle:
        center, radius = circle
        cv2.circle(frame, center, radius, color, thickness)
    return frame


def draw_head_point(frame: np.ndarray, head_pos: Tuple, color: Tuple = (0, 0, 255), radius: int = 5) -> np.ndarray:
    """Draw head position as a small circle.
    
    Args:
        frame: video frame
        head_pos: (x, y)
        color: BGR color tuple
        radius: circle radius
    
    Returns:
        frame with head point drawn
    """
    if head_pos:
        cv2.circle(frame, head_pos, radius, color, -1)
    return frame


def draw_status_text(frame: np.ndarray, text: str, position: Tuple = (10, 30), 
                     color: Tuple = (255, 255, 255), font_scale: float = 1.0) -> np.ndarray:
    """Draw status text on frame.
    
    Returns:
        frame with text drawn
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(frame, text, position, font, font_scale, color, 2)
    return frame


def process_video_frame(frame: np.ndarray, spine_line: Tuple, head_circle: Tuple, 
                       head_pos: Tuple, head_outside: bool) -> np.ndarray:
    """Draw all annotations on frame.
    
    Returns:
        annotated frame
    """
    # Draw spine line (green)
    frame = draw_spine_line(frame, spine_line, color=(0, 255, 0), thickness=2)
    
    # Draw head circle - red if head is outside, green if inside
    circle_color = (0, 0, 255) if head_outside else (0, 255, 0)
    frame = draw_head_circle(frame, head_circle, color=circle_color, thickness=2)
    
    # Draw head position
    frame = draw_head_point(frame, head_pos, color=(0, 255, 255), radius=5)
    
    # Draw status
    status = "❌ Head Outside Circle" if head_outside else "✓ Head Inside Circle"
    status_color = (0, 0, 255) if head_outside else (0, 255, 0)
    frame = draw_status_text(frame, status, position=(10, 30), color=status_color, font_scale=0.8)
    
    return frame
