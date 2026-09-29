"""只读已有推荐页，按候选人ID记录有时间戳的列表位置；不导航或打开浏览器。"""
from __future__ import annotations

import json
import socket
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def capture_positions(candidate_ids, job_id, run_id):
    """无现有CDP/对应岗位页面时返回None，不影响离线报告。"""
    if not candidate_ids:
        return None
    try:
        with socket.create_connection(('127.0.0.1', 9222), timeout=0.3):
            pass
        from patchright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=3000)
            frames = []
            for context in browser.contexts:
                for page in context.pages:
                    for frame in page.frames:
                        url = urlsplit(frame.url)
                        if (url.hostname == 'www.zhipin.com'
                                and url.path == '/web/frame/recommend/'
                                and parse_qs(url.query).get('jobid') == [job_id]):
                            frames.append(frame)
            if len(frames) != 1:
                return None
            result = frames[0].evaluate('''ids => {
                const cards = [...document.querySelectorAll('.card-list .card-item')]
                    .filter(el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden');
                return {total: cards.length, matches: cards.flatMap((el, i) => {
                    const html = el.outerHTML;
                    return ids.filter(id => html.includes(id)).map(id => ({geek_id:id, index:i+1}));
                })};
            }''', list(candidate_ids))
            if not result['total']:
                return None
            return {'run_id': run_id, 'job_id': job_id,
                    'checked_at': datetime.now().astimezone().isoformat(timespec='seconds'),
                    **result}
    except Exception:
        # 不输出浏览器异常原文，避免URL参数或平台认证字段进入日志。
        return None


def _read_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def enrich_candidate_positions(candidates, process_dir, job_id, run_id, *, refresh=True):
    """采集文件序号与页面卡片位置分开保存；禁止姓名回退及跨run关联。"""
    process = Path(process_dir)
    saved = _read_json(process / 'recommend_geek_ids.json', [])
    source_positions = {}
    if isinstance(saved, list):
        for index, card in enumerate(saved, 1):
            if isinstance(card, dict) and card.get('encryptGeekId'):
                source_positions.setdefault(card['encryptGeekId'], []).append(index)
    ids = {c['geek_id'] for c in candidates if c.get('geek_id')}
    snapshot = capture_positions(ids, job_id, run_id) if refresh else None
    fresh = snapshot is not None
    if fresh:
        try:
            (process / 'candidate_positions.json').write_text(
                json.dumps(snapshot, ensure_ascii=False, indent=2), encoding='utf-8')
        except OSError:
            pass
    else:
        snapshot = _read_json(process / 'candidate_positions.json', {})
    if not isinstance(snapshot, dict) or snapshot.get('job_id') != job_id or snapshot.get('run_id') != run_id:
        snapshot = {}
    matches = [m for m in snapshot.get('matches', []) if isinstance(m, dict)
               and type(m.get('index')) is int and m['index'] > 0]
    counts = Counter(m.get('geek_id') for m in matches)
    positions = {m['geek_id']: m['index'] for m in matches if counts[m.get('geek_id')] == 1}
    for candidate in candidates:
        gid = candidate.get('geek_id')
        candidate.pop('boss_position', None)
        candidate.pop('source_list_index', None)
        indexes = source_positions.get(gid, [])
        if len(indexes) == 1:
            candidate['source_list_index'] = indexes[0]
        candidate['boss_position_status'] = 'not_in_loaded_list' if fresh else 'unavailable'
        if gid in positions and snapshot.get('checked_at'):
            candidate['boss_position'] = {'index': positions[gid], 'checked_at': snapshot['checked_at'],
                                          'historical': not fresh}
            candidate['boss_position_status'] = 'matched' if fresh else 'historical'
