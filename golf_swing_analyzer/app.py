"""Streamlit web interface for golf swing analyzer - continuous playback."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import cv2
import numpy as np
import tempfile
import imageio
import time
from golf_swing_analyzer.visualizer import process_video_frame


def main():
    st.set_page_config(page_title="Golf Swing Analyzer", layout="wide")
    st.title("⛳ Golf Swing Head Movement Analyzer")
    st.markdown("标记首帧关键点 → 自动分析全视频 → 连续播放结果")
    
    # Initialize session state
    if 'current_upload' not in st.session_state:
        st.session_state.current_upload = None
    
    # Sidebar settings
    with st.sidebar:
        st.header("⚙️ Settings")
        head_circle_radius = st.slider("Head Circle Radius", 30, 150, 60)
    
    # File upload
    uploaded_file = st.file_uploader("上传视频", type=["mp4", "avi", "mov", "mkv"])
    
    # Check if new file uploaded
    if uploaded_file is None:
        st.info("请上传一个视频文件")
        return
    
    # Clear cache on new file
    if uploaded_file.name != st.session_state.current_upload:
        if 'video_data' in st.session_state:
            del st.session_state['video_data']
        if 'output_frames' in st.session_state:
            del st.session_state['output_frames']
        if 'head_outside_frames' in st.session_state:
            del st.session_state['head_outside_frames']
        st.session_state.current_upload = uploaded_file.name
    
    # Save uploaded file temporarily
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "input.mp4")
        with open(input_path, 'wb') as f:
            f.write(uploaded_file.read())
        
        # Read video info
        cap = cv2.VideoCapture(input_path)
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
            return
        
        # Mark keypoints
        st.header("第1步: 标记首帧关键点")
        col1, col2 = st.columns(2)
        
        with col1:
            st.image(cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        with col2:
            st.markdown("**输入坐标 (像素)**")
            head_x = st.number_input("头部 X", 0, width, width//2, key="head_x")
            head_y = st.number_input("头部 Y", 0, height, height//3, key="head_y")
            shoulder_x = st.number_input("肩膀 X", 0, width, width//2, key="shoulder_x")
            shoulder_y = st.number_input("肩膀 Y", 0, height, height//2, key="shoulder_y")
            hip_x = st.number_input("臀部 X", 0, width, width//2, key="hip_x")
            hip_y = st.number_input("臀部 Y", 0, height, 2*height//3, key="hip_y")
        
        # Preview marks
        preview = first_frame.copy()
        cv2.circle(preview, (int(head_x), int(head_y)), 12, (0, 255, 255), -1)
        cv2.circle(preview, (int(shoulder_x), int(shoulder_y)), 8, (0, 255, 0), 2)
        cv2.circle(preview, (int(hip_x), int(hip_y)), 8, (255, 0, 0), 2)
        cv2.line(preview, (int(shoulder_x), int(shoulder_y)), (int(hip_x), int(hip_y)), (0, 255, 0), 2)
        
        st.markdown("**标记预览**")
        st.image(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB), use_container_width=True)
        
        # Analysis button
        if st.button("▶️ 开始分析全视频", key="analyze_btn"):
            # Process all frames
            with st.spinner("处理中..."):
                cap = cv2.VideoCapture(input_path)
                output_frames = []
                head_outside_frames = []
                
                head_initial = (int(head_x), int(head_y))
                spine_line = ((int(shoulder_x), int(shoulder_y)), (int(hip_x), int(hip_y)))
                head_circle = (head_initial, head_circle_radius)
                current_head_pos = head_initial
                
                progress_bar = st.progress(0)
                
                frame_idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Head tracking
                    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                    lower = np.array([0, 20, 70])
                    upper = np.array([20, 255, 255])
                    mask = cv2.inRange(hsv, lower, upper)
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                    
                    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        candidates = []
                        for c in contours:
                            x, y, w, h = cv2.boundingRect(c)
                            cx, cy = x + w//2, y + h//2
                            d = np.sqrt((cx - current_head_pos[0])**2 + (cy - current_head_pos[1])**2)
                            if d < 200:
                                candidates.append((d, (cx, cy)))
                        if candidates:
                            current_head_pos = sorted(candidates)[0][1]
                    
                    # Check if head outside circle
                    dist = np.sqrt((current_head_pos[0] - head_circle[0][0])**2 + 
                                 (current_head_pos[1] - head_circle[0][1])**2)
                    head_outside = dist > head_circle[1]
                    head_outside_frames.append(head_outside)
                    
                    # Draw annotations
                    annotated = process_video_frame(frame, spine_line, head_circle, 
                                                   current_head_pos, head_outside)
                    output_frames.append(annotated)
                    
                    frame_idx += 1
                    progress_bar.progress(min(frame_idx / total_frames, 1.0))
                
                cap.release()
                progress_bar.empty()
            
            # Store results
            st.session_state.output_frames = output_frames
            st.session_state.head_outside_frames = head_outside_frames
            st.success("✅ 分析完成")
        
        # Display results if available
        if 'output_frames' in st.session_state:
            output_frames = st.session_state.output_frames
            head_outside_frames = st.session_state.head_outside_frames
            
            # Results metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("总帧数", len(output_frames))
            with col2:
                outside_count = sum(head_outside_frames)
                st.metric("越界帧数", outside_count)
            with col3:
                pct = (outside_count / len(output_frames) * 100) if output_frames else 0
                st.metric("越界百分比", f"{pct:.1f}%")
            
            # Video playback section
            st.header("📹 分析视频")
            col_play, col_ctrl = st.columns([3, 1])
            
            with col_play:
                # Slideshow
                frame_display = st.empty()
                
                with col_ctrl:
                    st.subheader("控制")
                    speed = st.slider("速度", 0.5, 2.0, 1.0, key="playback_speed")
                    is_auto = st.checkbox("自动播放", True, key="auto_play_mode")
                
                if is_auto:
                    for frame in output_frames:
                        frame_display.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), use_container_width=True)
                        time.sleep(1.0 / (fps * speed))
                else:
                    selected_idx = st.slider("帧号", 0, len(output_frames) - 1, 0, key="frame_selector")
                    frame_display.image(cv2.cvtColor(output_frames[selected_idx], cv2.COLOR_BGR2RGB), use_container_width=True)
            
            # Frame inspection
            st.header("🔍 逐帧查看")
            inspect_idx = st.slider("选择帧", 0, len(output_frames) - 1, 0, key="inspect_slider")
            
            col_frame, col_status = st.columns([2, 1])
            with col_frame:
                st.image(cv2.cvtColor(output_frames[inspect_idx], cv2.COLOR_BGR2RGB), use_container_width=True)
            with col_status:
                status = "❌ 头部越界" if head_outside_frames[inspect_idx] else "✅ 头部在圆圈内"
                st.write(f"**第 {inspect_idx + 1} 帧**\n{status}")


if __name__ == "__main__":
    main()
