"""Streamlit web interface for golf swing analyzer."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import cv2
import numpy as np
import tempfile
import time as time_module
from golf_swing_analyzer.visualizer import process_video_frame

st.set_page_config(page_title="Golf Swing Analyzer", layout="wide")
st.title("⛳ Golf Swing Head Movement Analyzer")

# Initialize session state
if 'output_frames' not in st.session_state:
    st.session_state.output_frames = None
if 'head_outside_frames' not in st.session_state:
    st.session_state.head_outside_frames = None
if 'fps' not in st.session_state:
    st.session_state.fps = None
if 'analyzed' not in st.session_state:
    st.session_state.analyzed = False

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    head_circle_radius = st.slider("Head Circle Radius", 30, 150, 60)

# Upload video
uploaded_file = st.file_uploader("上传视频", type=["mp4", "avi", "mov", "mkv"])

if uploaded_file is None:
    st.info("请上传一个视频文件")
    st.stop()

# Save and read video
with tempfile.TemporaryDirectory() as tmpdir:
    video_path = os.path.join(tmpdir, "input.mp4")
    with open(video_path, 'wb') as f:
        f.write(uploaded_file.read())
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    ret, first_frame = cap.read()
    cap.release()
    
    if not ret:
        st.error("❌ 无法读取视频")
        st.stop()
    
    st.info(f"📹 {width}x{height} @ {fps:.1f}fps, 共 {total_frames} 帧")
    
    # Step 1: Mark keypoints
    st.header("第1步: 标记首帧关键点")
    col1, col2 = st.columns(2)
    
    with col1:
        st.image(cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB), use_container_width=True)
    
    with col2:
        head_x = st.number_input("头部 X", 0, width, width//2)
        head_y = st.number_input("头部 Y", 0, height, height//3)
        shoulder_x = st.number_input("肩膀 X", 0, width, width//2)
        shoulder_y = st.number_input("肩膀 Y", 0, height, height//2)
        hip_x = st.number_input("臀部 X", 0, width, width//2)
        hip_y = st.number_input("臀部 Y", 0, height, 2*height//3)
    
    preview = first_frame.copy()
    cv2.circle(preview, (int(head_x), int(head_y)), 12, (0, 255, 255), -1)
    cv2.circle(preview, (int(shoulder_x), int(shoulder_y)), 8, (0, 255, 0), 2)
    cv2.circle(preview, (int(hip_x), int(hip_y)), 8, (255, 0, 0), 2)
    cv2.line(preview, (int(shoulder_x), int(shoulder_y)), (int(hip_x), int(hip_y)), (0, 255, 0), 2)
    
    st.image(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB), use_container_width=True)
    
    # Step 2: Analyze
    if st.button("▶️ 开始分析"):
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
                
                frame = cv2.resize(frame, (width // 2, height // 2))
                
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
                
                dist = np.sqrt((current_head_pos[0] - head_circle[0][0])**2 + 
                             (current_head_pos[1] - head_circle[0][1])**2)
                head_outside = dist > head_circle[1]
                head_outside_frames.append(head_outside)
                
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

# Display results if analyzed
if st.session_state.analyzed and st.session_state.output_frames:
    output_frames = st.session_state.output_frames
    head_outside_frames = st.session_state.head_outside_frames
    fps = st.session_state.fps
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总帧数", len(output_frames))
    with col2:
        outside_count = sum(head_outside_frames)
        st.metric("越界帧数", outside_count)
    with col3:
        pct = (outside_count / len(output_frames) * 100) if output_frames else 0
        st.metric("越界百分比", f"{pct:.1f}%")
    
    st.header("📹 播放分析视频")
    st.markdown("🟢绿圈=头部正常 | 🔴红圈=头部越界 | 💛黄点=头部位置 | 🟩绿线=脊椎")
    
    speed = st.slider("播放速度", 0.5, 2.0, 1.0, key="speed_slider")
    
    if st.button("▶️ 开始播放视频"):
        frame_col = st.empty()
        info_col = st.empty()
        progress_col = st.empty()
        
        for idx in range(len(output_frames)):
            frame_col.image(cv2.cvtColor(output_frames[idx], cv2.COLOR_BGR2RGB), use_container_width=True)
            
            status = "🔴 越界" if head_outside_frames[idx] else "🟢 正常"
            info_col.write(f"第 {idx+1}/{len(output_frames)} 帧 - {status}")
            
            progress_col.progress((idx + 1) / len(output_frames))
            
            time_module.sleep(1.0 / (fps * speed))
        
        st.balloons()
        st.success("✅ 播放完成！")
