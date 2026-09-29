# -*- coding: utf-8 -*-
"""school_tier.lookup 的单测

覆盖目标：
  1. 精确匹配各档（C9 / 985 / 211 / 双一流 / 一本公办 / 二本公办 / 民办独立学院）
  2. 缺失学校 → score=None
  3. 模糊匹配（输入是表内校名的子串 / 父串）
  4. 模糊匹配必须「最长优先」——避免独立学院被母体本部校名截胡
     （这是 score_resumes.validate_score 行为正确性的前提）
  5. 返回字典的 schema 稳定（防止后续重构破坏下游）
"""
import os
import sys

# 把 scripts/ 目录加入 path，让 import 路径和真实运行环境一致
_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.join(_HERE, "..", "resume-screener", "scripts")
sys.path.insert(0, os.path.abspath(_SCRIPTS))

import pytest  # noqa: E402

from school_tier import lookup, batch_lookup, popular_overseas_schools  # noqa: E402


# ============================================================
# 1. 精确匹配：每一档至少 1 个
# ============================================================

@pytest.mark.parametrize("school, expected_tier, expected_score", [
    ("清华大学",         "C9",         100),
    ("北京大学",         "C9",         100),
    ("浙江大学",         "C9",         100),
    ("同济大学",         "985",        92),
    ("厦门大学",         "985",        92),
    ("江南大学",         "211",        85),
    ("合肥工业大学",     "211",        85),
    ("南方科技大学",     "双一流",     77),
    ("深圳大学",         "一本公办",   71),
    ("辽宁工业大学",     "二本公办",   62),
    ("燕京理工学院",     "民办/独立学院", 53),
])
def test_lookup_exact_match_all_tiers(school, expected_tier, expected_score):
    """精确匹配各档学校，返回正确 tier + 分数"""
    r = lookup(school)
    assert r["score"] == expected_score, f"{school} 期望分数 {expected_score}, 实际 {r['score']}"
    assert r["tier"] == expected_tier, f"{school} 期望 tier {expected_tier}, 实际 {r['tier']}"
    assert r["matched"] == school
    assert r["fuzzy"] is False


# ============================================================
# 2. 缺失学校
# ============================================================

def test_lookup_missing_school_returns_none_score():
    r = lookup("不存在的野鸡大学 XYZ")
    assert r["score"] is None
    assert r["tier"] == "未知"
    assert r["matched"] is None
    assert r["fuzzy"] is False


def test_lookup_empty_string_returns_none_score():
    r = lookup("")
    assert r["score"] is None
    assert r["tier"] == "未知"


# ============================================================
# 3. 模糊匹配
# ============================================================

def test_lookup_fuzzy_input_is_substring_of_table():
    """输入是表内校名的子串（如 "江南" 匹配 "江南大学"）"""
    r = lookup("江南")
    assert r["fuzzy"] is True
    assert r["score"] == 85
    assert r["tier"] == "211"
    assert r["matched"] == "江南大学"


def test_lookup_fuzzy_table_school_is_substring_of_input():
    """表内校名是输入的子串"""
    r = lookup("江南大学设计学院")  # 假设"江南大学"是子串
    assert r["fuzzy"] is True
    assert r["matched"] == "江南大学"


# ============================================================
# 4. 模糊匹配「最长优先」——这是核心安全语义
# ============================================================

def test_lookup_fuzzy_prefers_longest_match():
    """独立学院必须匹配到独立学院条目，不能被较短的母体本部「截胡」

    场景：「杭州电子科技大学信息工程学院」
      - 母体「杭州电子科技大学」= 一本公办 (71)
      - 独立学院「杭州电子科技大学信息工程学院」= 民办/独立学院 (53)
    必须返回 53。
    """
    r = lookup("杭州电子科技大学信息工程学院")
    assert r["score"] == 53, (
        f"独立学院被母体本部截胡了！"
        f"实际分数 {r['score']} (tier={r['tier']}, matched={r['matched']})"
    )
    assert r["tier"] == "民办/独立学院"
    assert r["matched"] == "杭州电子科技大学信息工程学院"


def test_lookup_fuzzy_jiangsu_normal_university_not_misrouted():
    """江苏师范大学应匹配到自己（71），不应被「南京师范大学」等干扰。

    类似的潜在风险：精确或近似匹配但更长的条目应优先。
    """
    r = lookup("江苏师范大学")
    assert r["score"] is not None
    # 不管是精确还是模糊，只要 score=71 就是对的
    assert r["score"] == 71


# ============================================================
# 5. 返回值 schema 稳定
# ============================================================

def test_lookup_return_schema():
    r = lookup("清华大学")
    assert set(r.keys()) == {
        "school", "tier", "score", "matched", "fuzzy", "scope", "basis",
        "rankings", "popular", "region",
    }


def test_batch_lookup_returns_list_in_order():
    schools = ["清华大学", "江南大学", "不存在的XYZ"]
    results = batch_lookup(schools)
    assert len(results) == 3
    assert [r["score"] for r in results] == [100, 85, None]


# ============================================================
# 6. 海外热门院校：明确别名 + 官方排名依据
# ============================================================

@pytest.mark.parametrize("school, expected_score, expected_matched", [
    ("康奈尔大学", 100, "Cornell University"),
    ("cornell university", 100, "Cornell University"),
    ("澳门大学", 85, "University of Macau"),
    ("Universidade de Macau", 85, "University of Macau"),
    ("澳门科技大学", 77, "Macau University of Science and Technology"),
    ("DIPLOMA Fachhochschule Nordhessen Deutschland", 53, "DIPLOMA Hochschule"),
])
def test_lookup_overseas_aliases(school, expected_score, expected_matched):
    r = lookup(school)
    assert r["score"] == expected_score
    assert r["matched"] == expected_matched
    assert r["scope"] == "overseas"
    assert r["basis"]


def test_lookup_overseas_normalizes_width_case_spaces_and_punctuation():
    a = lookup("  CORNELL   UNIVERSITY  ")
    b = lookup("University of California，Berkeley")
    assert a["score"] == 100
    assert b["score"] == 100


@pytest.mark.parametrize("unsafe", [
    "UM", "University", "大学", "Cornell College", "DIPLOMA",
])
def test_lookup_does_not_guess_unsafe_short_or_similar_names(unsafe):
    r = lookup(unsafe)
    assert r["score"] is None
    assert r["scope"] == "unknown"


def test_diploma_is_internal_exact_entry_not_public_popular_school():
    r = lookup("DIPLOMA Hochschule")
    assert r["score"] == 53
    assert r["popular"] is False
    assert all(s["canonical"] != "DIPLOMA Hochschule" for s in popular_overseas_schools())


def test_popular_overseas_table_contains_current_ranked_examples():
    names = {s["canonical"] for s in popular_overseas_schools()}
    assert "Cornell University" in names
    assert "University of Macau" in names
    assert len(names) >= 90


# ============================================================
# 7. 国内基准项纠正：海外对标所依赖的档位不能静默降档
# ============================================================

@pytest.mark.parametrize("school, expected_score", [
    ("湖南大学", 92),
    ("电子科技大学", 92),
    ("长安大学", 85),
    ("南京师范大学", 85),
    ("石河子大学", 85),
])
def test_domestic_reference_tiers_are_not_overwritten(school, expected_score):
    assert lookup(school)["score"] == expected_score
