"""Synthetic controls only; external panels are never committed as fixtures."""
import copy
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B18 import supply_source_reference as ref
from tools.materialize_b18_supply_source_reference import guard_private_output, write_reference


def selection(sid=ref.TRADE_SOURCE, **changes):
    p = ref.PINS[sid]
    s = ref.SupplySelection(sid, p['dataset_id'], p['product_code'], p['classification'],
        p['reference_year'], p['source_updated_at'], 'HU',
        'WORLD' if sid == ref.TRADE_SOURCE else None,
        '1' if sid == ref.TRADE_SOURCE else None,
        ref.TRADE_METRICS if sid == ref.TRADE_SOURCE else ref.PRODUCTION_METRICS)
    return replace(s, **changes)


def fixture(sid=ref.TRADE_SOURCE):
    p = ref.PINS[sid]
    axes = {'freq': {'A': 0}, 'reporter': {'HU': 0}, 'time': {'2025': 0},
            'product': {p['product_code']: 0}}
    if sid == ref.TRADE_SOURCE:
        axes.update(partner={**{f'SYNTHETIC_{i}': i for i in range(275)},
                            'WORLD': 275, 'INT_EU27_2020': 276, 'EXT_EU27_2020': 277},
                    flow={'1': 0, '2': 1}, indicators={m:i for i,m in enumerate(ref.TRADE_METRICS)})
        values = {'1650': 123, '1651': 4.25, '1653': 12, '1654': 0}
    else:
        axes['indicators'] = {m:i for i,m in enumerate(ref.PRODUCTION_INDICATORS)}
        values = {'1': ':C', '7': '-', '12': ':C', '15': '-', '21': '-', '3': 17, '4': 29}
    return {'version':'2.0','class':'dataset','source':'ESTAT',
            'updated':p['source_updated_at'],'extension':{'id':p['dataset_id']},
            'id':p['dimensions'],'size':p['sizes'],
            'dimension':{d:{'category':{'index':a,'label':{k:f'Synthetic {k}' for k in a}}} for d,a in axes.items()},
            'value':values}


def decode(obj=None, sel=None):
    sel = sel or selection()
    return ref._decode(json.dumps(obj or fixture(sel.source_id)), sel, ref._selection_spec(sel))


class SupplySourceReferenceTests(unittest.TestCase):
    def test_manifest_boundaries_and_bridge(self):
        m=ref.source_manifest()
        self.assertEqual(m['classification_bridge']['prodcom_2025'],'28211400')
        self.assertIsNone(m['classification_bridge']['cn_2025_supplementary_unit'])
        self.assertFalse(m['classification_bridge']['time_series_substitution_authorized'])

    def test_workforce_scenario_tables_cannot_promote_quantities(self):
        j=json.loads((ref.ROOT/'registry/b18_workforce_source_review_manifest.json').read_text())
        for key in ('training_projection','sqa_table35','roadmap_table4'):
            self.assertEqual(j['reviewed_controls'][key]['evidence_status'],'SCN')
        for key in ('sqa_table35','roadmap_table4'):
            self.assertEqual(j['reviewed_controls'][key]['source_transcription_status'],'OBS')
            self.assertEqual(j['reviewed_controls'][key]['arithmetic_check_status'],'DER')

    def test_workforce_scope_and_unknowns_remain_explicit(self):
        j=json.loads((ref.ROOT/'registry/b18_workforce_source_review_manifest.json').read_text())
        self.assertFalse(j['reviewed_controls']['industry_survey']['representative'])
        self.assertEqual(j['model_use_status'],'NO_NATIONAL_CAPACITY_ADMISSION')
        self.assertTrue(all(v is None for v in j['unknowns'].values()))
        self.assertEqual(j['reviewed_controls']['training_projection']['base_renovation_rate_reference_year'],2010)

    def test_source_identity_is_explicit(self):
        with self.assertRaises(ref.SupplySourceReferenceError): ref._selection_spec(None)

    def test_wrong_selection_fields_fail(self):
        for k,v in [('source_id','unknown'),('dataset_id','DS-059367'),('product_code','28251380'),
                    ('classification','CN_2024'),('reference_year',2024),('source_updated_at','2026-10-01'),
                    ('reporter','EU27_2020'),('partner','ALL'),('flow','IMPORT')]:
            with self.subTest(k=k), self.assertRaises(ref.SupplySourceReferenceError):
                ref._selection_spec(selection(**{k:v}))

    def test_no_current_join_by_reversible_label(self):
        for code in ('28251252','28251380','84186100'):
            with self.assertRaises(ref.SupplySourceReferenceError):
                ref._selection_spec(selection(ref.PRODUCTION_SOURCE,product_code=code))

    def test_no_mixed_partner_aggregation(self):
        with self.assertRaises(ref.SupplySourceReferenceError):
            ref._selection_spec(selection(partner=('WORLD','INT_EU27_2020')))

    def test_production_has_no_trade_axes(self):
        for k in ('partner','flow'):
            with self.assertRaises(ref.SupplySourceReferenceError):
                ref._selection_spec(selection(ref.PRODUCTION_SOURCE,**{k:'1'}))

    def test_non_native_capacity_metrics_fail(self):
        for metrics in ((), ['VALUE_IN_EUROS'], ('VALUE_IN_EUROS','VALUE_IN_EUROS'),
                        ('DEVICE_COUNT',), ('IMPORT_SHARE',), ('KW',), ('AVAILABLE_CAPACITY',)):
            with self.assertRaises(ref.SupplySourceReferenceError):
                ref._selection_spec(selection(metrics=metrics))

    def test_native_mass_is_not_count(self):
        a,b,c=decode()
        self.assertEqual(a.value,Decimal(123));self.assertEqual(a.unit,'EUR')
        self.assertEqual(b.value,Decimal('4.25'));self.assertEqual(b.unit,'100_KG_NET_MASS')
        self.assertEqual(b.source_cell_index,1651)
        self.assertIsNone(c.value);self.assertIsNone(c.unit)
        self.assertEqual(c.value_status,'NO_SUPPLEMENTARY_UNIT');self.assertEqual(c.evidence_status,'Q')

    def test_zero_is_observed_not_missing(self):
        r=decode(sel=selection(flow='2'))[1]
        self.assertEqual(r.value,Decimal(0));self.assertEqual(r.value_status,'OBSERVED')

    def test_sparse_partner_absence_not_zero(self):
        for r in decode(sel=selection(partner='INT_EU27_2020')):
            self.assertIsNone(r.value)

    def test_confidential_inapplicable_and_absent_are_distinct(self):
        rows={r.metric:r for r in decode(sel=selection(ref.PRODUCTION_SOURCE))}
        self.assertEqual(rows['PRODVAL'].source_flag,':C')
        self.assertEqual(rows['PRODVAL'].source_flag_cell_index,1)
        self.assertEqual(rows['PRODVAL'].value_status,'CONFIDENTIAL')
        self.assertEqual(rows['PRODQNT'].source_flag,'-')
        self.assertEqual(rows['PRODQNT'].value_status,'NOT_APPLICABLE')
        self.assertEqual(rows['SCPRODVAL'].value_status,'MISSING')
        self.assertIsNone(rows['PRODQNT'].unit)
        self.assertEqual(rows['IMPVAL'].value,Decimal(29))

    def test_never_coerce_flag_into_numeric_value(self):
        o=fixture();o['value']['1650']=':C'
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_confidential_cell_must_not_carry_number(self):
        o=fixture(ref.PRODUCTION_SOURCE);o['value']['0']=100
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o,selection(ref.PRODUCTION_SOURCE))

    def test_no_mass_to_supplementary_quantity_substitution(self):
        o=fixture();o['value']['1652']=4.25
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_no_historical_piece_unit(self):
        o=fixture(ref.PRODUCTION_SOURCE);o['value']['6']='P/ST'
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o,selection(ref.PRODUCTION_SOURCE))

    def test_unreviewed_flags_fail_closed(self):
        o=fixture(ref.PRODUCTION_SOURCE);o['value']['1']=':E'
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o,selection(ref.PRODUCTION_SOURCE))

    def test_status_object_is_not_ignored(self):
        o=fixture();o['status']={'1650':'p'}
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_wrong_native_dimensions_fail(self):
        o=fixture();o['id']=list(reversed(o['id']))
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_wrong_dataset_or_vintage_fail(self):
        for key,value in [('updated','2026-01-01'),('source','OTHER'),('class','collection')]:
            o=fixture();o[key]=value
            with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_axis_index_must_be_bijective(self):
        o=fixture();o['dimension']['partner']['category']['index']['WORLD']=0
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_bool_axis_size_forbidden(self):
        o=copy.deepcopy(fixture());o['size'][0]=True
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_bool_axis_index_forbidden(self):
        o=fixture();o['dimension']['freq']['category']['index']['A']=False
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_out_of_range_or_noncanonical_sparse_keys_fail(self):
        for key in ('999999','-1','01','1.5'):
            o=fixture();o['value'][key]=1
            with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_wrong_indicator_order_fails(self):
        o=fixture();a=o['dimension']['indicators']['category']['index']
        a['VALUE_IN_EUROS'],a['QUANTITY_IN_100KG']=1,0
        with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_negative_bool_nonfinite_values_fail(self):
        for value in (-1,True,float('inf')):
            o=fixture();o['value']['1650']=value
            with self.assertRaises(ref.SupplySourceReferenceError):decode(o)

    def test_duplicate_json_keys_fail(self):
        data=json.dumps(fixture()).replace('"version": "2.0"','"version":"2.0","version":"2.0"')
        with self.assertRaises(ref.SupplySourceReferenceError):ref._decode(data,selection(),ref.PINS[ref.TRADE_SOURCE])

    def test_exact_hash_and_size_gate(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p=Path(d)/'synthetic.json';p.write_text(json.dumps(fixture()))
            with self.assertRaises(ref.SupplySourceReferenceError):ref.read_supply_reference(p,selection())

    def test_pinned_entrypoint_synthetic_positive(self):
        data=json.dumps(fixture()).encode();pins=copy.deepcopy(ref.PINS)
        pins[ref.TRADE_SOURCE].update(byte_count=len(data),sha256=hashlib.sha256(data).hexdigest())
        with tempfile.TemporaryDirectory() as d,patch.object(ref,'PINS',pins),patch.object(ref,'source_manifest'):
            p=Path(d)/'synthetic.json';p.write_bytes(data)
            r=ref.read_supply_reference(p,selection())
            self.assertEqual(r.records[0].value,123)
            with self.assertRaises(FrozenInstanceError):r.records[0].value=999

    def test_manifest_cannot_promote_or_repin(self):
        original=ref.source_manifest()
        for key in ('raw_storage_policy','model_use_status','national_supply_capacity_status'):
            m=copy.deepcopy(original);m[key]='APPROVED'
            with patch.object(Path,'read_text',return_value=json.dumps(m)),self.assertRaises(ref.SupplySourceReferenceError):ref.source_manifest()
        m=copy.deepcopy(original);m['source_artifacts'][0]['sha256']='0'*64
        with patch.object(Path,'read_text',return_value=json.dumps(m)),self.assertRaises(ref.SupplySourceReferenceError):ref.source_manifest()

    def test_reference_keeps_capacity_and_import_share_unknown(self):
        r=ref.SupplyReference(selection(),decode());s=ref.reference_summary(r)
        self.assertIsNone(s['national_capacity_or_import_share'])
        self.assertEqual(s['cross_source_substitution'],'FORBIDDEN')

    def test_ignored_output_receipt_and_no_overwrite(self):
        r=ref.SupplyReference(selection(),decode())
        base=ref.ROOT/'data/interim';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            s=write_reference(r,Path(d)/'private')
            self.assertEqual(s['record_count'],3)
            self.assertEqual(s['observed_numeric_cells'],2)
            self.assertEqual(s['normalized_storage_policy'],'EXTERNAL_ONLY_NOT_FOR_PUBLIC_COMMIT')
            with self.assertRaises(ref.SupplySourceReferenceError):write_reference(r,Path(d)/'private')

    def test_ignored_output_normalizes_lexical_parent_alias(self):
        base=ref.ROOT/'data/interim';base.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=base) as d:
            path=Path(d)/'nested/../result'
            self.assertEqual(guard_private_output(path),Path(d)/'result')

    def test_public_repo_output_rejected(self):
        with self.assertRaises(ref.SupplySourceReferenceError):guard_private_output(ref.ROOT/'evidence/test')

    def test_other_git_checkout_output_rejected(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            (Path(d)/'.git').mkdir()
            with self.assertRaises(ref.SupplySourceReferenceError):guard_private_output(Path(d)/'data')

    def test_symlinked_output_rejected(self):
        with tempfile.TemporaryDirectory(dir='/tmp') as d:
            p=Path(d);(p/'real').mkdir();(p/'link').symlink_to(p/'real')
            with self.assertRaises(ref.SupplySourceReferenceError):guard_private_output(p/'link'/'child')


if __name__ == '__main__':
    unittest.main()
