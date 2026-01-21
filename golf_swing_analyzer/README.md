# Golf Swing Head Movement Analyzer

实时分析高尔夫挥杆过程中的头部运动，检测是否超出预定范围。

## 功能

- **脊柱检测**：自动识别脊柱轴线（绿色线条）
- **头部圆圈**：绘制头部活动范围圆圈（蓝色）
- **越界检测**：判断挥杆过程中头部是否越界（红色警告）
- **实时分析**：逐帧处理并统计结果

## 快速开始

```bash
streamlit run golf_swing_analyzer/app.py
```

然后：
1. 上传高尔夫挥杆视频（MP4/AVI/MOV/MKV）
2. 调整头部圆圈半径（可选）
3. App 自动分析并显示结果

## 输出

- 脊柱线 (绿) + 头部圆圈 (蓝/红) + 头部位置 (黄)
- 越界帧数统计
- 完整分析视频下载
- 逐帧细节展示

## 依赖

- mediaipe: 姿态检测
- opencv-python: 视频处理
- streamlit: Web UI
- numpy: 数值计算
