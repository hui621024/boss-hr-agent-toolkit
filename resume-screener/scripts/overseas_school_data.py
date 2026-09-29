# -*- coding: utf-8 -*-
"""海外及港澳院校的可审计内置数据。

本模块只提供结构化常量，不负责模糊匹配。调用方应先规范空白、大小写和
全/半角标点，再对 ``canonical`` 与 ``aliases`` 做完整字段匹配。这里刻意不
收录 MIT、UM、UCL、USC、HKU 等危险短别名，避免把专业、城市、其他院校
或普通单词误识别为学校。

口径日期：2026-09-29。此日期 THE World University Rankings 2027 尚未发布，
所以交叉核验仍使用 THE 2026；主分档使用已经发布的 QS 2027。
"""

from __future__ import annotations


DATA_AS_OF = "2026-09-29"


# 与现有国内七档分数保持一致。前六档由 QS 2027 总榜名次直接落档；最后
# 一档只适用于经院校官网确认、但未进入 QS/THE/ARWU 总榜的私立本科院校。
OVERSEAS_SCORE_BANDS = (
    {
        "score": 100,
        "tier": "海外世界前30（对标C9）",
        "qs_rank_min": 1,
        "qs_rank_max": 30,
        "rank_status": "ranked",
    },
    {
        "score": 92,
        "tier": "海外世界31-100（对标985）",
        "qs_rank_min": 31,
        "qs_rank_max": 100,
        "rank_status": "ranked",
    },
    {
        "score": 85,
        "tier": "海外世界101-300（对标211）",
        "qs_rank_min": 101,
        "qs_rank_max": 300,
        "rank_status": "ranked",
    },
    {
        "score": 77,
        "tier": "海外世界301-500（对标双一流）",
        "qs_rank_min": 301,
        "qs_rank_max": 500,
        "rank_status": "ranked",
    },
    {
        "score": 71,
        "tier": "海外世界501-800（对标一本公办）",
        "qs_rank_min": 501,
        "qs_rank_max": 800,
        "rank_status": "ranked",
    },
    {
        "score": 62,
        "tier": "海外世界801-1500（对标二本公办）",
        "qs_rank_min": 801,
        "qs_rank_max": 1500,
        "rank_status": "ranked",
    },
    {
        "score": 53,
        "tier": "海外受认可私立本科（未入三大总榜）",
        "qs_rank_min": None,
        "qs_rank_max": None,
        "rank_status": "unranked_verified_private",
    },
)


OFFICIAL_RANKING_SOURCES = {
    "qs_wur_2027": {
        "publisher": "QS Quacquarelli Symonds",
        "title": "QS World University Rankings 2027",
        "edition": 2027,
        "role": "primary_score_band",
        "url": "https://www.topuniversities.com/qs-top-uni-wur",
        "methodology_url": (
            "https://www.topuniversities.com/world-university-rankings/methodology"
        ),
    },
    "the_wur_2026": {
        "publisher": "Times Higher Education",
        "title": "World University Rankings 2026",
        "edition": 2026,
        "role": "secondary_evidence",
        "url": (
            "https://www.timeshighereducation.com/world-university-rankings/"
            "latest/world-ranking"
        ),
        "methodology_url": (
            "https://www.timeshighereducation.com/sites/default/files/"
            "breaking_news_files/the_world_university_rankings_2026_methodology.pdf"
        ),
        "as_of_note": (
            "THE WUR 2027 is scheduled for 2026-09-30; on 2026-09-29, "
            "THE WUR 2026 is the latest published overall table."
        ),
        "release_note_url": (
            "https://www.timeshighereducation.com/world-university-rankings"
        ),
    },
    "arwu_2026": {
        "publisher": "ShanghaiRanking Consultancy",
        "title": "Academic Ranking of World Universities 2026",
        "edition": 2026,
        "role": "secondary_evidence",
        "url": "https://www.shanghairanking.com/rankings/arwu/2026",
    },
}


OFFICIAL_INSTITUTION_SOURCES = {
    "cornell_university": {
        "qs_profile": "https://www.topuniversities.com/universities/cornell-university",
        "the_profile": (
            "https://www.timeshighereducation.com/world-university-rankings/"
            "cornell-university"
        ),
        "accreditation": "https://irp.cornell.edu/university-accreditation",
    },
    "university_of_macau": {
        "qs_profile": "https://www.topuniversities.com/universities/university-macau",
        "the_profile": (
            "https://www.timeshighereducation.com/world-university-rankings/"
            "university-macau"
        ),
        "arwu_profile": (
            "https://www.shanghairanking.com/universities/university-of-macau"
        ),
        "official_overview": "https://www.um.edu.mo/about-um/introduction/",
        "official_names": "https://www.um.edu.mo/about-um/identity/",
    },
    "diploma_hochschule": {
        "official_overview": "https://www.diploma.de/ueber-uns",
        "official_history": "https://www.diploma.de/historie",
        "official_accreditation_faq": "https://www.diploma.de/faq",
    },
}


_TIER_BY_SCORE = {band["score"]: band["tier"] for band in OVERSEAS_SCORE_BANDS}


def _band_for_qs_rank(qs_rank):
    if qs_rank is None:
        return OVERSEAS_SCORE_BANDS[-1]
    for band in OVERSEAS_SCORE_BANDS:
        minimum = band["qs_rank_min"]
        maximum = band["qs_rank_max"]
        if minimum is not None and minimum <= qs_rank <= maximum:
            return band
    raise ValueError(f"QS rank is outside configured bands: {qs_rank}")


def _school(
    canonical,
    aliases,
    region,
    qs_rank,
    qs_rank_display=None,
    *,
    popular=True,
    basis=None,
    rankings=None,
    match_mode="exact_normalized",
):
    band = _band_for_qs_rank(qs_rank)
    qs_display = qs_rank_display or (str(qs_rank) if qs_rank is not None else None)
    ranking_data = rankings or {
        "qs_world": {
            "edition": 2027,
            "rank": qs_rank,
            "display": qs_display,
            "source": "qs_wur_2027",
        }
    }
    return {
        "canonical": canonical,
        "aliases": tuple(aliases),
        "region": region,
        "qs_rank": qs_rank,
        "score": band["score"],
        "tier": band["tier"],
        "basis": basis or (
            f"QS World University Rankings 2027 #{qs_display}; "
            f"按QS区间预计算为{band['score']}分"
        ),
        "popular": popular,
        "rankings": ranking_data,
        "match_mode": match_mode,
    }


# 精简名单以中国求职简历中常见的美、英、加、澳、新加坡、港澳院校为主，
# 并补充新西兰常见院校。aliases 只保留完整、可安全匹配的名称。
OVERSEAS_SCHOOLS = (
    # 100 分：QS 2027 前 30
    _school("Massachusetts Institute of Technology", ("麻省理工学院", "麻省理工大学", "麻省理工"), "美国", 1),
    _school("Stanford University", ("斯坦福大学",), "美国", 2, "=2"),
    _school("Harvard University", ("哈佛大学",), "美国", 5),
    _school("California Institute of Technology", ("加州理工学院", "加州理工大学"), "美国", 7),
    _school("University of Pennsylvania", ("宾夕法尼亚大学",), "美国", 15),
    _school(
        "Cornell University",
        ("康奈尔大学", "康乃尔大学"),
        "美国",
        16,
        "=16",
        basis="QS 2027并列16、THE 2026并列18、ARWU 2026第12；三榜均处世界前20，计100分",
        rankings={
            "qs_world": {"edition": 2027, "rank": 16, "display": "=16", "source": "qs_wur_2027"},
            "the_world": {"edition": 2026, "rank": 18, "display": "=18", "source": "the_wur_2026"},
            "arwu": {"edition": 2026, "rank": 12, "display": "12", "source": "arwu_2026"},
        },
    ),
    _school("Yale University", ("耶鲁大学",), "美国", 16, "=16"),
    _school("Johns Hopkins University", ("约翰斯·霍普金斯大学", "约翰霍普金斯大学", "约翰斯霍普金斯大学"), "美国", 20, "=20"),
    _school("University of California, Berkeley", ("University of California Berkeley", "UC Berkeley", "加州大学伯克利分校", "加利福尼亚大学伯克利分校"), "美国", 20, "=20"),
    _school("University of Chicago", ("芝加哥大学",), "美国", 24),
    _school("Princeton University", ("普林斯顿大学",), "美国", 27),
    _school("Imperial College London", ("帝国理工学院", "帝国理工大学"), "英国", 2, "=2"),
    _school("University of Oxford", ("牛津大学",), "英国", 4),
    _school("University of Cambridge", ("剑桥大学",), "英国", 6),
    _school("University College London", ("伦敦大学学院",), "英国", 8, "=8"),
    _school("McGill University", ("麦吉尔大学",), "加拿大", 30),
    _school("University of New South Wales", ("UNSW Sydney", "The University of New South Wales", "新南威尔士大学"), "澳大利亚", 19),
    _school("University of Melbourne", ("The University of Melbourne", "墨尔本大学"), "澳大利亚", 22, "=22"),
    _school("University of Sydney", ("The University of Sydney", "悉尼大学"), "澳大利亚", 28),
    _school("Australian National University", ("The Australian National University", "澳大利亚国立大学", "澳洲国立大学"), "澳大利亚", 29),
    _school("National University of Singapore", ("新加坡国立大学",), "新加坡", 10),
    _school("Nanyang Technological University, Singapore", ("Nanyang Technological University Singapore", "南洋理工大学", "新加坡南洋理工大学"), "新加坡", 12),
    _school("The University of Hong Kong", ("University of Hong Kong", "香港大学"), "中国香港", 11),
    _school("The Chinese University of Hong Kong", ("Chinese University of Hong Kong", "香港中文大学"), "中国香港", 18),

    # 92 分：QS 2027 第 31-100
    _school("Columbia University", ("哥伦比亚大学",), "美国", 43, "=43"),
    _school("Northwestern University", ("美国西北大学", "西北大学（美国）"), "美国", 45, "=45"),
    _school("University of California, Los Angeles", ("University of California Los Angeles", "加州大学洛杉矶分校", "加利福尼亚大学洛杉矶分校"), "美国", 49),
    _school("University of Michigan-Ann Arbor", ("University of Michigan, Ann Arbor", "密歇根大学安娜堡分校", "密西根大学安娜堡分校"), "美国", 51),
    _school("Carnegie Mellon University", ("卡内基梅隆大学", "卡耐基梅隆大学"), "美国", 55),
    _school("New York University", ("纽约大学",), "美国", 58),
    _school("Brown University", ("布朗大学",), "美国", 66),
    _school("Duke University", ("杜克大学",), "美国", 70),
    _school("University of Texas at Austin", ("The University of Texas at Austin", "德克萨斯大学奥斯汀分校", "得克萨斯大学奥斯汀分校", "德州大学奥斯汀分校"), "美国", 72),
    _school("University of Illinois Urbana-Champaign", ("University of Illinois at Urbana-Champaign", "伊利诺伊大学厄巴纳-香槟分校", "伊利诺伊大学香槟分校"), "美国", 74),
    _school("University of California, San Diego", ("University of California San Diego", "加州大学圣地亚哥分校", "加利福尼亚大学圣地亚哥分校"), "美国", 81),
    _school("Pennsylvania State University", ("Pennsylvania State University, University Park", "宾夕法尼亚州立大学", "宾州州立大学"), "美国", 92, "=92"),
    _school("University of Washington", ("华盛顿大学",), "美国", 92, "=92"),
    _school("Boston University", ("波士顿大学",), "美国", 94),
    _school("Purdue University", ("Purdue University West Lafayette", "普渡大学", "普渡大学西拉法叶分校"), "美国", 100, "=100"),
    _school("University of Edinburgh", ("The University of Edinburgh", "爱丁堡大学"), "英国", 35),
    _school("King's College London", ("伦敦国王学院", "伦敦大学国王学院"), "英国", 37),
    _school("University of Manchester", ("The University of Manchester", "曼彻斯特大学"), "英国", 40, "=40"),
    _school("University of Bristol", ("布里斯托大学", "布里斯托尔大学"), "英国", 57),
    _school("London School of Economics and Political Science", ("The London School of Economics and Political Science", "伦敦政治经济学院"), "英国", 62),
    _school("University of Warwick", ("华威大学",), "英国", 68, "=68"),
    _school("University of Birmingham", ("伯明翰大学",), "英国", 68, "=68"),
    _school("University of Leeds", ("利兹大学",), "英国", 77, "=77"),
    _school("University of Glasgow", ("格拉斯哥大学",), "英国", 80),
    _school("University of Sheffield", ("The University of Sheffield", "谢菲尔德大学"), "英国", 82, "=82"),
    _school("Durham University", ("杜伦大学",), "英国", 85),
    _school("University of Nottingham", ("The University of Nottingham", "诺丁汉大学"), "英国", 97, "=97"),
    _school("University of Toronto", ("多伦多大学",), "加拿大", 32),
    _school("University of British Columbia", ("The University of British Columbia", "英属哥伦比亚大学", "不列颠哥伦比亚大学", "卑诗大学"), "加拿大", 45, "=45"),
    _school("University of Alberta", ("阿尔伯塔大学",), "加拿大", 96),
    _school("Monash University", ("蒙纳士大学", "莫纳什大学"), "澳大利亚", 31),
    _school("University of Queensland", ("The University of Queensland", "昆士兰大学"), "澳大利亚", 40, "=40"),
    _school("University of Western Australia", ("The University of Western Australia", "西澳大学", "西澳大利亚大学"), "澳大利亚", 77, "=77"),
    _school("Adelaide University", ("The University of Adelaide", "University of Adelaide", "阿德莱德大学"), "澳大利亚", 79),
    _school("University of Technology Sydney", ("University of Technology, Sydney", "悉尼科技大学"), "澳大利亚", 87, "=87"),
    _school("Hong Kong University of Science and Technology", ("The Hong Kong University of Science and Technology", "香港科技大学"), "中国香港", 33),
    _school("Hong Kong Polytechnic University", ("The Hong Kong Polytechnic University", "香港理工大学"), "中国香港", 50),
    _school("City University of Hong Kong", ("City University of Hong Kong (CityUHK)", "香港城市大学"), "中国香港", 52, "=52"),
    _school("University of Auckland", ("The University of Auckland", "奥克兰大学"), "新西兰", 67),

    # 85 分：QS 2027 第 101-300
    _school("Rice University", ("莱斯大学",), "美国", 122),
    _school("University of Wisconsin-Madison", ("University of Wisconsin Madison", "威斯康星大学麦迪逊分校", "威斯康辛大学麦迪逊分校"), "美国", 131, "=131"),
    _school("University of California, Davis", ("University of California Davis", "加州大学戴维斯分校", "加利福尼亚大学戴维斯分校"), "美国", 137),
    _school("Georgia Institute of Technology", ("Georgia Tech", "佐治亚理工学院", "乔治亚理工学院"), "美国", 142, "=142"),
    _school("University of Southern California", ("南加州大学",), "美国", 153),
    _school("University of North Carolina at Chapel Hill", ("The University of North Carolina at Chapel Hill", "北卡罗来纳大学教堂山分校", "北卡大学教堂山分校"), "美国", 158, "=158"),
    _school("Washington University in St. Louis", ("Washington University in Saint Louis", "圣路易斯华盛顿大学", "华盛顿大学圣路易斯分校"), "美国", 162, "=162"),
    _school("Texas A&M University", ("Texas A and M University", "德州农工大学", "得克萨斯农工大学"), "美国", 169),
    _school("Arizona State University", ("亚利桑那州立大学",), "美国", 172),
    _school("University of California, Santa Barbara", ("University of California Santa Barbara", "加州大学圣塔芭芭拉分校", "加州大学圣巴巴拉分校"), "美国", 173),
    _school("Michigan State University", ("密歇根州立大学", "密西根州立大学"), "美国", 182),
    _school("Emory University", ("埃默里大学", "艾莫里大学"), "美国", 183),
    _school("Queen Mary University of London", ("伦敦玛丽女王大学", "伦敦大学玛丽女王学院"), "英国", 103),
    _school("University of Southampton", ("南安普顿大学",), "英国", 111, "=111"),
    _school("University of St Andrews", ("University of St. Andrews", "圣安德鲁斯大学"), "英国", 115, "=115"),
    _school("University of Bath", ("巴斯大学",), "英国", 125),
    _school("University of Exeter", ("埃克塞特大学",), "英国", 136),
    _school("University of Liverpool", ("利物浦大学",), "英国", 139),
    _school("Newcastle University", ("英国纽卡斯尔大学", "纽卡斯尔大学（英国）"), "英国", 149),
    _school("University of York", ("英国约克大学", "约克大学（英国）"), "英国", 158, "=158"),
    _school("Lancaster University", ("兰卡斯特大学",), "英国", 164),
    _school("Queen's University Belfast", ("Queen’s University Belfast", "贝尔法斯特女王大学", "贝尔法斯特皇后大学"), "英国", 174, "=174"),
    _school("Cardiff University", ("卡迪夫大学",), "英国", 179, "=179"),
    _school("University of Reading", ("雷丁大学",), "英国", 196, "=196"),
    _school("University of Waterloo", ("滑铁卢大学",), "加拿大", 113, "=113"),
    _school("Western University", ("University of Western Ontario", "韦仕敦大学", "西安大略大学"), "加拿大", 142, "=142"),
    _school("Université de Montréal", ("University of Montreal", "蒙特利尔大学"), "加拿大", 162, "=162"),
    _school("McMaster University", ("麦克马斯特大学",), "加拿大", 174, "=174"),
    _school("Queen's University at Kingston", ("Queen's University, Kingston", "加拿大女王大学", "女王大学（加拿大）", "加拿大皇后大学"), "加拿大", 179, "=179"),
    _school("RMIT University", ("Royal Melbourne Institute of Technology", "皇家墨尔本理工大学"), "澳大利亚", 119, "=119"),
    _school("Macquarie University", ("麦考瑞大学", "麦格理大学"), "澳大利亚", 126, "=126"),
    _school("Curtin University", ("科廷大学",), "澳大利亚", 189),
    _school("University of Wollongong", ("伍伦贡大学", "卧龙岗大学"), "澳大利亚", 195),
    _school(
        "University of Macau",
        ("Universidade de Macau", "澳门大学", "澳門大學"),
        "中国澳门",
        267,
        basis="QS 2027第267、THE 2026并列145、ARWU 2026第301-400；按QS 101-300档计85分",
        rankings={
            "qs_world": {"edition": 2027, "rank": 267, "display": "267", "source": "qs_wur_2027"},
            "the_world": {"edition": 2026, "rank": 145, "display": "=145", "source": "the_wur_2026"},
            "arwu": {"edition": 2026, "rank": None, "display": "301-400", "source": "arwu_2026"},
        },
    ),
    _school("University of Otago", ("奥塔哥大学",), "新西兰", 198),

    # 77 分：QS 2027 第 301-500
    _school("Macau University of Science and Technology", ("澳门科技大学", "澳門科技大學"), "中国澳门", 440, "=440"),

    # 53 分：内部精确匹配，不在公开的热门院校示例中展示。
    _school(
        "DIPLOMA Hochschule",
        (
            "DIPLOMA Hochschule – Private Fachhochschule Nordhessen",
            "DIPLOMA Hochschule - Private Fachhochschule Nordhessen",
            "Private Fachhochschule Nordhessen",
            "DIPLOMA – FH Nordhessen",
            "DIPLOMA - FH Nordhessen",
            "Diploma University of Applied Sciences",
            "DIPLOMA Fachhochschule Nordhessen Deutschland",
        ),
        "德国",
        None,
        popular=False,
        match_mode="exact_normalized_only",
        basis=(
            "未在QS 2027、THE 2026、ARWU 2026总榜查到；院校官网确认其为德国私立应用科学大学，"
            "1997年获黑森州批准设立、2008年获无限期国家认可，按受认可私立本科档计53分"
        ),
        rankings={
            "qs_world": {"edition": 2027, "rank": None, "display": None, "status": "not_listed", "source": "qs_wur_2027"},
            "the_world": {"edition": 2026, "rank": None, "display": None, "status": "not_listed", "source": "the_wur_2026"},
            "arwu": {"edition": 2026, "rank": None, "display": None, "status": "not_listed", "source": "arwu_2026"},
            "official_status": {
                "status": "private_state_recognised_university_of_applied_sciences",
                "sources": (
                    "official_institution_sources.diploma_hochschule.official_overview",
                    "official_institution_sources.diploma_hochschule.official_history",
                    "official_institution_sources.diploma_hochschule.official_accreditation_faq",
                ),
            },
        },
    ),
)


# 明确禁止作为独立别名录入。若调用方确实接收到缩写，应结合国家、城市、
# 完整教育字段等上下文另行消歧，不能直接映射。
UNSAFE_SHORT_ALIASES = frozenset(
    {
        "ANU", "BU", "CMU", "CUHK", "HKU", "HKUST", "LSE", "MIT",
        "NTU", "NUS", "NYU", "RMIT", "UCL", "UCLA", "UCSD", "UIUC",
        "UM", "UNSW", "USC", "UTS", "UWA",
        "澳大", "宾大", "港大", "港科大", "港中文",
    }
)


def _validate_data():
    """导入时校验排名落档、字段和危险别名，避免静默污染评分。"""
    required = {
        "canonical", "aliases", "qs_rank", "score", "tier", "basis",
        "popular", "rankings",
    }
    canonical_names = set()
    alias_owners = {}

    for school in OVERSEAS_SCHOOLS:
        missing = required.difference(school)
        if missing:
            raise ValueError(f"{school.get('canonical')!r} missing fields: {sorted(missing)}")

        canonical = school["canonical"]
        if canonical in canonical_names:
            raise ValueError(f"duplicate canonical school: {canonical}")
        canonical_names.add(canonical)

        expected_band = _band_for_qs_rank(school["qs_rank"])
        if school["score"] != expected_band["score"]:
            raise ValueError(
                f"score mismatch for {canonical}: {school['score']} != "
                f"{expected_band['score']}"
            )
        if school["tier"] != expected_band["tier"]:
            raise ValueError(f"tier mismatch for {canonical}: {school['tier']}")

        for alias in school["aliases"]:
            if alias in UNSAFE_SHORT_ALIASES:
                raise ValueError(f"unsafe short alias for {canonical}: {alias}")
            normalized = " ".join(alias.casefold().split())
            previous = alias_owners.get(normalized)
            if previous and previous != canonical:
                raise ValueError(
                    f"alias collision: {alias!r} belongs to {previous!r} and {canonical!r}"
                )
            alias_owners[normalized] = canonical


_validate_data()


__all__ = (
    "DATA_AS_OF",
    "OVERSEAS_SCORE_BANDS",
    "OFFICIAL_RANKING_SOURCES",
    "OFFICIAL_INSTITUTION_SOURCES",
    "OVERSEAS_SCHOOLS",
    "UNSAFE_SHORT_ALIASES",
)
