# video_manus_generator

轻量 Python CLI，用于自动生成 15/30/60 秒的营销短视频脚本与拍摄指引元数据。

使用方法：

示例运行：

```bash
python3 cli.py --sample
```

自定义运行：

```bash
python3 cli.py --product "我的产品" --audience "25-40岁上班族" --benefits "省时, 操作简单, 高性价比" --out ./outdir

生成并导出 Excel：

```bash
python3 cli.py --sample --out ./outdir --excel
```
```

输出会生成文本脚本与对应的 `*.meta.json`，以及一个 `index.json`。
