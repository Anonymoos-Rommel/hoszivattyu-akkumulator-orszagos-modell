import csv
import json
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from modules.B12.input_accounting_contract import Scalar, Period


ROOT = Path(__file__).resolve().parents[1]


class CostLifecycleHandoffTests(unittest.TestCase):
    def setUp(self):
        self.handoff = json.loads((ROOT/'registry/b06_cost_lifecycle_handoff.json').read_text())

    def test_single_life_is_modeled_ass_e2_not_observed_survival(self):
        life = self.handoff['service_life']
        self.assertEqual((life['value'], life['unit'], life['truth'], life['evidence_tier']),
                         ('17', 'year', 'ASS', 'E2'))
        self.assertEqual(life['asset_life_definition'], 'EXPLICIT_SCENARIO_LIFE')
        self.assertIsNone(self.handoff['unresolved']['observed_hungarian_survival_distribution'])
        self.assertIsNone(self.handoff['unresolved']['whole_system_life_years'])

    def test_existing_b12_scalar_accepts_the_reviewed_partial_input(self):
        life = self.handoff['service_life']; period = life['reference_period']
        scalar = Scalar(value=Decimal(life['value']), unit=life['unit'], truth=life['truth'],
                        reference_period=Period(date.fromisoformat(period['start']),
                                                date.fromisoformat(period['end'])),
                        basis_id=life['basis_id'], source_ids=tuple(life['source_ids']),
                        scenario_ref=life['scenario_ref'], evidence_tier=life['evidence_tier'],
                        admission_ref=life['admission_ref'], reason=None, acquisition_ref=None)
        self.assertEqual(scalar.value, Decimal('17'))
        self.assertEqual(scalar.admission_ref, self.handoff['handoff_id'])
        self.assertIn('NOT_COMMISSIONING', period['convention'])

    def test_maintenance_cycle_is_not_a_paid_visit_or_zero_cost(self):
        m = self.handoff['maintenance_condition']
        self.assertEqual((m['value'], m['unit'], m['truth']), ('1','maintenance_cycle/year','ASS'))
        for key in ('paid_supplier_visits_per_year','annual_monetary_om_huf','repair_cost_huf'):
            self.assertIsNone(m[key], key)
        self.assertFalse(m['unrelated_supplier_visit_price_joined'])

    def test_four_transfer_debts_continue_model_but_block_final_physical_claim(self):
        debts = self.handoff['validation_debt']
        self.assertEqual({d['id'] for d in debts}, {'B06-LIFE-SYSTEM-BOUNDARY',
                         'B06-LIFE-MAINTENANCE','B06-LIFE-HU-DUTY','B06-LIFE-SERVICE'})
        for d in debts:
            self.assertEqual(d['evidence_tier'],'E2')
            self.assertFalse(d['model_blocker']); self.assertTrue(d['finalization_blocker'])
            self.assertTrue(d['upgrade'])

    def test_debts_are_registered_centrally_and_linked_to_both_slices(self):
        ids={d['id'] for d in self.handoff['validation_debt']}
        with (ROOT/'registry/project_blocker_evidence_audit.csv').open(newline='') as f:
            rows=[r for r in csv.DictReader(f) if r['blocker_id'] in ids]
        self.assertEqual(len(rows),len(ids))
        self.assertEqual({r['blocker_id'] for r in rows},ids)
        for row in rows:
            self.assertEqual(row['source_registry'],'b06_cost_lifecycle_handoff.json')
            self.assertEqual((row['evidence_tier'],row['blocker_class']),('E2','VALIDATION_BLOCKER'))
            self.assertEqual((row['model_blocker'],row['finalization_blocker']),('no','yes'))
        plan=json.loads((ROOT/'registry/v1_research_plan.json').read_text())
        slices={s['slice_id']:s for m in plan['modules'] for s in m['slices']}
        for key in ('B06-D02','B12-D01'):
            self.assertTrue(ids.issubset(set(slices[key]['validation_debt_ids'])))
            self.assertEqual(slices[key]['status'],'INTEGRATING')

    def test_existing_source_reused_with_exact_external_identity(self):
        source = self.handoff['source']
        with (ROOT/'registry/sources.csv').open(newline='') as f:
            rows=[r for r in csv.DictReader(f) if r['source_id']==source['source_id']]
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['url'],source['original_url'])
        self.assertEqual(rows[0]['local_snapshot_sha256'],source['sha256'])
        self.assertEqual(rows[0]['evidence_status'],'OBS')  # existing system-binding claim
        self.assertIsNone(source['repo_snapshot_path'])
        self.assertEqual(self.handoff['target_scope']['services'],['space_heating'])
        self.assertIn('domestic_hot_water',self.handoff['source_system']['services'])

    def test_no_invented_replacement_or_complete_cost(self):
        self.assertTrue(all(v is None for v in self.handoff['unresolved'].values()))
        d=self.handoff['downstream']
        for key in ('replacement_scheduler_exists','external_b12_arithmetic_admitted',
                    'full_costs_or_assets_complete','whole_slice_accepted'):
            self.assertFalse(d[key],key)
        self.assertEqual(d['b15_gate'],'BLOCKED')

    def test_inventory_narrows_subinput_without_erasing_global_missingness(self):
        inventory=json.loads((ROOT/'registry/b12_input_inventory.json').read_text())
        admissions=inventory['current_source_admissions']
        self.assertEqual(len(admissions),1)
        self.assertEqual(admissions[0]['artifact'],'registry/b06_cost_lifecycle_handoff.json')
        self.assertEqual(admissions[0]['field'],'assets.service_life')
        self.assertFalse(admissions[0]['numerical_b12_output_admitted'])
        self.assertEqual(inventory['numerical_output_status'],'Q')
        for row in inventory['inputs']:
            self.assertIsNone(row['value']); self.assertEqual(row['status'],'Q')
        assets=next(r for r in inventory['inputs'] if r['field']=='assets')
        self.assertIn(admissions[0]['artifact'],assets['upstream_authorities'])
