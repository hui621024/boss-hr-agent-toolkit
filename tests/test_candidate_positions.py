"""位置关联及报告转义回归测试，使用虚构数据，不连接浏览器。"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from shared.candidate_positions import enrich_candidate_positions

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('report_renderer', ROOT / 'html-report/scripts/generate_html_report.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class PositionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.write('recommend_geek_ids.json', [{'encryptGeekId': 'id-A'}, {'encryptGeekId': 'id-B'}])
        self.snapshot = {'job_id': 'job', 'run_id': 'run', 'checked_at': '2026-09-29T10:00:00+08:00',
                         'matches': [{'geek_id': 'id-B', 'index': 39}], 'total': 50}
        self.write('candidate_positions.json', self.snapshot)

    def write(self, name, value):
        (self.path / name).write_text(json.dumps(value), encoding='utf-8')

    def test_same_name_never_used_and_file_order_not_page_position(self):
        candidates = [{'name': 'same', 'geek_id': 'id-B'}, {'name': 'same'}, {'name': 'same', 'geek_id': 'other'}]
        enrich_candidate_positions(candidates, self.path, 'job', 'run', refresh=False)
        self.assertEqual(candidates[0]['source_list_index'], 2)
        self.assertEqual(candidates[0]['boss_position']['index'], 39)
        self.assertTrue(candidates[0]['boss_position']['historical'])
        self.assertNotIn('boss_position', candidates[1])
        self.assertNotIn('boss_position', candidates[2])

    def test_other_job_or_run_and_ambiguous_id_are_rejected(self):
        for job, run in [('wrong', 'run'), ('job', 'wrong')]:
            c = [{'geek_id': 'id-B'}]
            enrich_candidate_positions(c, self.path, job, run, refresh=False)
            self.assertNotIn('boss_position', c[0])
        self.snapshot['matches'].append({'geek_id': 'id-B', 'index': 40})
        self.write('candidate_positions.json', self.snapshot)
        c = [{'geek_id': 'id-B'}]
        enrich_candidate_positions(c, self.path, 'job', 'run', refresh=False)
        self.assertNotIn('boss_position', c[0])

    def test_fresh_missing_candidate_does_not_reuse_old_position(self):
        current = {**self.snapshot, 'matches': []}
        c = [{'geek_id': 'id-B', 'boss_position': {'index': 39}}]
        with patch('shared.candidate_positions.capture_positions', return_value=current):
            enrich_candidate_positions(c, self.path, 'job', 'run')
        self.assertNotIn('boss_position', c[0])
        self.assertEqual(c[0]['boss_position_status'], 'not_in_loaded_list')

    def test_summary_has_all_evidence_and_escaped_content(self):
        c = {'name': 'Test', 'geek_id': 'id-B', 'rank': 1, 'tier': '推荐', 'total': 75,
             'highlights': ['FastAPI', '<script>unsafe</script>'], 'concerns': ['Needs RAG demo'],
             'boss_position': {'index': 39, 'checked_at': '2026-09-29'}, 'source_list_index': 2}
        html = renderer.render({'candidates': [c]})
        table = html.split('<tbody>')[1].split('</tbody>')[0]
        for value in ['第39张', '2026-09-29', 'FastAPI', 'Needs RAG demo', 'id-B', '&lt;script&gt;']:
            self.assertIn(value, table)
        self.assertNotIn('<script>', html)
        c['hard_pass'] = False
        c['hard_reason'] = 'Required experience absent'
        c['concerns'] = []
        table = renderer.render({'candidates': [c]}).split('<tbody>')[1].split('</tbody>')[0]
        self.assertIn('Required experience absent', table)
        self.assertIn('FastAPI', table)


if __name__ == '__main__':
    unittest.main()
