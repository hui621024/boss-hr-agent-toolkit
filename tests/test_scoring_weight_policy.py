"""Requested 15/35 weights and historical report labels; no external services."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

score = module('weight_scoring', 'resume-screener/scripts/score_resumes.py')
report = module('weight_report', 'html-report/scripts/generate_html_report.py')

class WeightPolicyTests(unittest.TestCase):
    def test_requested_formula(self):
        self.assertEqual(score.WEIGHTS_PCT, {'edu':15, 'exp':35, 'skill':25, 'proj':15, 'major':10})
        self.assertAlmostEqual(sum(score.WEIGHTS.values()), 1)
        raw = {'edu':60, 'exp':80, 'skill':70, 'proj':90, 'major':100}
        self.assertEqual(score.calc_total(score.calc_weighted(raw)), 78)
        self.assertEqual(raw['exp'], 80)

    def test_header_uses_report_weights_including_historical_reports(self):
        for weights in ([15,35,25,15,10], [25,25,25,15,10]):
            c={'name':'test', 'dimensions':[{'pct':80,'weight':w,'weighted':80*w/100} for w in weights]}
            h=report.render({'candidates':[c]})
            self.assertIn(f'<th>学历 {weights[0]}%</th>', h)
            self.assertIn(f'<th>工作经验 {weights[1]}%</th>', h)

    def test_thresholds_unchanged(self):
        self.assertEqual(score.calc_tier(70), '推荐')
        self.assertEqual(score.calc_tier(60), '待定')
        self.assertEqual(score.calc_tier(59.9), '不推荐')

if __name__ == '__main__':
    unittest.main()
