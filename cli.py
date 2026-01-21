#!/usr/bin/env python3
"""Simple CLI to generate marketing short-video scripts."""
import argparse
import os
from video_manus_generator import generator
from video_manus_generator import exporter


def _parse_args():
    p = argparse.ArgumentParser(description="生成营销短视频脚本（15/30/60s）")
    p.add_argument("--product", required=False, help="产品名")
    p.add_argument("--audience", required=False, help="目标受众")
    p.add_argument("--benefits", required=False, help="核心卖点，逗号分隔")
    p.add_argument("--tone", default="轻快", help="风格/语气")
        p.add_argument("--out", default="output", help="输出目录")
        p.add_argument("--excel", action="store_true", help="同时导出为 Excel 文件（在输出目录内）")
    p.add_argument("--sample", action="store_true", help="运行示例生成")
    #!/usr/bin/env python3
    """Simple CLI to generate marketing short-video scripts."""
    import argparse
    import os
    from video_manus_generator import generator
    from video_manus_generator import exporter


    def _parse_args():
        p = argparse.ArgumentParser(description="生成营销短视频脚本（15/30/60s）")
        p.add_argument("--product", required=False, help="产品名")
        p.add_argument("--audience", required=False, help="目标受众")
        p.add_argument("--benefits", required=False, help="核心卖点，逗号分隔")
        p.add_argument("--tone", default="轻快", help="风格/语气")
        p.add_argument("--out", default="output", help="输出目录")
        p.add_argument("--excel", action="store_true", help="同时导出为 Excel 文件（在输出目录内）")
        p.add_argument("--sample", action="store_true", help="运行示例生成")
        return p.parse_args()


    def main():
        args = _parse_args()
        if args.sample:
            product = "示例产品"
            audience = "25-40岁上班族"
            benefits = ["省时", "易用", "高性价比"]
        else:
            if not args.product or not args.audience or not args.benefits:
                print("请提供 --product --audience --benefits，或使用 --sample 查看示例。")
                return
            product = args.product
            audience = args.audience
            benefits = [b.strip() for b in args.benefits.split(",") if b.strip()]

        out_dir = args.out
        os.makedirs(out_dir, exist_ok=True)
        res = generator.generate_scripts(product, audience, benefits, tone=args.tone, output_dir=out_dir)
        print("生成文件：")
        for k, v in res.items():
            print(k, ":", v)

        if args.excel:
            try:
                idx = res.get('index')
                if not idx:
                    # fallback: try export_folder
                    excel = exporter.export_folder(out_dir)
                else:
                    excel = exporter.export_index_to_excel(idx, excel_path=os.path.join(out_dir, f"{product.replace(' ', '_')}_scripts.xlsx"))
                print("导出 Excel：", excel)
            except Exception as e:
                print("导出 Excel 失败：", e)


    if __name__ == "__main__":
        main()
