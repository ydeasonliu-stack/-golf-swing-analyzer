import os
import json
from datetime import datetime


def _join_benefits(benefits):
    return "; ".join(benefits[:3])


def _build_template(product, audience, benefits, tone, length):
    b1 = benefits[0] if benefits else "提升效率"
    b2 = benefits[1] if len(benefits) > 1 else "操作简单"
    b3 = benefits[2] if len(benefits) > 2 else "高性价比"

    if length == 15:
        return (
            f"[{length}s 营销短片]\n"
            f"钩子(0-2s)：镜头直切忙碌场景，旁白：还在为{b1}苦恼吗？\n"
            f"问题(2-5s)：展示痛点画面与快节奏字幕\n"
            f"解决(5-11s)：展示{product}核心效果，字幕：{b1}；{b2}\n"
            f"CTA(11-15s)：扫码/点击购买，促销信息\n"
            f"风格：{tone}；目标受众：{audience}\n"
        )

    if length == 30:
        return (
            f"[{length}s 营销短片]\n"
            f"开场(0-3s)：主角挫败表情，旁白：每天浪费多少时间在X上？\n"
            f"放大(3-8s)：痛点数据+场景切换\n"
            f"产品(8-16s)：{product}演示，3步展示，字幕：{_join_benefits(benefits)}\n"
            f"社会证明(16-22s)：用户评价/前后对比\n"
            f"CTA(22-30s)：限时优惠+购买路径\n"
            f"风格：{tone}；目标受众：{audience}\n"
        )

    # default to 60s
    return (
        f"[{length}s 营销短片]\n"
        f"开头故事(0-10s)：短篇人物故事引出痛点\n"
        f"痛点(10-20s)：展示后果与情绪冲击\n"
        f"产品(20-35s)：场景化演示，分步展示并强调：{_join_benefits(benefits)}\n"
        f"功能(35-45s)：列出三大卖点：{b1}、{b2}、{b3}\n"
        f"背书(45-53s)：用户/专家短句\n"
        f"强CTA(53-60s)：购买路径+优惠+无忧承诺\n"
        f"风格：{tone}；目标受众：{audience}\n"
    )


def generate_scripts(product_name: str,
                     audience: str,
                     benefits: list,
                     tone: str = "轻快",
                     output_dir: str = "output"):
    """Generate 15s/30s/60s scripts and save them with metadata.

    Returns a dict of generated file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.utcnow().isoformat()
    results = {}
    for length in (15, 30, 60):
        text = _build_template(product_name, audience, benefits, tone, length)
        fname = f"{product_name.replace(' ', '_')}_{length}s.txt"
        path = os.path.join(output_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        meta = {
            "product": product_name,
            "audience": audience,
            "benefits": benefits,
            "tone": tone,
            "length": length,
            "file": fname,
            "generated_at": now,
        }
        meta_path = path + ".meta.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        results[length] = {"text": path, "meta": meta_path}

    # also write an index
    index = {
        "product": product_name,
        "generated": now,
        "outputs": results,
    }
    index_path = os.path.join(output_dir, f"{product_name.replace(' ', '_')}_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    results["index"] = index_path
    return results


if __name__ == "__main__":
    # quick manual test
    sample = generate_scripts("示例产品", "25-40岁上班族", ["省时", "易用", "高性价比"], "轻快", output_dir="./output_sample")
    print("生成完成:", sample)
