"""Streamlit web interface for golf swing analyzer."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import cv2
import numpy as np
import tempfile
from golf_swing_analyzer.visualizer import process_video_frame


st.set_page_config(page_title="Golf Swing Analyzer", layout="wide")
st.title("⛳ Golf Swing Head Movement Analyzer")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    head_circle_radius = st.slider("Head Circle Radius", 30, 150, 60)

# Upload video
uploaded_file = st.file_uploader("上传视频", type=["mp4", "avi", "mov", "mkv"])

if uploaded_file is None:
    st.info("请上传一个视频文件")
    st.stop()

# Save video temporarily
with tempfile.TemporaryDirectory() as tmpdir:
    video_path = os.path.join(tmpdir, "input.mp4")
    with open(video_path, 'wb') as f:
        f.write(uploaded_file.read())
    
    # Read video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        st.error("❌ 无法打开视频")
        st.stop()
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    st.info(f"📹 {width}x{height} @ {fps:.1f}fps, 共 {total_frames} 帧")
    
    # Get first frame
    ret, first_frame = cap.read()
    cap.release()
    
    if not ret:
        st.error("❌ 无法读取视频")
        st.stop()
    
    # Step 1: Mark keypoints
    st.header("第1步: 标记首帧关键点")
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB), use_container_width=True)
    
    with col2:
        st.markdown("**输入坐标 (像素)**")
        head_x = st.number_input("头部 X", 0, width, width//2)
        head_y = st.number_input("头部 Y", 0, height, height//3)
        shoulder_x = st.number_input("肩膀 X", 0, width, width//2)
        shoulder_y = st.number_input("肩膀 Y", 0, height, height//2)
        hip_x = st.number_input("臀部 X", 0, width, width//2)
        hip_y = st.number_input("臀部 Y", 0, height, 2*height//3)
    
    # Preview
    preview = first_frame.copy()
    cv2.circle(preview, (int(head_x), int(head_y)), 12, (0, 255, 255), -1)
    cv2.circle(preview, (int(shoulder_x), int(shoulder_y)), 8, (0, 255, 0), 2)
    cv2.circle(preview, (int(hip_x), int(hip_y)), 8, (255, 0, 0), 2)
    cv2.line(preview, (int(shoulder_x), int(shoulder_y)), (int(hip_x), int(hip_y)), (0, 255, 0), 2)
    
    st.markdown("**标记预览**")
    st.image(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB), use_container_width=True)
    
    # Step 2: Analyze
    if st.button("▶️ 开始分析"):
        with st.spinner("处理中..."):
            cap = cv2.VideoCapture(video_path)
            output_frames = []
            head_outside_frames = []
            
            head_initial = (int(head_x / 2), int(head_y / 2))  # Scale down coords
            spine_line = ((int(shoulder_x / 2), int(shoulder_y / 2)), (int(hip_x / 2), int(hip_y / 2)))
            head_circle = (head_initial, head_circle_radius // 2)
            current_head_pos = head_initial
            
            progress = st.progress(0)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Scale down frame by 2x (1/4 area)
                frame = cv2.resize(frame, (width // 2, height // 2))
                
                # Track head
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, np.array([0, 20, 70]), np.array([20, 255, 255]))
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    valid = []
                    for c in contours:
                        x, y, w, h = cv2.boundingRect(c)
                        cx, cy = x + w//2, y + h//2
                        d = np.sqrt((cx - current_head_pos[0])**2 + (cy - current_head_pos[1])**2)
                        if d < 200:
                            valid.append((d, (cx, cy)))
                    if valid:
                        current_head_pos = sorted(valid)[0][1]
                
                # Check outside circle
                dist = np.sqrt((current_head_pos[0] - head_circle[0][0])**2 + 
                             (current_head_pos[1] - head_circle[0][1])**2)
                head_outside = dist > head_circle[1]
                head_outside_frames.append(head_outside)
                
                # Annotate
                annotated = process_video_frame(frame, spine_line, head_circle, 
                                               current_head_pos, head_outside)
                output_frames.append(annotated)
                
                frame_count += 1
                progress.progress(min(frame_count / total_frames, 1.0))
            
            cap.release()
        
        # Store in session state for playback
        st.session_state.output_frames = output_frames
        st.session_state.head_outside_frames = head_outside_frames
        st.success("✅ 分析完成")
        
        # Step 3: Display results (only if analysis completed)
        if 'output_frames' in st.session_state:
            output_frames = st.session_state.output_frames
            head_outside_frames = st.session_state.head_outside_frames
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总帧数", len(output_frames))
            with col2:
                outside_count = sum(head_outside_frames)
                st.metric("越界帧数", outside_count)
            with col3:
                pct = (outside_count / len(output_frames) * 100) if output_frames else 0
                st.metric("越界百分比", f"{pct:.1f}%")
            
            # Slideshow with fixed annotations
            st.header("📹 分析视频")
            st.markdown("圆圈和脊椎线为固定参考标注，红色圆圈表示头部已越界，绿色表示在范围内")
            
            col_play, col_ctrl = st.columns([3, 1])
            with col_ctrl:
                speed = st.slider("播放速度", 0.5, 2.0, 1.0, key="speed")
                auto_play = st.checkbox("自动播放", value=True, key="auto")
            
            with col_play:
                frame_placeholder = st.empty()
                
                if not auto_play:
                    frame_idx = st.slider("帧号", 0, len(output_frames) - 1, 0, key="manual_frame")
                    frame_placeholder.image(cv2.cvtColor(output_frames[frame_idx], cv2.COLOR_BGR2RGB), use_container_width=True)
                else:
                    # Auto play
                    for i, frame in enumerate(output_frames):
                        frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        st.session_state.current_frame = i
