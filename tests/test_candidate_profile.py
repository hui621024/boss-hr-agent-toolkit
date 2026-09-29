"""候选人基本信息必须按当前 run 的稳定 ID 匹配。"""

import json

from shared.candidate_profile import enrich_candidate_profiles


def test_profile_enrichment_does_not_guess_duplicate_names(tmp_path):
    process_dir = tmp_path / "run" / "process"
    process_dir.mkdir(parents=True)
    (process_dir / "new_resumes.json").write_text(json.dumps([
        {"name": "牛人", "age": "27岁", "degree": "本科", "work_years": "3年",
         "_meta": {"encrypt_geek_id": "gid_1"}},
        {"name": "牛人", "age": "34岁", "degree": "硕士", "work_years": "8年",
         "_meta": {"encrypt_geek_id": "gid_2"}},
    ], ensure_ascii=False), encoding="utf-8")
    candidates = [
        {"name": "牛人", "geek_id": "gid_2"},
        {"name": "牛人"},
        {"name": "牛人", "geek_id": "not_in_this_run"},
    ]

    enrich_candidate_profiles(candidates, process_dir)

    assert candidates[0]["age"] == "34岁"
    assert candidates[0]["degree"] == "硕士"
    assert candidates[0]["work_years"] == "8年"
    assert "age" not in candidates[1]
    assert "age" not in candidates[2]
