#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ip-make-pipeline 质检脚本
对标「质检 P0~P2 门槛 + C1~C12 子检查码」，对分镜表做机械检查。

输入：分镜表 JSON（见 tools/README.md 的 schema）
输出：分级质检报告（P0 必过 / P1 建议 / P2 可选），退出码 0=通过 P0，非 0=有 P0 错误。

用法：
    python validate.py storyboard.json
    python validate.py storyboard.json --json    # 输出 JSON 报告
"""

import json
import sys
import re
from collections import defaultdict

# 语速范围（按赛道）：中文=字/秒，英文=词/秒
RATE_MIN = 4.5
RATE_MAX = 6.5
# 英文语速（词/秒）
RATE_EN_MIN = 2.0
RATE_EN_MAX = 2.8

# 景别词典（8 级，从远到近，中英双语）
SHOT_SIZES = ["大远景", "远景", "全景", "中景", "中近景", "近景", "特写", "大特写"]

# 景别英文别名 → 中文名（用于 C07 景别跳变校验，映射到最近的 8 级）
SHOT_SIZE_EN = {
    "extreme wide shot": "大远景", "extreme long shot": "大远景",
    "wide shot": "远景", "long shot": "远景",
    "full shot": "全景",
    "medium shot": "中景",
    "medium close-up": "中近景",
    "close-up": "特写", "big close-up": "大特写",
    "extreme close-up": "大特写",
}

# 运镜词典（中英双语，海外剧用英文别名）
CAMERA_MOVES = ["固定", "推", "拉", "摇", "移", "跟", "升降", "手持", "快切", "慢镜", "航拍",
                "static", "push-in", "pull-out", "pan", "tilt", "tracking", "crane",
                "handheld", "quick-cut", "slow motion", "aerial"]

# 构图词典（中英双语）
COMPOSITIONS = ["对角线纵深", "三分线", "居中", "对称", "过肩", "双人侧拍", "框架构图", "留白", "前景遮挡",
                "diagonal depth", "rule of thirds", "centered", "symmetry", "over-the-shoulder",
                "two-shot side", "frame within frame", "negative space", "foreground occlusion"]

# 资产编号前缀
ASSET_PREFIX = ("P", "S", "D", "V")


def check_id_continuous(shots):
    """C01: 分镜号连续无跳号"""
    ids = [s.get("shot_id") for s in shots]
    errors = []
    for i, sid in enumerate(ids):
        if sid is None:
            errors.append((i, "缺分镜号"))
        elif i > 0 and ids[i - 1] is not None and sid != ids[i - 1] + 1:
            errors.append((i, f"分镜号跳号：{ids[i-1]} → {sid}"))
    return errors


def check_fields_complete(shots, required_fields):
    """C02: 每镜字段齐全

    - 硬字段（shot_id/duration/description/camera/composition/shot_size）必须非空
    - 软字段（characters/dialogue/props/scene）允许空字符串（空镜/无台词是合法的）
    """
    HARD_FIELDS = {"shot_id", "duration", "description", "camera", "composition", "shot_size"}
    errors = []
    for i, s in enumerate(shots):
        # 键缺失 → 报错（结构不对）
        missing_key = [f for f in required_fields if f not in s]
        # 硬字段值为空 → 报错
        empty_hard = [f for f in HARD_FIELDS if not s.get(f)]
        if missing_key:
            errors.append((i, f"缺字段键：{', '.join(missing_key)}"))
        elif empty_hard:
            errors.append((i, f"硬字段为空：{', '.join(empty_hard)}"))
    return errors


def check_total_duration(shots, storyboard):
    """C03: 表尾合计行校验

    - Σ每镜时长 = 目标时长（误差 ≤0.5s）
    - 若分镜表提供了 total 字段（合计行），校验其总镜数/总时长与 shots 实际一致
    """
    errors = []
    total = sum(float(s.get("duration", 0)) for s in shots)
    target = storyboard.get("target_duration", total)
    if abs(total - target) > 0.5:
        errors.append((len(shots), f"总时长 {total}s 偏离目标 {target}s"))
    # 合计行校验（storyboard-format.md 要求表尾必有合计行）
    tb = storyboard.get("total")
    if tb is not None:
        if isinstance(tb, dict):
            t_shots = tb.get("shots")
            t_dur = tb.get("duration")
            if t_shots is not None and int(t_shots) != len(shots):
                errors.append((len(shots), f"合计行镜数 {t_shots} ≠ 实际 {len(shots)}"))
            if t_dur is not None and abs(float(t_dur) - total) > 0.5:
                errors.append((len(shots), f"合计行时长 {t_dur}s ≠ 实际 Σ {total}s"))
        else:
            errors.append((len(shots), "合计行 total 字段格式应为 {shots, duration}"))
    return errors


def count_chars(text, language="zh"):
    """统计台词字数/词数（去空白、去标点）

    - 中文（zh）：按「字」数，去标点
    - 英文（en）：按「词」数，空格/标点切分
    """
    if not text:
        return 0
    if language == "en":
        # 英文按词计数：非字母数字字符作为分隔
        words = re.findall(r"[A-Za-z0-9'\-]+", text)
        return len(words)
    text = re.sub(r"[。，、？！；：“”‘’（）\s]", "", text)
    return len(text)


def check_duration_vs_lines(shots, language="zh"):
    """C04: 每镜台词字数/词数 ÷ 语速 ≤ 镜时长"""
    errors = []
    rate_max = RATE_EN_MAX if language == "en" else RATE_MAX
    unit = "词" if language == "en" else "字"
    for i, s in enumerate(shots):
        lines = s.get("dialogue", "") or ""
        n = count_chars(lines, language)
        dur = float(s.get("duration", 0))
        if n == 0:
            continue
        # 用最快语速算最短所需时长
        min_dur = n / rate_max
        if dur < min_dur - 0.1:
            errors.append((i, f"台词 {n} {unit}需 ≥{min_dur:.1f}s，实际 {dur}s 超时"))
    return errors


def check_asset_refs(shots, language="zh"):
    """C05: 人物/场景/道具均用编号

    检查逻辑：字段值非空时，必须含资产编号前缀（P/S/D/V + 两位数字）。
    允许「编号 + 名字」格式（如 P01 梁大 / P01 Lena），但禁止纯裸描述（没编号）。
    """
    errors = []
    # 中文可忽略的标签词（不含编号，但属于合法的空镜/占位说明）
    IGNORE_ZH = ("人物资产", "场景资产", "空镜", "有", "无")
    for i, s in enumerate(shots):
        for field in ("characters", "scene", "props"):
            val = s.get(field, "") or ""
            if not val:
                continue
            # 有编号前缀 → 合法，跳过
            if re.search(r"[PSDV]\d{2}", val):
                continue
            # 无编号前缀：判断是否为「纯标签词」（中文）或纯空白
            if language == "en":
                # 英文：非空且无编号即视为裸描述（英文没有「人物资产」这类标签词约定）
                errors.append((i, f"{field} 未用资产编号：{val}"))
            else:
                # 中文：允许「人物资产」等标签词，其余裸描述报错
                tokens = re.findall(r"[\u4e00-\u9fff]{2,}", val)
                bare = [t for t in tokens if t not in IGNORE_ZH]
                if bare:
                    errors.append((i, f"{field} 未用资产编号：{val}"))
    return errors


def check_face_consistency(shots):
    """C06: 同角色跨镜面部描述一致（防换脸）

    face_anchor 支持两种格式：
    1. 单角色镜： "P01：圆脸、细长眼、黑色短发"
    2. 多角色镜： "P01：…；P02：…"（用分号分隔，按角色 key 提取比对）
    """
    faces = defaultdict(list)
    errors = []
    for i, s in enumerate(shots):
        chars = s.get("characters", "") or ""
        anchor = s.get("face_anchor", "") or ""
        if not anchor:
            continue
        # 拆分多角色锚点：按「；」或「;」拆成 "Pxx：desc" 片段
        parts = re.split(r"[；;]", anchor)
        for part in parts:
            m = re.match(r"\s*(P\d{2})\s*[:：]\s*(.+)$", part)
            if not m:
                continue
            pid, desc = m.group(1), m.group(2).strip()
            if desc:
                faces[pid].append((i, desc))
    for pid, lst in faces.items():
        base = lst[0][1]
        for i, desc in lst[1:]:
            if desc != base:
                errors.append((i, f"{pid} 面部描述与首镜不一致（防换脸）"))
    return errors


def shot_size_index(name):
    name = (name or "").strip()
    # 英文别名归一化：把英文景别换成中文名
    name_norm = SHOT_SIZE_EN.get(name.lower(), name)
    # 处理「大远景→中景」这种变化，取首尾
    parts = re.split(r"[→\-—>]", name_norm)
    return [SHOT_SIZES.index(p) for p in parts if p in SHOT_SIZES]


def check_shot_size_jump(shots):
    """C07: 景别跳变 ≤2 级"""
    errors = []
    prev_idx = None
    for i, s in enumerate(shots):
        idxs = shot_size_index(s.get("shot_size", ""))
        if not idxs:
            continue
        cur = idxs[-1]
        if prev_idx is not None and abs(cur - prev_idx) > 2:
            errors.append((i, f"景别跳变超 2 级：{SHOT_SIZES[prev_idx]} → {SHOT_SIZES[cur]}"))
        prev_idx = cur
    return errors


def check_camera_composition(shots):
    """C08: 运镜/构图取值在词典内"""
    errors = []
    for i, s in enumerate(shots):
        cam = s.get("camera", "") or ""
        # 分割符支持中文顿号/加号/斜杠 + 英文逗号/分号
        for c in re.split(r"[+、/、,，;；]", cam):
            c = c.strip()
            if c and not any(k in c for k in CAMERA_MOVES):
                errors.append((i, f"运镜「{c}」不在词典"))
        comp = s.get("composition", "") or ""
        if comp and not any(k in comp for k in COMPOSITIONS):
            errors.append((i, f"构图「{comp}」不在词典"))
    return errors


def check_action_phases(shots):
    """C09: 武戏关键动作是否拆相位（有 action 标记的镜）"""
    errors = []
    for i, s in enumerate(shots):
        if s.get("is_action") and len(shots) > 0:
            # 检查本镜画面描述是否含相位关键词（中英双语）
            desc = s.get("description", "") or ""
            if not any(k in desc for k in ("预备", "发动", "命中", "反馈", "收势", "结果", "过程",
                                           "wind-up", "strike", "impact", "recoil", "follow-through", "reaction", "recovery")):
                errors.append((i, "武戏关键动作未拆相位"))
    return errors


def check_axis_cross(shots):
    """C10: 越轴检测

    规则（对齐 staging.md 的 180° 轴线锁）：
    - 同一场景内，机位方向（camera_side）不能左右跳变，除非经过中性镜头过渡
    - 换场景（scene 变化）时重置轴线，允许换边
    - neutral_shot=true 或 camera_side 为空，视为中性镜头，可作换轴过渡
    """
    errors = []
    prev_side = None
    prev_scene = None
    for i, s in enumerate(shots):
        scene = s.get("scene", "") or ""
        side = s.get("camera_side", "") or ""
        neutral = s.get("neutral_shot") == True

        # 换场景 → 重置轴线
        if prev_scene is not None and scene != prev_scene:
            prev_side = side  # 新场景首镜定基线，不报越轴
            prev_scene = scene
            continue

        if side:
            if prev_side and side != prev_side and not neutral:
                # 前一镜不是中性镜头才报越轴
                prev_neutral = shots[i-1].get("neutral_shot") == True if i > 0 else False
                if not prev_neutral:
                    errors.append((i, f"疑似越轴：机位从 {prev_side} 切到 {side}，需中性镜头过渡"))
            prev_side = side

        prev_scene = scene
    return errors


# 安全转译词典敏感词（血腥/断肢/重创类，见 references/compliance-translate.md，中英双语）
SENSITIVE_WORDS = ["喷血", "血花", "鲜血", "血流", "砍断", "斩断", "断头", "断肢", "肢解",
                   "毙命", "肉泥", "血泊", "脏器", "脑浆", "断臂", "断腿", "血肉模糊",
                   "blood", "gore", "severed", "decapitat", "dismember", "mutilat",
                   "disembowel", "guts", "brains", "corpse", "amputat"]

# 合规转译词（命中敏感词时提示替换为这些）
SAFE_ALTERNATIVES = "气浪震散 / 火花四溅 / 重创定格 / 光华绽开 / 能量涟漪"


def check_compliance_translate(shots):
    """C11: 安全转译检测——画面描述/台词含血腥断肢类敏感词，建议按合规词典转译"""
    errors = []
    for i, s in enumerate(shots):
        text = (s.get("description", "") or "") + (s.get("dialogue", "") or "")
        for w in SENSITIVE_WORDS:
            if w in text:
                errors.append((i, f"含敏感词「{w}」，建议转译为 {SAFE_ALTERNATIVES}"))
                break  # 每镜只报一次，避免刷屏
    return errors


def check_emotion_peak(shots):
    """C12: 情绪峰值校验——若分镜标注了 tension 字段，校验第 9 节拍（或末段）是否为峰值

    规则（对齐 emotion-curve.md）：
    - 全片有 tension 标注时，找峰值镜
    - 峰值应出现在后段（≥ 70% 位置，接近"第 9 节拍"），且 ≥ 8
    - 若峰值出现在前段/中段，提示"结尾泄气"
    """
    errors = []
    tensions = [(i, float(s.get("tension"))) for i, s in enumerate(shots)
                if s.get("tension") not in (None, "", 0)]
    if len(tensions) < 3:
        return []  # 标注太少，不做峰值校验
    peak_idx, peak_val = max(tensions, key=lambda x: x[1])
    n = len(shots)
    # 峰值应落在后 30% 区间（接近第 9 节拍，12 节拍里的第 9 拍 ≈ 75% 位置）
    if peak_idx < n * 0.7:
        errors.append((peak_idx, f"情绪峰值（tension={peak_val}）出现在前中段，结尾可能泄气，建议把最强反转挪到第 9 节拍附近"))
    elif peak_val < 8:
        errors.append((peak_idx, f"情绪峰值（tension={peak_val}）偏低，建议反杀峰值 ≥ 8"))
    return errors


# 检查码注册表：code -> (level, func)
CHECKS = [
    ("C01", "P0", "分镜号连续", check_id_continuous),
    ("C02", "P0", "字段齐全", check_fields_complete),
    ("C03", "P0", "总时长对齐", check_total_duration),
    ("C04", "P0", "台词时长校验", check_duration_vs_lines),
    ("C05", "P0", "资产编号引用", check_asset_refs),
    ("C06", "P0", "防换脸一致性", check_face_consistency),
    ("C07", "P1", "景别跳变", check_shot_size_jump),
    ("C08", "P1", "运镜构图合规", check_camera_composition),
    ("C09", "P1", "武戏动作拆相位", check_action_phases),
    ("C10", "P1", "越轴检测", check_axis_cross),
    ("C11", "P1", "安全转译检测", check_compliance_translate),
    ("C12", "P2", "情绪峰值校验", check_emotion_peak),
]

REQUIRED_FIELDS = ["shot_id", "duration", "description", "characters", "dialogue",
                   "camera", "composition", "shot_size"]


def run_validate(storyboard):
    """运行所有检查，返回报告"""
    shots = storyboard.get("shots", [])
    language = storyboard.get("language", "zh")  # 赛道语言契约：zh=国内剧，en=海外剧
    report = {"P0": [], "P1": [], "P2": [], "summary": {}}
    for code, level, name, func in CHECKS:
        if code == "C02":
            errs = func(shots, REQUIRED_FIELDS)
        elif code == "C03":
            errs = func(shots, storyboard)
        elif code == "C04":
            errs = func(shots, language)
        elif code == "C05":
            errs = func(shots, language)
        else:
            errs = func(shots)
        if errs:
            for idx, msg in errs:
                # 检查函数用 0-based index 定位，上报时统一转为 1-based shot_id，
                # 避免报告里的镜头号与分镜表对不上（index 0 = shot_id 1）。
                # idx == len(shots) 是 C03 表尾合计行的哨兵，显示为「合计行」。
                if idx == len(shots):
                    shot_label = "合计行"
                elif 0 <= idx < len(shots):
                    shot_label = shots[idx].get("shot_id", idx + 1)
                else:
                    shot_label = idx + 1
                report[level].append({"code": code, "name": name, "shot": shot_label, "msg": msg})
    report["summary"] = {
        "总镜数": len(shots),
        "P0 错误": len(report["P0"]),
        "P1 问题": len(report["P1"]),
        "P2 提示": len(report["P2"]),
        "结论": "❌ 不通过（有 P0 错误）" if report["P0"] else "✅ 通过 P0",
    }
    return report


def main():
    if len(sys.argv) < 2:
        print("用法: python validate.py storyboard.json [--json]")
        sys.exit(2)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        storyboard = json.load(f)
    report = run_validate(storyboard)
    as_json = "--json" in sys.argv
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("=" * 50)
        print("分镜表质检报告")
        print("=" * 50)
        for k, v in report["summary"].items():
            print(f"{k}: {v}")
        for level in ("P0", "P1", "P2"):
            items = report[level]
            if items:
                print(f"\n--- {level} ---")
                for it in items:
                    print(f"  [{it['code']}·{it['name']}] 镜{it['shot']}: {it['msg']}")
    sys.exit(1 if report["P0"] else 0)


if __name__ == "__main__":
    main()
