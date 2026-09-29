"""从当前 run 的原始简历补齐报告用的基本信息。"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


PROFILE_FIELDS = ("age", "degree", "work_years")


def _as_text(value: object) -> str:
    if value is None or isinstance(value, bool):
        return ""
    return str(value).strip()


def enrich_candidate_profiles(candidates: list[dict], process_dir: str | Path) -> None:
    """按 geek_id 匹配同一 run 的简历；旧结果仅允许唯一姓名回退。

    只填报告展示字段，不参与评分，也不读取跨 run 的 state 数据。
    找不到可靠匹配时保留原值，报告端显示“未提供”。
    """
    profiles: dict[str, dict[str, str]] = {}
    ids_by_name: dict[str, set[str]] = defaultdict(set)

    for path in sorted(Path(process_dir).glob("*_resumes.json")):
        try:
            resumes = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(resumes, list):
            continue
        for resume in resumes:
            if not isinstance(resume, dict):
                continue
            meta = resume.get("_meta") or {}
            if not isinstance(meta, dict):
                continue
            geek_id = _as_text(meta.get("encrypt_geek_id"))
            if not geek_id:
                continue
            name = _as_text(resume.get("name"))
            if name:
                ids_by_name[name].add(geek_id)
            profile = profiles.setdefault(geek_id, {})
            for field in PROFILE_FIELDS:
                value = _as_text(resume.get(field))
                if value and not profile.get(field):
                    profile[field] = value

    for candidate in candidates:
        geek_id = _as_text(candidate.get("geek_id"))
        if not geek_id:
            matches = ids_by_name.get(_as_text(candidate.get("name")), set())
            if len(matches) == 1:
                geek_id = next(iter(matches))
        profile = profiles.get(geek_id)
        if not profile:
            continue
        candidate["geek_id"] = geek_id
        for field in PROFILE_FIELDS:
            if profile.get(field):
                candidate[field] = profile[field]
