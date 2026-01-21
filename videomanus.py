"""Simple runner for the video manus generator.

This script calls the generator module to produce 15/30/60s scripts
and writes them to `./output_videomanus` when executed.
"""

from video_manus_generator.generator import generate_scripts


def main():
	product = "示例产品-自动化"
	audience = "25-40岁上班族"
	benefits = ["省时", "操作简单", "高性价比"]
	out = "./output_videomanus"
	res = generate_scripts(product, audience, benefits, tone="轻快", output_dir=out)
	print("生成完成，输出：")
	for k, v in res.items():
		print(k, ":", v)


if __name__ == "__main__":
	main()

