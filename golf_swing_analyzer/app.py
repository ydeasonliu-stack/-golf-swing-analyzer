"""Streamlit web interface for golf swing analyzer - continuous playback."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import cv2
import numpy as np
import tempfile
from golf_swing_analyzer.visualizer import process_video_frame


def main():
    st.set_page_config(page_title="Golf Swing Analyzer", layout="wide")
    st.title("⛳ Golf Swing Head Movement Analyzer")
    st.markdown("标记首帧关键点 → 自动分析全视频 → 连续播放结果")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        head_circle_radius = st.slider("Head Circle Radius", 30, 150, 60)
    
    # Upload
    uploaded_file = st.file_uploader("上传视频", type=["mp4", "avi", "mov", "mkv"])
    
    if uploaded_file:
        with tempfile.TemporaryDirectory() as tmpdir:
            video_path = os.path.join(tmpdir, "input.mp4")
            with open(video_path, 'wb') as f:
                f.write(uploaded_file.read())
            
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            st.info(f"📹 {width}x{height} @ {fps:.1f}fps, 共 {total_frames} 帧")
            
            # Get first frame
            ret, first_frame = cap.read()
            cap.release()
            
            if not ret:
                st.error("Failed to read video")
                return
            
            # Mark keypoints
            st.header("第1步: 标记首帧关键点")
            col1, col2 = st.columns(2)
            
            with col1:
                st.image(cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB), width=350)
            
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
            st.image(cv2.cvtColor(preview, cv2.COLOR_BGR2RGB), width=350)
            
            if st.button("▶️ 开始分析全视频"):
                # Process all frames
                with st.spinner("处理中..."):
                    cap = cv2.VideoCapture(video_path)
                    output_frames = []
                    head_outside_frames = []
                    
                    head_initial = (int(head_x), int(head_y))
                    spine_line = ((int(shoulder_x), int(shoulder_y)), (int(hip_x), int(hip_y)))
                    head_circle = (head_initial, head_circle_radius)
                    current_head_pos = head_initial
                    
                    progress_bar = st.progress(0)
                    frame_count = 0
                    
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
                            valid = []
                            for c in contours:
                                x, y, w, h = cv2.boundingRect(c)
                                cx, cy = x + w//2, y + h//2
                                d = np.sqrt((cx - current_head_pos[0])**2 + (cy - current_head_pos[1])**2)
                                if d < 200:
                                    valid.append((d, (cx, cy)))
                            if valid:
                                current_head_pos = sorted(valid)[0][1]
                        
                        # Check outside
                        circle_center, radius = head_circle
                        dist = np.sqrt((current_head_pos[0] - circle_center[0])**2 + 
                                     (current_head_pos[1] - circle_center[1])**2)
                        head_outside = dist > radius
                        head_outside_frames.append(head_outside)
                        
                        # Draw
                        annotated = process_video_frame(frame, spine_line, head_circle, 
                                                       current_head_pos, head_outside)
                        output_frames.append(annotated)
                        
                        frame_count += 1
                        progress_bar.progress(min(frame_count / total_frames, 1.0))
                    
                    cap.release()
                    progress_bar.empty()
                
                # Results
                st.success("✅ 分析完成")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("总帧数", len(output_frames))
                with col2:
                    outside_count = sum(head_outside_frames)
                    st.metric("头部越界帧数", outside_count)
                with col3:
                    pct = (outside_count / len(output_frames) * 100) if output_frames else 0
                    st.metric("越界百分比", f"{pct:.1f}%")
                
                # Save and play video - write to persistent temp file
                output_path = os.path.join(tmpdir, "output.mp4")
                try:
                    # Use MJPEG codec for better compatibility
                    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                    if not out.isOpened():
                        raise ValueError("VideoWriter failed to open")
                    
                    for frame in output_frames:
                        success = out.write(frame)
                        if not success:
                            st.warning("⚠️ 部分帧写入失败")
                    out.release()
                    
                    # Read video before tmpdir cleanup
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        with open(output_path, 'rb') as f:
                            video_data = f.read()
                        st.session_state.video_data = video_data
                    else:
                        st.error("❌ 视频文件创建失败或为空")
                        return
                except Exception as e:
                    st.error(f"❌ 视频编码错误: {e}")
                    return
                
                # Store outputs
                st.session_state.output_frames = output_frames
                st.session_state.head_outside_frames = head_outside_frames
        
        # Display video and results outside tmpdir context
        if 'video_data' in st.session_state:
            st.header("📹 分析视频")
            st.video(st.session_state.video_data)
            
            # Frame slider (optional)
            st.header("🔍 逐帧查看")
            frame_idx = st.slider("选择帧", 0, len(st.session_state.output_frames) - 1, 0)
            col1, col2 = st.columns(2)
            with col1:
                st.image(cv2.cvtColor(st.session_state.output_frames[frame_idx], cv2.COLOR_BGR2RGB), width=300)
            with col2:
                status = "❌ 头部越界" if st.session_state.head_outside_frames[frame_idx] else "✅ 头部在圆圈内"
                st.write(f"**第 {frame_idx + 1} 帧**\n{status}")


if __name__ == "__main__":
    main()
