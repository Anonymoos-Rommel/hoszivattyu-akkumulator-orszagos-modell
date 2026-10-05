import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B02 import reported_service_controls as model


class ReportedServiceControlTests(unittest.TestCase):
    def test_exact_source_vector_and_scope(self):
        rows = model.load_controls()
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows['GAS_PRIMARY'].mean_reported_indoor_temperature_c, Decimal('21.17'))
        self.assertEqual(rows['GAS_SECONDARY_ONLY'].mean_dwelling_area_m2, Decimal('96.49'))
        self.assertEqual(rows['NO_GAS_HEATING'].mean_reported_heated_area_share_pct, Decimal('84.97'))
        for row in rows.values():
            self.assertEqual(row.reference_year, 2022)
            self.assertFalse(row.heat_allocation_allowed)
            self.assertEqual(row.claim_scope, 'SURVEY_GROUP_MEAN_CONTROL_ONLY')

    def test_recomposition_keeps_source_residuals(self):
        results = model.recomposition_diagnostics()
        for result in results.values():
            self.assertNotEqual(result['residual'], 0)
            self.assertLess(abs(result['residual']), Decimal('0.01'))
        self.assertEqual(results['mean_dwelling_area_m2']['printed_all_mean'], Decimal('79.24'))

    def test_product_of_means_cannot_authorize_heated_area(self):
        for group in model.GROUPS:
            with self.assertRaisesRegex(ValueError, 'CROSS_MOMENT'):
                model.mean_heated_area_m2(group)
        # Same two marginal means, different pairing, different heated area.
        areas = [Decimal(50), Decimal(100)]
        use = [Decimal('0.5'), Decimal(1)]
        same = sum(a*b for a,b in zip(areas,use))/2
        reverse = sum(a*b for a,b in zip(areas,reversed(use)))/2
        self.assertNotEqual(same, reverse)
        with self.assertRaisesRegex(ValueError, 'unknown'):
            model.mean_heated_area_m2('JRC_GAS')

    def test_source_tamper_duplicate_and_nonfinite_fail_closed(self):
        original = model.ROOT
        relative = 'data/processed/b02/rekk_reported_service_2022.csv'
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'registry').mkdir()
            (root/'data/processed/b02').mkdir(parents=True)
            manifest = json.loads((original/'registry/b02_reported_service_manifest.json').read_text())
            with (original/relative).open() as f:
                rows = list(csv.DictReader(f))
            for case in ('hash', 'duplicate', 'nonfinite', 'date'):
                copied = [dict(r) for r in rows]
                if case == 'hash': copied[0]['mean_dwelling_area_m2'] = '80'
                if case == 'duplicate': copied[1]['group_id'] = 'ALL'
                if case == 'nonfinite': copied[0]['mean_dwelling_area_m2'] = 'NaN'
                if case == 'date': copied[0]['reference_year'] = '2026'
                with (root/relative).open('w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
                    writer.writeheader(); writer.writerows(copied)
                current = dict(manifest)
                if case != 'hash':
                    current['curated_extract_sha256'] = hashlib.sha256((root/relative).read_bytes()).hexdigest()
                (root/'registry/b02_reported_service_manifest.json').write_text(json.dumps(current))
                with patch.object(model, 'ROOT', root):
                    with self.assertRaises(ValueError): model.load_controls()


if __name__ == '__main__': unittest.main()
