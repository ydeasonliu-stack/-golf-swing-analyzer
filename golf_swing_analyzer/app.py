"""Streamlit web interface for golf swing analyzer."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import cv2
import numpy as np
import tempfile
import time
from golf_swing_analyzer.visualizer import process_video_frame

st.set_page_config(page_title="Golf Swing Analyzer", layout="wide")
st.title("⛳ Golf Swing Head Movement Analyzer")

# Initialize session state
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False
if 'playing' not in st.session_state:
    st.session_state.playing = False
if 'current_frame' not in st.session_state:
    st.session_state.current_frame = 0

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    head_circle_radius = st.slider("Head Circle Radius", 30, 150, 60)

# Upload video
uploaded_file = st.file_uploader("上传视频", type=["mp4", "avi", "mov", "mkv"])

if uploaded_file is None:
    st.stop()

# Save video temporarily
with tempfile.TemporaryDirectory() as tmpdir:
    video_path = os.path.join(tmpdir, "input.mp4")
    with open(video_path, 'wb') as f:
        f.write(uploaded_file.read())
    
    # Read video info
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
    if st.button("▶️ 开始分析", use_container_width=True):
        with st.spinner("分析中..."):
            cap = cv2.VideoCapture(video_path)
            output_frames = []
            head_outside_frames = []
            
            head_initial = (int(head_x / 2), int(head_y / 2))
            spine_line = ((int(shoulder_x / 2), int(shoulder_y / 2)), (int(hip_x / 2), int(hip_y / 2)))
            head_circle = (head_initial, head_circle_radius // 2)
            current_head_pos = head_initial
            
            progress = st.progress(0)
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Scale down
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
        
        # Save to session state
        st.session_state.output_frames = output_frames
        st.session_state.head_outside_frames = head_outside_frames
        st.session_state.fps = fps
        st.session_state.analyzed = True
        
        st.success("✅ 分析完成")
        st.rerun()

# Display results if analyzed
if st.session_state.analyzed and 'output_frames' in st.session_state:
    output_frames = st.session_state.output_frames
    head_outside_frames = st.session_state.head_outside_frames
    fps = st.session_state.fps
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总帧数", len(output_frames))
    with col2:
        outside_count = sum(head_outside_frames)
        st.metric("越界帧数", outside_count)
    with col3:
        pct = (outside_count / len(output_frames) * 100) if output_frames else 0
        st.metric("越界百分比", f"{pct:.1f}%")
    
    # Playback
    st.header("📹 分析视频 - 实时播放")
    st.markdown("**红圈** = 头部越界 | **绿圈** = 头部在范围内 | **黄点** = 当前头部位置 | **绿线** = 脊椎线")
    
    col_speed, col_btn = st.columns([2, 1])
    with col_speed:
        speed = st.slider("播放速度", 0.5, 2.0, 1.0, key="playback_speed")
    with col_btn:
        if st.button("▶️ 开始播放", use_container_width=True, key="play_btn"):
            st.session_state.playing = True
            st.session_state.current_frame = 0
    
    # Create placeholders
    frame_placeholder = st.empty()
    info_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    # Play frames if playing flag is set
    if st.session_state.playing:
        for i in range(len(output_frames)):
            # Display frame
            frame_placeholder.image(cv2.cvtColor(output_frames[i], cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # Display status
            status_text = "🔴 头部越界" if head_outside_frames[i] else "🟢 头部在范围内"
            info_placeholder.write(f"**第 {i + 1} / {len(output_frames)} 帧** - {status_text}")
            
            # Display progress
            progress_placeholder.progress((i + 1) / len(output_frames))
            
            # Delay between frames
            time.sleep(1.0 / (fps * speed))
        
        # After playback completes
        st.session_state.playing = False
        st.success("✅ 播放完成！")
    else:
        # Show first frame as preview
        if len(output_frames) > 0:
            frame_placeholder.image(cv2.cvtColor(output_frames[0], cv2.COLOR_BGR2RGB), use_container_width=True)
            info_placeholder.write("点击上方按钮开始播放视频")
            progress_placeholder.progress(0)
