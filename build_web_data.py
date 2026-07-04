"""
AI事例100本ノックのJSON → cases.json, filters.json, stats.json 変換スクリプト。
単体実行では入力JSONを必ず明示する。四半期マージは
generate_2026q2_assets.py から transform_cases() を呼び出して行う。
"""
import argparse
import json
import re
from pathlib import Path

DATA_DIR = (
    Path(__file__).parent.parent.parent
    / "社内AI推進"
    / "AI事例100本ノック"
    / "ソースデータ"
)
OUTPUT_DIR = Path(__file__).parent / "data"

# ── フェーズ順序（建築業務の流れ） ──
PHASE_ORDER = [
    "営業・追客", "集客・広報", "設計・デザイン", "積算・見積",
    "施工・現場", "引渡・アフター", "契約・ローン", "経営・戦略",
    "経理・財務", "組織・総務・人事", "開発・IT", "その他",
]

# ── 削減時間の順序と中央値（分） ──
TIME_SAVED_ORDER = [
    ("1〜5分", 3),
    ("5〜15分", 10),
    ("15〜30分", 22.5),
    ("30分〜1時間", 45),
    ("1〜3時間", 120),
    ("3時間以上", 240),
    ("時間削減ではなく品質向上", 0),
    ("測定できない・不明", 0),
]

# ── 頻度の年間回数中央値 ──
FREQ_MAP = {
    "1日に複数回（年間500回以上）": 625,
    "毎日（年間約250回）": 250,
    "週に数回（年間100〜200回）": 150,
    "週1回程度（年間約50回）": 50,
    "月に数回（年間10〜30回）": 20,
    "月1回以下（年間10回未満）": 5,
    "一度きり・不定期": 1,
}

# ── 目的の正規化（画像・動画 → 画像・動画・スライド に統合） ──
PURPOSE_NORMALIZE = {
    "画像・動画": "画像・動画・スライド",
    "技術・Excel": "技術・表計算ファイル",
    "調査・確認": "調査・検索",
    "開発・ツール作成": "技術・開発",
}

# ── 部署名の一般化（社内名 → 一般名） ──
DEPT_NORMALIZE = {
    "アドバイザー課": "営業",
    "PG｜アドバイザー課": "営業",
    "自社ブランド｜アドバイザー課": "営業",
    "マーケティング課": "マーケティング",
    "建設課": "施工管理",
    "設計課（設計）": "設計",
    "設計課（スタイリスト）": "インテリア",
    "経営戦略室": "経営企画",
    "不動産課": "不動産",
    "業務管理課": "業務管理",
    "組織人事課": "人事・総務",
    "建設技術統括部": "技術統括",
}


def extract_bracket(text: str) -> str:
    m = re.match(r"【(.+?)】", text)
    return m.group(1) if m else text


def normalize_tools(tool_str: str) -> list[str]:
    tools = []
    seen = set()
    for tool in (t.strip() for t in tool_str.split(",") if t.strip()):
        key = tool.lower()
        if key in seen:
            continue
        seen.add(key)
        tools.append(tool)
    return tools


def build_search_index(case: dict) -> str:
    fields = [
        case.get("title", ""),
        case.get("toolsDisplay", ""),
        case.get("phaseDisplay", ""),
        case.get("purposeDisplay", ""),
        case.get("department", ""),
        case.get("problem", ""),
        case.get("solution", ""),
        case.get("result", ""),
        case.get("voice", ""),
    ]
    text = " ".join(fields).lower()
    text = re.sub(r"[【】「」『』（）()\[\]]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def transform_cases(raw_data: list) -> list[dict]:
    cases = []
    for i, item in enumerate(raw_data, 1):
        c = item["case"]
        r = item["rewritten"]

        phase_raw = extract_bracket(c["phase"])
        purpose_raw = extract_bracket(c["purpose"])
        purpose_normalized = PURPOSE_NORMALIZE.get(purpose_raw, purpose_raw)
        dept_raw = c.get("department", "")
        dept_normalized = DEPT_NORMALIZE.get(dept_raw, dept_raw)

        ts_order = next(
            (idx for idx, (label, _) in enumerate(TIME_SAVED_ORDER) if label == c["time_saved"]),
            99,
        )

        case_obj = {
            "id": i,
            "rank": c.get("rank", 0),
            "title": c.get("title", ""),
            "tools": normalize_tools(c.get("tool", "")),
            "toolsDisplay": c.get("tool", ""),
            "phaseDisplay": phase_raw,
            "purposeDisplay": purpose_normalized,
            "department": dept_normalized,
            "timeSavedDisplay": c.get("time_saved", ""),
            "timeSavedOrder": ts_order,
            "frequency": c.get("frequency", ""),
            "score": c.get("score", 0),
            "problem": r.get("problem_main", ""),
            "problemSub": r.get("problem_sub", ""),
            "solution": r.get("solution_main", ""),
            "solutionSub": r.get("solution_sub", ""),
            "result": r.get("result_main", ""),
            "resultSub": r.get("result_sub", ""),
            "voice": r.get("voice", ""),
            "promptFull": item.get("prompt_full", ""),
            "promptSource": item.get("prompt_source", item.get("promptSource", "original")),
            "hasPrompt": len(item.get("prompt_full", "")) >= 50,
        }
        case_obj["_searchIndex"] = build_search_index(case_obj)
        cases.append(case_obj)

    # フェーズ順ソート
    phase_idx = {p: i for i, p in enumerate(PHASE_ORDER)}
    cases.sort(key=lambda x: (phase_idx.get(x["phaseDisplay"], 99), -1 * (x["score"] or 0)))

    # id を並び順で振り直し
    for i, case in enumerate(cases, 1):
        case["id"] = i

    return cases


def build_filters(cases: list[dict]) -> dict:
    def count_by(cases, key_fn):
        counts = {}
        for c in cases:
            vals = key_fn(c)
            if isinstance(vals, list):
                for v in vals:
                    counts[v] = counts.get(v, 0) + 1
            else:
                counts[vals] = counts.get(vals, 0) + 1
        return counts

    tool_counts = count_by(cases, lambda c: c["tools"])
    phase_counts = count_by(cases, lambda c: c["phaseDisplay"])
    purpose_counts = count_by(cases, lambda c: c["purposeDisplay"])
    dept_counts = count_by(cases, lambda c: c["department"])
    ts_counts = count_by(cases, lambda c: c["timeSavedDisplay"])

    def to_options(counts, order=None):
        items = [{"label": k, "count": v} for k, v in counts.items()]
        if order:
            idx = {name: i for i, name in enumerate(order)}
            items.sort(key=lambda x: idx.get(x["label"], 99))
        else:
            items.sort(key=lambda x: -x["count"])
        return items

    return {
        "tools": to_options(tool_counts),
        "phases": to_options(phase_counts, PHASE_ORDER),
        "purposes": to_options(purpose_counts),
        "departments": to_options(dept_counts),
        "timeSaved": to_options(ts_counts, [t[0] for t in TIME_SAVED_ORDER]),
    }


def build_stats(cases: list[dict]) -> dict:
    ts_mid = {label: mid for label, mid in TIME_SAVED_ORDER}

    total_hours = 0
    for c in cases:
        mid = ts_mid.get(c["timeSavedDisplay"], 0)
        freq = FREQ_MAP.get(c["frequency"], 1)
        total_hours += mid * freq / 60

    filters = build_filters(cases)

    return {
        "totalCases": len(cases),
        "totalDepartments": len(filters["departments"]),
        "totalTools": len(filters["tools"]),
        "totalPhases": len(filters["phases"]),
        "estimatedAnnualHoursSaved": round(total_hours),
        "byTool": filters["tools"],
        "byDepartment": filters["departments"],
        "byPhase": filters["phases"],
        "byPurpose": filters["purposes"],
        "byTimeSaved": filters["timeSaved"],
    }


def main():
    parser = argparse.ArgumentParser(description="AIラボ用Webデータ生成")
    parser.add_argument("--input", required=True, help="変換元JSON（rewritten_100系）")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_path = Path(args.input)
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    cases = transform_cases(raw_data)
    existing_cases_path = OUTPUT_DIR / "cases.json"
    if existing_cases_path.exists():
        existing_count = len(json.loads(existing_cases_path.read_text(encoding="utf-8")))
        if len(cases) < existing_count:
            raise RuntimeError(
                f"既存cases.json({existing_count}件)より入力結果({len(cases)}件)が少ないため中断しました。"
                "四半期追加は generate_2026q2_assets.py の --lab-dir 付き実行で行ってください。"
            )
    filters = build_filters(cases)
    stats = build_stats(cases)

    with open(OUTPUT_DIR / "cases.json", "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_DIR / "filters.json", "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_DIR / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(cases)} cases")
    print(f"  Tools: {len(filters['tools'])}")
    print(f"  Phases: {len(filters['phases'])}")
    print(f"  Departments: {len(filters['departments'])}")
    print(f"  Est. annual hours saved: {stats['estimatedAnnualHoursSaved']}h")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
