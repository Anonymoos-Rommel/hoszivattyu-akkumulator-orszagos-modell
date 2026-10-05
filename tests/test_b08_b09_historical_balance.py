"""Synthetic contract/negative tests; no original numeric panels are committed."""
import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

from modules.B08 import historical_source_balance as balance
from modules.B09 import gui_generation_reference as generation

D = Decimal
NAMES = sorted(generation.PSR_CODES)
COLUMNS = {generation.PSR_CODES[name]: i + 2 for i, name in enumerate(NAMES)}
ARTIFACT = generation.SourceArtifact(generation.GENERATION_ID, generation.ENTSOE_SOURCE_ID,
                                     'synthetic.xlsx', 'a' * 64, 1, 3)
LOAD_ARTIFACT = generation.SourceArtifact(balance.LOAD_ID, balance.LOAD_SOURCE_ID,
                                          'synthetic-load.xlsx', 'd' * 64, 1, 3)
OP = generation.SourceArtifact(generation.OPERATIONAL_IDS[0], generation.MAVIR_NET_OPERATIONAL_SOURCE_ID,
                               'synthetic-operation.xlsx', 'b' * 64, 1, 3)
END = balance.START + 3 * balance.STEP


def load_rows(values=('14', '14', '7')):
    rows = [(1, {1: 'Total Load - Day-ahead / Actual'}),
            (2, {1: 'Actual Total Load [6.1.A]'}),
            (3, {1: 'Day-ahead Total Load Forecast [6.1.B]'}),
            (4, {1: '01/01/2025 00:00 - 01/01/2026 00:00 (UTC)'}),
            (6, {1: 'MTU', 2: 'BZN|HU', 3: 'BZN|HU'}),
            (7, {1: 'MTU', 2: 'Actual Total Load (MW)', 3: 'Day-ahead Total Load Forecast (MW)'})]
    for i, value in enumerate(values):
        start = balance.START + i * balance.STEP
        mtu = start.strftime('%d/%m/%Y %H:%M') + ' - ' + (start + balance.STEP).strftime('%d/%m/%Y %H:%M')
        rows.append((i + 8, {1: mtu, 2: value, 3: '999999'}))
    return rows


def generation_rows(count=3):
    rows = [(1, {1: 'Actual Generation per Production Type - Generation'}),
            (2, {1: 'Aggregated Generation per Type [16.1.B&C]'}),
            (3, {1: '01/01/2025 00:00 - 01/01/2026 00:00 (UTC)'}),
            (5, {1: 'MTU', **{i + 2: 'BZN|HU' for i in range(21)}}),
            (6, {1: 'MTU', **{i + 2: name + ' (MW)' for i, name in enumerate(NAMES)}})]
    for i in range(count):
        start = balance.START + i * balance.STEP
        mtu = start.strftime('%d/%m/%Y %H:%M:%S') + ' - ' + (start + balance.STEP).strftime('%d/%m/%Y %H:%M:%S')
        row = {1: mtu, **{col: 'n/e' if code in balance.STRUCTURAL else '1' for code, col in COLUMNS.items()}}
        rows.append((i + 7, row))
    return rows


def runtime_rows(genrows, recoveries):
    result = []
    for n, source in genrows[5:]:
        timestamp = balance.START + (n - 7) * balance.STEP
        for code in balance.ACTIVE:
            cell = generation._column_name(COLUMNS[code]) + str(n)
            recovery = recoveries.get((timestamp, code))
            value = recovery.value_mw if recovery else D(source[COLUMNS[code]])
            selected = recovery.copies[0] if recovery else ('', '', '')
            result.append({
                'start_utc': timestamp.isoformat(), 'end_utc': (timestamp + balance.STEP).isoformat(),
                'timestep_hours': '0.25', 'production_type_code': code,
                'delivered_generation_kw': str(float(max(value, D(0))) * 1000),
                'source_withdrawal_kw': str(float(max(-value, D(0))) * 1000),
                'net_generation_contribution_kw': str(float(value) * 1000),
                'boundary_id': 'SIGNED_NET_GENERATION_AC' if recovery else 'GENERATION_AC',
                'region_id': 'HUNGARY_CONTROL_AREA', 'region_scheme': 'ENTSOE_CONTROL_AREA',
                'truth_context': 'REAL', 'evidence_status': 'Q', 'evidence_tier': balance.EVIDENCE_TIER,
                'model_use_status': balance.SOURCE_MODEL_USE,
                'source_refs': generation.ENTSOE_SOURCE_ID + (';' + generation.MAVIR_NET_OPERATIONAL_SOURCE_ID if recovery else ''),
                'a75_acquisition_record_id': ARTIFACT.acquisition_record_id,
                'a75_sha256': ARTIFACT.sha256, 'a75_cell': cell,
                'selected_operational_acquisition_record_id': selected[0],
                'selected_operational_sha256': selected[1], 'selected_operational_cell': selected[2],
            })
    return result


def fixture():
    loads, genrows = load_rows(), generation_rows()
    cell = generation._column_name(COLUMNS['B04']) + '8'
    genrows[-2][1][COLUMNS['B04']] = ''
    recoveries = {(balance.START + balance.STEP, 'B04'):
                  balance.Recovery(D('-2'), cell, ((OP.acquisition_record_id, OP.sha256, 'E3'),))}
    return loads, genrows, runtime_rows(genrows, recoveries), recoveries


def consume(loads=None, genrows=None, runtime=None, recoveries=None):
    if loads is None:
        loads, genrows, runtime, recoveries = fixture()
    return list(balance._iter_balance(loads, genrows, runtime, recoveries, ARTIFACT, load_artifact=LOAD_ARTIFACT, end=END))


class ArithmeticAndBoundaryTests(unittest.TestCase):
    def test_signed_withdrawal_once_residual_signs_conservation_and_ties(self):
        rows = consume()
        self.assertEqual([r.signed_generation_mw for r in rows], [D(14), D(11), D(14)])
        self.assertEqual([r.source_reference_residual_mw for r in rows], [D(0), D(3), D(-7)])
        self.assertEqual(rows[1].source_withdrawal_mw, D(2))
        self.assertEqual(rows[1].actual_load_mw, D(14))
        self.assertTrue(all(r.evidence_status == 'DER' and r.evidence_tier == balance.EVIDENCE_TIER for r in rows))
        self.assertEqual(rows[0].load_source.sha256, LOAD_ARTIFACT.sha256)
        self.assertEqual(rows[0].generation_source.evidence_status, 'Q')
        self.assertEqual(rows[0].generation_source.raw_storage_policy, 'EXTERNAL_ONLY')
        result = balance._summarize(iter(rows), end=END)
        self.assertEqual({k: D(v) for k, v in result['energy_mwh'].items()}, {
            'load': D('8.75'), 'injection': D('10.25'), 'source_withdrawal': D('.5'),
            'signed_generation': D('9.75'), 'source_reference_residual': D('-1'),
            'positive_residual': D('.75'), 'negative_residual_magnitude': D('1.75')})
        self.assertEqual(result['counts']['zero_residual_intervals'], 1)
        self.assertEqual(result['counts']['negative_residual_intervals'], 1)
        self.assertEqual(len(result['peaks']['load_peak']['coincident_intervals']), 2)
        self.assertEqual(len(result['peaks']['generation_peak']['coincident_intervals']), 2)
        self.assertEqual(len(result['generation_by_type']['B01']['peak']['timestamps_utc']), 3)
        self.assertEqual(D(result['monthly_utc']['2025-01']['generation_by_type_mwh']['B04']), D(0))
        self.assertNotIn('B10', result['generation_by_type'])
        self.assertNotIn('B25', result['generation_by_type'])

    def test_native_decimal_precision_ignores_callers_decimal_context(self):
        loads, genrows, _, rec = fixture()
        genrows[-3][1][COLUMNS['B01']] = '1.23456789'
        runtime = runtime_rows(genrows, rec)
        with localcontext() as context:
            context.prec = 5
            result = balance._summarize(balance._iter_balance(loads, genrows, runtime, rec, ARTIFACT, load_artifact=LOAD_ARTIFACT, end=END), end=END)
        self.assertEqual(D(result['generation_by_type']['B01']['energy_mwh']), D('.8086419725'))

    def test_stream_yield_restores_caller_decimal_context(self):
        with localcontext() as context:
            context.prec = 11
            stream = balance._iter_balance(*fixture(), ARTIFACT, load_artifact=LOAD_ARTIFACT, end=END)
            next(stream)
            self.assertEqual(context.prec, 11)
            stream.close()

    def test_last_interval_end_and_exact_exclusive_boundary(self):
        rows = consume()
        self.assertEqual(rows[-1].start_utc, END - balance.STEP)
        self.assertEqual(rows[-1].end_utc, END)
        self.assertEqual(rows[0].start_utc, balance.START)

    def test_native_load_stream_keeps_final_four_utc_intervals(self):
        def rows():
            yield from load_rows()[:6]
            for index in range(35040):
                start = balance.START + index * balance.STEP
                label = start.strftime('%d/%m/%Y %H:%M') + ' - ' + (start + balance.STEP).strftime('%d/%m/%Y %H:%M')
                yield index + 8, {1: label, 2: '2', 3: '900'}
        final = []
        count = 0
        for row in balance._loads(rows()):
            count += 1
            if row[0] >= balance.END - 4 * balance.STEP:
                final.append(row)
        self.assertEqual(count, 35040)
        self.assertEqual(len(final), 4)
        self.assertEqual(final[-1][0] + balance.STEP, balance.END)
        self.assertEqual(final[-1][2], 'B35047')

    def test_short_long_duplicate_shifted_cross_year_and_duration_fail(self):
        for what in ('short_load', 'long_load', 'duplicate_load', 'shift_load', 'duration_load',
                     'short_generation', 'long_generation', 'shift_generation', 'duration_generation'):
            loads, genrows, runtime, rec = fixture()
            if what == 'short_load': loads.pop()
            elif what == 'long_load': loads.append((11, {1: 'extra', 2: '1', 3: '1'}))
            elif what == 'duplicate_load': loads[-1] = loads[-2]
            elif what == 'shift_load': loads[-1][1][1] = '01/01/2025 00:15 - 01/01/2025 00:30'
            elif what == 'duration_load': loads[-1][1][1] = '01/01/2025 00:30 - 01/01/2025 01:30'
            elif what == 'short_generation': genrows.pop()
            elif what == 'long_generation': genrows.append(copy.deepcopy(genrows[-1]))
            elif what == 'shift_generation': genrows[-1][1][1] = '31/12/2024 23:30:00 - 31/12/2024 23:45:00'
            elif what == 'duration_generation': genrows[-1][1][1] = '01/01/2025 00:30:00 - 01/01/2025 01:30:00'
            with self.subTest(what=what), self.assertRaises(ValueError):
                consume(loads, genrows, runtime, rec)

    def test_summary_rejects_truncation_reordering_and_type_loss(self):
        rows = consume()
        for bad in (rows[:-1], list(reversed(rows)),
                    [replace(rows[0], contributions=rows[0].contributions[:-1]), *rows[1:]]):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                balance._summarize(bad, end=END)


class ProductAndMissingnessTests(unittest.TestCase):
    def test_forecast_unit_grain_direction_and_type_header_rejected(self):
        cases = [('load', 1, 1, 'Day-ahead Total Load Forecast [6.1.B]'),
                 ('load', 5, 2, 'Day-ahead Total Load Forecast (MW)'),
                 ('load', 5, 2, 'Actual Total Load (kW)'),
                 ('load', 4, 2, 'BZN|AT'),
                 ('load', 3, 1, '01/01/2025 00:00 - 01/01/2026 00:00 (CET)'),
                 ('generation', 0, 1, 'Actual Generation per Production Type - Consumption'),
                 ('generation', 1, 1, 'Installed Generation Capacity Aggregated [14.1.A]'),
                 ('generation', 3, 2, 'BZN|AT'),
                 ('generation', 4, 2, 'Biomass (kW)'),
                 ('generation', 4, 3, 'Biomass (MW)')]
        for target, row, column, value in cases:
            loads, genrows, runtime, rec = fixture()
            (loads if target == 'load' else genrows)[row][1][column] = value
            with self.subTest(target=target, value=value), self.assertRaises(ValueError):
                consume(loads, genrows, runtime, rec)

    def test_load_missing_nonfinite_negative_and_cell_loss_rejected(self):
        for value in ('', 'n/e', 'NaN', 'Infinity', '-1'):
            loads, genrows, runtime, rec = fixture()
            loads[-1][1][2] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                consume(loads, genrows, runtime, rec)
        loads, genrows, runtime, rec = fixture()
        del loads[-1][1][2]
        with self.assertRaises(ValueError): consume(loads, genrows, runtime, rec)

    def test_generation_blank_nonfinite_negative_and_structural_zero_rejected(self):
        for code, value in (('B01', ''), ('B04', ''), ('B01', 'NaN'), ('B01', '-1'),
                            ('B01', 'n/e'), ('B10', '0'), ('B25', ''), ('B25', '1')):
            loads, genrows, runtime, rec = fixture()
            genrows[-1][1][COLUMNS[code]] = value
            with self.subTest(code=code, value=value), self.assertRaises(ValueError):
                consume(loads, genrows, runtime, rec)

    def test_no_overwrite_no_extra_recovery_and_exact_blank_locator(self):
        for what in ('overwrite', 'missing', 'wrong_cell', 'extra_key'):
            loads, genrows, runtime, rec = fixture()
            key = next(iter(rec))
            if what == 'overwrite': genrows[-2][1][COLUMNS['B04']] = '0'
            elif what == 'missing': rec.clear()
            elif what == 'wrong_cell': rec[key] = replace(rec[key], a75_cell='F999')
            elif what == 'extra_key': rec[(balance.START, 'B06')] = rec[key]
            with self.subTest(what=what), self.assertRaises(ValueError):
                consume(loads, genrows, runtime, rec)

    def test_runtime_cross_product_units_signs_and_provenance_rejected(self):
        fields = {'start_utc': '2025-01-01T00:15:00+00:00', 'end_utc': '2025-01-01T01:00:00+00:00',
                  'timestep_hours': '1', 'production_type_code': 'B25', 'region_id': 'PROGRAMME',
                  'region_scheme': 'NUTS2', 'truth_context': 'SCENARIO', 'evidence_status': 'OBS',
                  'evidence_tier': 'E1', 'model_use_status': 'OBS', 'source_refs': 'FORECAST',
                  'a75_acquisition_record_id': 'B08B09-P5-R04', 'a75_sha256': '0' * 64,
                  'a75_cell': 'A7', 'boundary_id': 'SIGNED_NET_GENERATION_AC',
                  'selected_operational_cell': 'E3', 'delivered_generation_kw': '1',
                  'source_withdrawal_kw': '1', 'net_generation_contribution_kw': '-1000'}
        for field, value in fields.items():
            loads, genrows, runtime, rec = fixture()
            runtime[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                consume(loads, genrows, runtime, rec)

    def test_runtime_missing_extra_or_duplicate_record_rejected(self):
        for mutation in (lambda rows: rows.pop(), lambda rows: rows.append(rows[-1]),
                         lambda rows: rows.insert(1, rows[0])):
            loads, genrows, runtime, rec = fixture()
            mutation(runtime)
            with self.assertRaises(ValueError): consume(loads, genrows, runtime, rec)

    def test_recovery_sign_flip_and_double_leg_fail_closed(self):
        for mutate in (lambda r: r.update(source_withdrawal_kw='-2000'),
                       lambda r: r.update(delivered_generation_kw='2000', net_generation_contribution_kw='0'),
                       lambda r: r.update(net_generation_contribution_kw='2000')):
            loads, genrows, runtime, rec = fixture()
            row = next(r for r in runtime if r['boundary_id'] == 'SIGNED_NET_GENERATION_AC')
            mutate(row)
            with self.assertRaises(ValueError): consume(loads, genrows, runtime, rec)


class RecoveryAndPinTests(unittest.TestCase):
    def lineage(self):
        return {'start_utc': balance.START.isoformat(), 'production_type_code': 'B04',
                'a75_acquisition_record_id': ARTIFACT.acquisition_record_id, 'a75_sha256': ARTIFACT.sha256,
                'a75_cell': generation._column_name(COLUMNS['B04']) + '7', 'source_signed_power_mw': '-0.0123',
                'operational_acquisition_record_id': OP.acquisition_record_id,
                'operational_sha256': OP.sha256, 'operational_cell': 'E2', 'selected_for_recovery': 'True'}

    def test_exact_decimal_recovery_and_copy_selection(self):
        first = self.lineage()
        second_artifact = replace(OP, acquisition_record_id=generation.OPERATIONAL_IDS[1], sha256='c' * 64)
        second = dict(first, operational_acquisition_record_id=second_artifact.acquisition_record_id,
                      operational_sha256=second_artifact.sha256, selected_for_recovery='False')
        artifacts = {a.acquisition_record_id: a for a in (ARTIFACT, OP, second_artifact)}
        recovered = balance._read_recovery([second, first], artifacts)[balance.START, 'B04']
        self.assertEqual(recovered.value_mw, D('-0.0123'))
        self.assertEqual([x[0] for x in recovered.copies], list(generation.OPERATIONAL_IDS[:2]))
        for mutate in (lambda r: r.update(source_signed_power_mw='0.0123'),
                       lambda r: r.update(selected_for_recovery='True'),
                       lambda r: r.update(a75_cell='F9')):
            bad = second.copy()
            mutate(bad)
            with self.assertRaises(ValueError): balance._read_recovery([first, bad], artifacts)

    def test_lineage_drift_is_rejected(self):
        artifacts = {a.acquisition_record_id: a for a in (ARTIFACT, OP)}
        mutations = {'start_utc': '2024-12-31T23:45:00+00:00', 'production_type_code': 'B10',
                     'a75_acquisition_record_id': 'B08B09-P5-R04', 'a75_sha256': '0' * 64,
                     'operational_acquisition_record_id': 'B09-P6-OP99', 'operational_sha256': '0' * 64,
                     'operational_cell': 'G2', 'selected_for_recovery': 'maybe', 'source_signed_power_mw': 'NaN'}
        for key, value in mutations.items():
            row = dict(self.lineage(), **{key: value})
            with self.subTest(key=key), self.assertRaises(ValueError): balance._read_recovery([row], artifacts)
        with self.assertRaises(ValueError): balance._read_recovery([self.lineage()] * 2, artifacts)

    def test_recovery_original_replay_requires_matching_end_timestamp_cell_and_number(self):
        artifacts = {key: replace(OP, acquisition_record_id=key, data_rows=1)
                     for key in generation.OPERATIONAL_IDS}
        source_rows = [(1, dict(enumerate(generation.MAVIR_HEADERS, 1))),
                       (2, {1: '2025.01.01 01:15:00 +0100', 5: '-0.0123'})]
        recovery = balance.Recovery(D('-0.0123'), 'F7', ((OP.acquisition_record_id, OP.sha256, 'E2'),))
        paths = {key: Path(key) for key in artifacts}
        with patch.object(generation, '_xlsx_rows', side_effect=lambda *args: iter(source_rows)):
            balance._verify_recovery_originals(paths, artifacts, {(balance.START, 'B04'): recovery})
        for column, value in ((1, '2025.01.01 01:00:00 +0100'), (5, '0.0123'), (5, '')):
            bad = copy.deepcopy(source_rows)
            bad[1][1][column] = value
            with self.subTest(column=column, value=value), \
                    patch.object(generation, '_xlsx_rows', side_effect=lambda *args: iter(bad)), \
                    self.assertRaises(ValueError):
                balance._verify_recovery_originals(paths, artifacts, {(balance.START, 'B04'): recovery})

    def test_recovery_original_replay_cannot_lose_requested_copy_locator(self):
        artifacts = {key: replace(OP, acquisition_record_id=key, data_rows=1)
                     for key in generation.OPERATIONAL_IDS}
        rows = [(1, dict(enumerate(generation.MAVIR_HEADERS, 1))),
                (2, {1: '2025.01.01 00:15:00 +0000', 5: '-0.0123'})]
        recovery = balance.Recovery(D('-0.0123'), 'F7', ((OP.acquisition_record_id, OP.sha256, 'E3'),))
        with patch.object(generation, '_xlsx_rows', side_effect=lambda *args: iter(rows)), self.assertRaises(ValueError):
            balance._verify_recovery_originals({key: Path(key) for key in artifacts}, artifacts,
                                               {(balance.START, 'B04'): recovery})

    def test_exact_handoff_hash_and_size_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.csv'
            path.write_text('a,b\n1,2\n')
            content = path.read_bytes()
            pin = {'sha256': hashlib.sha256(content).hexdigest(), 'bytes': len(content)}
            with balance._pinned_csv(path, pin) as rows:
                self.assertEqual(list(rows), [{'a': '1', 'b': '2'}])
            for changed in (dict(pin, sha256='0' * 64), dict(pin, bytes=1)):
                with self.assertRaises(ValueError), balance._pinned_csv(path, changed): pass
            path.write_text('a,b\n1,3\n')
            with self.assertRaises(ValueError), balance._pinned_csv(path, pin): pass

    def test_public_fixed_contract_source_pins_and_evidence(self):
        contract, artifacts = balance._contract()
        self.assertEqual(len(artifacts), 8)
        self.assertEqual(contract['evidence_status'], 'DER')
        self.assertEqual(contract['source_evidence']['generation']['record_evidence_status'], 'Q')
        self.assertFalse(contract['coverage_limits']['complete_budapest_civil2025'])
        self.assertFalse(contract['coverage_limits']['complete_meteorological_winter'])
        with self.assertRaisesRegex(ValueError, 'eight'):
            list(balance.iter_historical_source_balance({}, {}))

    def test_contract_policy_grain_unit_time_type_and_source_drift_rejected(self):
        base = json.loads(balance.MANIFEST.read_text())
        changes = [lambda m: m.update(evidence_status='OBS'),
                   lambda m: m.update(evidence_tier='E1'),
                   lambda m: m.update(raw_storage_policy='PUBLIC'),
                   lambda m: m.update(public_raw_reuse_status='FREE'),
                   lambda m: m.update(source_model_use_status='OBS'),
                   lambda m: m.update(model_use_status='PROGRAMME_READY'),
                   lambda m: m.update(spatial_grain='NUTS2'),
                   lambda m: m.update(source_power_unit='kW'),
                   lambda m: m.update(end_utc_exclusive='2025-12-31T23:00:00+00:00'),
                   lambda m: m.update(resolution='PT60M'),
                   lambda m: m['active_production_type_codes'].append('B25'),
                   lambda m: m['source_artifacts'][0].update(sha256='0' * 64),
                   lambda m: m['source_artifacts'][0].update(source_id='FORECAST'),
                   lambda m: m['handoffs'].pop('generation'),
                   lambda m: m['handoffs']['generation'].update(sha256='0' * 64),
                   lambda m: m['source_evidence']['generation'].update(record_evidence_status='OBS'),
                   lambda m: m['coverage_limits'].update(complete_budapest_civil2025=True),
                   lambda m: m['authority_sha256'].pop('modules/B09/engine.py')]
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                manifest = copy.deepcopy(base)
                change(manifest)
                path = Path(directory) / 'manifest.json'
                path.write_text(json.dumps(manifest))
                with patch.object(balance, 'MANIFEST', path), self.assertRaises(ValueError): balance._contract()

    def test_civil_companion_cannot_be_generation_or_timestamp_shift(self):
        _, artifacts = balance._contract()
        row = {'start_utc': balance.START.isoformat(), 'end_utc': (balance.START + balance.STEP).isoformat(),
               'timestep_hours': '0.25', 'source_id': balance.LOAD_SOURCE_ID,
               'source_revision': balance.LOAD_ID + ':' + artifacts[balance.LOAD_ID].sha256,
               'evidence_status': 'DER', 'evidence_tier': balance.EVIDENCE_TIER, 'actual_load_mw': '1'}
        self.assertEqual(balance._civil_row(row, balance.START, artifacts), D(1))
        for key, value in (('source_id', generation.ENTSOE_SOURCE_ID), ('timestep_hours', '1'),
                           ('source_revision', balance.COMPANION_ID + ':' + artifacts[balance.COMPANION_ID].sha256)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                balance._civil_row(dict(row, **{key: value}), balance.START, artifacts)


if __name__ == '__main__':
    unittest.main()
