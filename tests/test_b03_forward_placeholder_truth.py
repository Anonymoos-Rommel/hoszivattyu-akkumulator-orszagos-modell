"""Regression for the specific unqualified ACER placeholder, not a price model."""
import csv
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ForwardPlaceholderTruthTests(unittest.TestCase):
    def test_unqualified_curve_has_no_invented_market_dates_or_base(self):
        with (ROOT / 'data/processed/gas_price_forward_curve.csv').open(newline='') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r['curve_id'] for r in rows], ['B03-FWD-ACER-UNQUALIFIED'])
        row = rows[0]
        self.assertEqual(row['status'], 'Q')
        self.assertEqual(row['source_ids'], 'SRC-B03-ACER-TTF-2026')
        self.assertEqual(row['layer'], 'WHOLESALE_IMPORT')
        for field in ('as_of_date', 'delivery_start', 'delivery_end', 'scenario',
                      'eur_per_mwh', 'eur_huf', 'huf_per_m3'):
            self.assertEqual(row[field], '', field)
        self.assertIn('B03-FWD-ACER-2026-08-22', row['notes'])
        self.assertIn('lineage only', row['notes'])
        self.assertIn('not a curve assessment date', row['notes'])
        self.assertIn('Original export not acquired', row['notes'])
        self.assertIn('rights and energy basis unqualified', row['notes'])

    def test_source_retrieval_and_unfulfilled_window_are_not_relabelled(self):
        with (ROOT / 'registry/sources.csv').open(newline='') as f:
            source = next(r for r in csv.DictReader(f) if r['source_id'] == 'SRC-B03-ACER-TTF-2026')
        self.assertEqual(source['published_at'], '2026-04-21')
        self.assertEqual(source['retrieved_at'], '2026-08-22')
        self.assertEqual(source['local_snapshot_sha256'], '')
        with (ROOT / 'registry/open_questions.csv').open(newline='') as f:
            questions = {r['question_id']: r for r in csv.DictReader(f)}
        for qid in ('Q-B03-001', 'Q-B03-002', 'Q-B03-004'):
            self.assertEqual(questions[qid]['status'], 'OPEN')
        self.assertIn('2026-08-22', questions['Q-B03-004']['question'])


if __name__ == '__main__':
    unittest.main()
