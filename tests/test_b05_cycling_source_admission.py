"""Source admission is distinct from preserved P18 conditional arithmetic."""
import csv
from datetime import date
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest

from modules.B05.manufacturer_wm50_reference import load_wm50_reference
from modules.B05.qualified_cycling_point import (
    CONDITIONAL_POINT, SOURCE_JOIN_REQUIRED, CyclingSourceContext,
    QualifiedCyclingPoint, evaluate_conditional_cycling_point,
    evaluate_exact_cycling_point,
)
from modules.B05.cycling_input_colocation import MEASUREMENT_DETERMINED

ROOT = Path(__file__).resolve().parents[1]


# This pins one technical revision, not a new source-admission authority.
REVISION_PROOF_PATH = 'registry/b05_independent_contract_current_revision_20261029.json'
REVISION_PROOF_SHA256 = '87dbe6185f262eaabe5f942a8c4356e605fb4283457cc90bb7aaf5a6c027dbc9'
INDEPENDENT_HISTORY_PATH = 'evidence/history/B05-CYCLING-ADMISSION-2026-10-02/manifest.json'
B06_CURRENT_PATH = 'modules/B06/prospective_capacity_reference.py'
B06_INPUT_MANIFEST_PATH = 'registry/b06_prospective_capacity_reference_manifest.json'


def _revision_require(condition, message):
    if not condition:
        raise ValueError(message)


def _revision_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _revision_require(key not in result, 'duplicate JSON key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def verify_independent_contract_revision(read_bytes):
    """Offline exact-byte proof; read_bytes permits isolated negative fixtures only.

    The historical checkpoint asserted 17 then-current files unchanged. That
    literal current-byte invariant is superseded for precisely one reviewed B06
    revision; historical bytes and the other 16 current pins remain unchanged.
    No production source admission, Q, readiness or physical formula is altered.
    """
    import re
    digest = lambda raw: hashlib.sha256(raw).hexdigest()
    raw = read_bytes(REVISION_PROOF_PATH)
    _revision_require(digest(raw) == REVISION_PROOF_SHA256, 'reviewed proof raw hash')
    proof = _revision_json(raw)
    _revision_require(set(proof) == {'schema_version', 'revision_id', 'date', 'purpose',
                                  'history', 'transition', 'input_manifest', 'limitations'}, 'proof fields')
    _revision_require(proof['schema_version'] == 1 and
                      proof['revision_id'] == 'B05-INDEPENDENT-CONTRACT-CURRENT-REVISION-20261029' and
                      proof['date'] == '2026-10-29' and
                      proof['purpose'] == 'TECHNICAL_CURRENT_REVISION_ONLY_NOT_PHYSICAL_SOURCE_ADMISSION',
                      'technical revision identity')
    _revision_require(proof['limitations'] == [
        'EXACT_SINGLE_REVISION_NO_AUTOMATIC_REPINNING', 'SIXTEEN_OTHER_CURRENT_CONTRACTS_RAW_IDENTICAL',
        'NO_PHYSICAL_ADMISSION_Q_OR_READINESS_CHANGE', 'B06_REMAINS_SCN_CAPACITY_ONLY'], 'revision scope')
    history_pin, transition, manifest_pin = proof['history'], proof['transition'], proof['input_manifest']
    _revision_require(set(history_pin) == {'path', 'sha256', 'contract_count'} and
                      history_pin['path'] == INDEPENDENT_HISTORY_PATH and
                      history_pin['contract_count'] == 17, 'history contract')
    _revision_require(set(transition) == {'path', 'predecessor_sha256', 'current_sha256', 'old_assignment',
                                        'new_assignment', 'old_pin_set_sha256', 'current_pin_set_sha256'} and
                      transition['path'] == B06_CURRENT_PATH, 'single exact transition')
    _revision_require(set(manifest_pin) == {'path', 'predecessor_sha256', 'current_sha256', 'changed_input',
                                          'old_method_sha256', 'current_method_sha256'} and
                      manifest_pin['path'] == B06_INPUT_MANIFEST_PATH and
                      manifest_pin['changed_input'] == 'ventilation_method', 'single input transition')
    history_raw = read_bytes(INDEPENDENT_HISTORY_PATH)
    _revision_require(digest(history_raw) == history_pin['sha256'], 'historical manifest raw hash')
    history = _revision_json(history_raw)['unchanged_independent_contracts']
    _revision_require(len(history) == 17 and B06_CURRENT_PATH in history and
                      history[B06_CURRENT_PATH] == transition['predecessor_sha256'], '17 historical pins')
    for path, expected in history.items():
        if path != B06_CURRENT_PATH:
            _revision_require(digest(read_bytes(path)) == expected, 'unchanged current contract: ' + path)

    current = read_bytes(B06_CURRENT_PATH)
    _revision_require(digest(current) == transition['current_sha256'], 'exact current B06 raw hash')
    old_pin = transition['old_pin_set_sha256'].encode('ascii')
    new_pin = transition['current_pin_set_sha256'].encode('ascii')
    old_assignment = transition['old_assignment'].encode('ascii')
    new_assignment = transition['new_assignment'].encode('ascii')
    assignments = re.findall(rb"^PIN_SET_SHA256 = '[0-9a-f]{64}'\r?$", current, re.M)
    _revision_require(assignments == [new_assignment] and current.count(new_pin) == 1 and
                      old_pin not in current and old_assignment == new_assignment.replace(new_pin, old_pin),
                      'one anchored exact assignment, no old literal')
    predecessor = current.replace(new_assignment, old_assignment, 1)
    _revision_require(digest(predecessor) == transition['predecessor_sha256'], 'entire B06 predecessor bytes')

    manifest_raw = read_bytes(B06_INPUT_MANIFEST_PATH)
    _revision_require(digest(manifest_raw) == manifest_pin['current_sha256'], 'exact current input manifest')
    old_method = manifest_pin['old_method_sha256'].encode('ascii')
    new_method = manifest_pin['current_method_sha256'].encode('ascii')
    _revision_require(manifest_raw.count(new_method) == 1 and old_method not in manifest_raw,
                      'one exact method pin delta')
    old_manifest_raw = manifest_raw.replace(new_method, old_method, 1)
    _revision_require(digest(old_manifest_raw) == manifest_pin['predecessor_sha256'], 'entire manifest predecessor bytes')
    manifest, old_manifest = _revision_json(manifest_raw), _revision_json(old_manifest_raw)
    _revision_require(manifest['inputs']['ventilation_method']['sha256'] == new_method.decode(), 'method pin')
    expected_old = _revision_json(manifest_raw)
    expected_old['inputs']['ventilation_method']['sha256'] = old_method.decode()
    _revision_require(old_manifest == expected_old, 'only method pin changed')
    for value, expected in ((manifest, new_pin), (old_manifest, old_pin)):
        canonical = json.dumps(value['inputs'], sort_keys=True, separators=(',', ':')).encode()
        _revision_require(digest(canonical) == expected.decode(), 'canonical input pin set')
    for name, pin in manifest['inputs'].items():
        _revision_require(digest(read_bytes(pin['path'])) == pin['sha256'], 'current input raw hash: ' + name)


def point(**changes):
    context = CyclingSourceContext(
        observation_id="WM50-20261002-average-low_temperature-A7",
        source_id="SRC-B05-HPKEYMARK-MITSUBISHI-WM50-2026",
        document_revision="037-0032-20 / rev.2; certification date 2023-12-19",
        component="Outdoor", climate="average", application="low_temperature",
    )
    p = QualifiedCyclingPoint(
        "PUZ-WM50VHA", "PUZ-WM50VHA(-BS)", 7, 35, 1.8, .33, 5.46,
        .95, MEASUREMENT_DETERMINED, True, True,
        minimum_source_id="SRC-B05-MITSUBISHI-PUZ-WM-MINNOMMAX-2024",
        source_context=context,
        minimum_document_revision="2024 technical sheet rev.1",
    )
    return replace(p, **changes)


class CyclingSourceAdmissionTests(unittest.TestCase):
    def rejected(self, p):
        result = evaluate_exact_cycling_point(p, required_capacity_kw=.9)
        self.assertEqual(result.status, SOURCE_JOIN_REQUIRED)
        self.assertIsNone(result.cop_bin)
        self.assertIsNone(result.electrical_input_kw)
        return result.residual_gaps

    def test_conditional_arithmetic_preserves_both_coefficients_without_admission(self):
        for cdh, cop, input_kw in ((.95, 5.2, .17307692307692307),
                                   (.98, 5.352941176470588, .16813186813186815)):
            with self.subTest(cdh=cdh):
                result = evaluate_conditional_cycling_point(point(cdh=cdh), required_capacity_kw=.9)
                self.assertEqual(result.status, CONDITIONAL_POINT)
                self.assertEqual(result.capacity_ratio, .5)
                self.assertAlmostEqual(result.cop_bin, cop, places=12)
                self.assertAlmostEqual(result.electrical_input_kw, input_kw, places=12)
                self.rejected(point(cdh=cdh))

    def test_p20_current_observation_does_not_prove_test_water_or_join(self):
        gaps = self.rejected(point())
        for gap in ("TEST_WATER_CONTROL_AUTHORITY_REQUIRED", "TEST_WATER_TEMPERATURE_C_AUTHORITY_REQUIRED",
                    "SOURCE_BOUND_TEST_CONDITION_AUTHORITY_REQUIRED", "SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED"):
            self.assertIn(gap, gaps)

    def test_missing_and_mismatched_scope_never_admits(self):
        context = point().source_context
        alternatives = dict(source_id="OTHER-SOURCE", document_revision="037-0032-20 / rev.1",
                            component="Outdoor+Indoor", climate="warmer", application="medium_temperature",
                            test_water_control="fixed", test_water_temperature_c=35)
        for field, wrong in alternatives.items():
            for value in (None, wrong):
                with self.subTest(field=field, value=value):
                    gaps = self.rejected(point(source_context=replace(context, **{field: value})))
                    prefix = field.upper()
                    self.assertTrue(any(g.startswith(prefix) for g in gaps))
        self.rejected(point(source_context=None))
        self.rejected(point(source_context=replace(context, observation_id="invented")))

    def test_temperature_model_and_current_value_mismatch_are_explicit(self):
        for changes, gap in ((dict(outdoor_temperature_c=2), "OUTDOOR_TEMPERATURE_MISMATCH"),
                             (dict(supply_temperature_c=55), "EXACT_WATER_COORDINATE_AUTHORITY_REQUIRED"),
                             (dict(certified_model_identifier="PUZ-WM50VHA+INDOOR"), "CERTIFIED_MODEL_MISMATCH"),
                             (dict(cdh=.98), "CDH_VALUE_MISMATCH")):
            with self.subTest(changes=changes):
                self.assertIn(gap, self.rejected(point(**changes)))

    def test_switching_to_correct_warmer_value_still_cannot_admit(self):
        context = replace(point().source_context,
                          observation_id="WM50-20261002-warmer-low_temperature-A7",
                          climate="warmer", test_water_control="fixed", test_water_temperature_c=35)
        gaps = self.rejected(point(cdh=.98, source_context=context))
        self.assertNotIn("CDH_VALUE_MISMATCH", gaps)
        self.assertIn("SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED", gaps)

    def test_all_four_p22_rows_keep_independent_facts_and_fail_source_join(self):
        with (ROOT / "data/processed/b05_p22_mitsubishi_w35_cycling_bins.csv").open() as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            context = replace(point().source_context, observation_id=row["current_source_observation_id"])
            p = point(outdoor_temperature_c=float(row["outdoor_temperature_C"]),
                      minimum_capacity_kw=float(row["min_modulation_kW"]),
                      declared_minimum_cop=float(row["min_point_COP"]),
                      minimum_input_kw=float(row["min_modulation_kW"])/float(row["min_point_COP"]),
                      cdh=float(row["Cdh_Tj"]), minimum_source_id=row["min_source_id"], source_context=context)
            self.rejected(p)
            result = evaluate_conditional_cycling_point(p, required_capacity_kw=.9)
            self.assertEqual(result.status, CONDITIONAL_POINT)
            self.assertGreater(result.electrical_input_kw, 0)

    def dimplex_point(self, row):
        return QualifiedCyclingPoint(
            manufacturer_model_identifier="LA 2030CP", certified_model_identifier="LA 2030CP",
            outdoor_temperature_c=float(row["outdoor_temperature_C"]), supply_temperature_c=35,
            minimum_capacity_kw=float(row["min_capacity_kW"]), minimum_input_kw=float(row["min_input_kW"]),
            declared_minimum_cop=float(row["min_COP"]),
            cdh={-7: .99, 2: .97, 7: .953, 12: .912}[int(row["outdoor_temperature_C"])],
            cdh_status=MEASUREMENT_DETERMINED, identity_correlated=True, point_pairing_explicit=True,
            minimum_source_id="SRC-B05-DIMPLEX-LA2030CP-DETAILED-MIN-SURFACE-2026",
            minimum_document_revision="System C Version 03/2026",
            source_context=CyclingSourceContext(
                observation_id="LA2030CP-20261002-average-low_temperature-A" + row["outdoor_temperature_C"],
                source_id="SRC-B05-HPKEYMARK-DIMPLEX-LA2030CP-2026",
                document_revision="registration 40060852; certification date 2025-08-29; revision unstated",
                component="Outdoor", climate="average", application="low_temperature"),
        )

    def test_current_p42_facts_and_each_dimplex_physical_join_are_distinct(self):
        with (ROOT / "data/processed/b05_p42_coordinate_gap_closure.csv").open() as f:
            rows = [r for r in csv.DictReader(f) if r["row_id"] in
                    ("B05-P42-D04", "B05-P42-D05", "B05-P42-D06", "B05-P42-D07")]
        self.assertEqual(len(rows), 4)
        for row in rows:
            p = self.dimplex_point(row)
            with self.subTest(row=row["row_id"]):
                self.assertIn("SOURCE_BOUND_MINIMUM_POINT_JOIN_REQUIRED", self.rejected(p))
                load = p.minimum_capacity_kw / 2
                result = evaluate_conditional_cycling_point(p, required_capacity_kw=load)
                # Independent rearranged input oracle; no source admission follows.
                expected = (p.cdh * load + (1-p.cdh) * p.minimum_capacity_kw) / p.declared_minimum_cop
                self.assertEqual(result.status, CONDITIONAL_POINT)
                self.assertAlmostEqual(result.electrical_input_kw, expected, places=12)
                self.assertAlmostEqual(result.cop_bin * result.electrical_input_kw, load, places=12)
        a7 = next(r for r in rows if r["outdoor_temperature_C"] == "7")
        self.assertEqual((a7["min_capacity_kW"], a7["min_input_kW"], a7["min_COP"]), ("7.72", "1.41", "5.49"))
        a12 = next(r for r in rows if r["outdoor_temperature_C"] == "12")
        self.assertEqual((a12["min_capacity_kW"], a12["min_input_kW"], a12["min_COP"]), ("8.87", "1.32", "6.70"))

    def test_dimplex_caller_metadata_and_cross_product_or_revision_substitution_fail(self):
        with (ROOT / "data/processed/b05_p42_coordinate_gap_closure.csv").open() as f:
            row = next(r for r in csv.DictReader(f) if r["row_id"] == "B05-P42-D06")
        p = self.dimplex_point(row)
        for field, wrong in dict(climate="warmer", application="medium_temperature", component="Indoor",
                                 document_revision="40060852-old", test_water_control="fixed",
                                 test_water_temperature_c=35).items():
            for value in (None, wrong):
                with self.subTest(field=field, value=value):
                    gaps = self.rejected(replace(p, source_context=replace(p.source_context, **{field: value})))
                    self.assertTrue(any(g.startswith(field.upper()) for g in gaps))
        self.assertIn("CERTIFIED_MODEL_MISMATCH", self.rejected(replace(p, source_context=point().source_context)))
        self.assertIn("CURRENT_MANUFACTURER_REVISION_REQUIRED", self.rejected(replace(
            p, minimum_source_id="SRC-B05-DIMPLEX-LA2030CP-MIN-SURFACE-2026")))
        self.assertIn("MANUFACTURER_DOCUMENT_REVISION_MISMATCH", self.rejected(replace(
            p, minimum_document_revision="historical P23 summary")))
        self.assertIn("MANUFACTURER_DOCUMENT_REVISION_REQUIRED", self.rejected(replace(
            p, minimum_document_revision=None)))
        # The correct source ID cannot transfer to another manufacturer's point.
        self.assertIn("MANUFACTURER_MODEL_MISMATCH", self.rejected(replace(
            point(), minimum_source_id=p.minimum_source_id, minimum_document_revision=p.minimum_document_revision)))

    def test_invalid_numeric_inputs_do_not_hide_behind_unknown_source(self):
        for changes in (dict(minimum_capacity_kw=float("nan")), dict(cdh=float("inf")),
                        dict(outdoor_temperature_c=float("nan")), dict(minimum_input_kw=0)):
            for evaluate in (evaluate_exact_cycling_point, evaluate_conditional_cycling_point):
                with self.subTest(changes=changes, evaluate=evaluate.__name__):
                    with self.assertRaises(ValueError): evaluate(point(**changes), required_capacity_kw=.9)
        for load in (0, -1, 1.8, 2, float("nan"), float("inf")):
            with self.assertRaises(ValueError): evaluate_conditional_cycling_point(point(), required_capacity_kw=load)

    def test_source_manifest_keeps_revision_limitation_and_no_invented_byte_hash(self):
        manifest = json.loads((ROOT / "registry/b05_cycling_source_admission_manifest.json").read_text())
        self.assertEqual(len(manifest["sources"]), 2)
        self.assertTrue(all(s["sha256"] is None for s in manifest["sources"]))
        self.assertTrue(all(s["repo_snapshot_path"] is None for s in manifest["sources"]))
        self.assertEqual(manifest["historical_claim"]["climate"], "warmer")
        self.assertEqual(manifest["historical_claim"]["status"], "CURRENT_CORROBORATION_MISMATCH_HISTORICAL_CAUSE_UNRESOLVED")
        self.assertTrue(all(o["admitted_minimum_point_join"] is None for o in manifest["observations"]))
        self.assertTrue(all(o["test_water_control"] is None for o in manifest["observations"]))

    def test_manifest_source_ids_dates_and_current_revisions_are_consistent(self):
        manifest = json.loads((ROOT / "registry/b05_cycling_source_admission_manifest.json").read_text())
        with (ROOT / "registry/sources.csv").open() as f:
            registered = {r["source_id"] for r in csv.DictReader(f)}
        self.assertEqual(manifest["schema_version"], 2)
        sources = {r["source_id"]: r for r in manifest["sources"]}
        self.assertEqual(len(sources), len(manifest["sources"]))
        self.assertEqual(len(manifest["observations"]), 11)
        self.assertEqual(len({r["observation_id"] for r in manifest["observations"]}), 11)
        for source in sources.values():
            self.assertIn(source["source_id"], registered)
            self.assertEqual(date.fromisoformat(source["retrieved_at"]), date(2026, 10, 2))
            self.assertTrue(source["exact_component_locator"])
        for obs in manifest["observations"]:
            source = sources[obs["source_id"]]
            self.assertEqual(obs["observation_date"], source["retrieved_at"])
            for field in ("model_identifier", "component", "document_revision"):
                self.assertEqual(obs[field], source[field])
        for reference in manifest["current_manufacturer_revisions"]:
            self.assertIn(reference["source_id"], registered)
            self.assertTrue(reference["document_revision"])
        self.assertIn(manifest["method_condition_authority"]["source_id"], registered)

    def test_independent_v53_capacity_consumer_and_grid_bytes_are_unchanged(self):
        # Historical test ID retained; current acceptance is the exact reviewed transition.
        verify_independent_contract_revision(lambda path: (ROOT / path).read_bytes())
        minimum = load_wm50_reference("MIN", fixed_supply_c=55).evaluate(-7, 55).point
        maximum = load_wm50_reference("MAX", fixed_supply_c=55).evaluate(-7, 55).point
        self.assertEqual(minimum.thermal_capacity_kw, 2)
        self.assertEqual(maximum.thermal_capacity_kw, 4.4)
        self.assertEqual(minimum.cop, 1.76)

    def revision_bytes(self):
        read = lambda path: (ROOT / path).read_bytes()
        proof = json.loads(read(REVISION_PROOF_PATH))
        history = json.loads(read(INDEPENDENT_HISTORY_PATH))['unchanged_independent_contracts']
        inputs = json.loads(read(B06_INPUT_MANIFEST_PATH))['inputs']
        paths = {REVISION_PROOF_PATH, INDEPENDENT_HISTORY_PATH, B06_CURRENT_PATH, B06_INPUT_MANIFEST_PATH}
        paths.update(history)
        paths.update(pin['path'] for pin in inputs.values())
        return {path: read(path) for path in paths}, proof

    def reject_revision_mutation(self, changes, expected=None):
        files, _ = self.revision_bytes()
        files.update(changes)
        with self.assertRaisesRegex(ValueError, expected or '.'):
            verify_independent_contract_revision(files.__getitem__)

    def test_revision_positive_uses_same_offline_gate(self):
        files, _ = self.revision_bytes()
        verify_independent_contract_revision(files.__getitem__)

    def test_revision_rejects_other_source_bytes_and_assignment_mutations(self):
        files, proof = self.revision_bytes()
        current = files[B06_CURRENT_PATH]
        t = proof['transition']
        new, old = t['new_assignment'].encode(), t['old_assignment'].encode()
        mutations = [current + b'\n# unrelated change\n', current.replace(b'SCOPE_METADATA_SHA256', b'OTHER_METADATA_SHA256'),
                     current.replace(new, b''), current + b'\n' + new,
                     current.replace(new, old), current + t['current_pin_set_sha256'].encode(),
                     current.replace(new, b' ' + new), current.replace(new, new.replace(b' = ', b'=')),
                     current.replace(t['current_pin_set_sha256'].encode(), b'0' * 64)]
        for mutated in mutations:
            with self.subTest(sha256=hashlib.sha256(mutated).hexdigest()):
                self.reject_revision_mutation({B06_CURRENT_PATH: mutated}, 'exact current B06 raw hash')

    def test_revision_rejects_proof_identity_scope_path_and_override_mutations(self):
        files, proof = self.revision_bytes()
        changes = [('purpose', 'PHYSICAL_SOURCE_ADMISSION'), ('date', '2026-10-30'),
                   ('revision_id', 'NEXT_REVISION'), ('schema_version', 2), ('limitations', [])]
        for key, value in changes:
            changed = json.loads(json.dumps(proof)); changed[key] = value
            with self.subTest(field=key):
                self.reject_revision_mutation({REVISION_PROOF_PATH: json.dumps(changed).encode()}, 'reviewed proof raw hash')
        for path in ('../modules/B06/prospective_capacity_reference.py', 'modules/B06/other.py',
                     './modules/B06/prospective_capacity_reference.py'):
            changed = json.loads(json.dumps(proof)); changed['transition']['path'] = path
            with self.subTest(path=path):
                self.reject_revision_mutation({REVISION_PROOF_PATH: json.dumps(changed).encode()})
        for addition in ({'second_transition': proof['transition']}, {'allowed_hashes': ['arbitrary']},
                         {'physical_admission': True}, {'readiness_credit': True}):
            changed = dict(proof, **addition)
            with self.subTest(extra=list(addition)):
                self.reject_revision_mutation({REVISION_PROOF_PATH: json.dumps(changed).encode()})
        self.reject_revision_mutation({REVISION_PROOF_PATH: files[REVISION_PROOF_PATH] + b' '})

    def test_revision_rejects_history_and_each_of_sixteen_other_current_contracts(self):
        files, _ = self.revision_bytes()
        self.reject_revision_mutation({INDEPENDENT_HISTORY_PATH: files[INDEPENDENT_HISTORY_PATH] + b' '},
                                      'historical manifest raw hash')
        history = json.loads(files[INDEPENDENT_HISTORY_PATH])['unchanged_independent_contracts']
        for path in history:
            if path != B06_CURRENT_PATH:
                with self.subTest(path=path):
                    self.reject_revision_mutation({path: files[path] + b'\n'}, 'unchanged current contract')

    def test_revision_rejects_current_manifest_scope_source_and_input_mutations(self):
        files, _ = self.revision_bytes()
        manifest = json.loads(files[B06_INPUT_MANIFEST_PATH])
        for field, value in (('claim_scope', 'ANNUAL_APPROVED'), ('physical_evidence_status', 'OBS')):
            changed = json.loads(json.dumps(manifest)); changed[field] = value
            with self.subTest(field=field):
                self.reject_revision_mutation({B06_INPUT_MANIFEST_PATH: json.dumps(changed).encode()}, 'exact current input manifest')
        for name, pin in manifest['inputs'].items():
            with self.subTest(input=name):
                self.reject_revision_mutation({pin['path']: files[pin['path']] + b'\n'})
        changed = json.loads(json.dumps(manifest))
        changed['inputs']['ventilation_method']['source_ids'] = ['NEW_AUTHORITY']
        self.reject_revision_mutation({B06_INPUT_MANIFEST_PATH: json.dumps(changed).encode()})

    def test_revision_rejects_coordinated_unauthorized_repin(self):
        files, proof = self.revision_bytes()
        manifest = json.loads(files[B06_INPUT_MANIFEST_PATH])
        method = manifest['inputs']['ventilation_method']['path']
        modified_method = files[method] + b'\n# unreviewed method revision\n'
        manifest['inputs']['ventilation_method']['sha256'] = hashlib.sha256(modified_method).hexdigest()
        new_pin = hashlib.sha256(json.dumps(manifest['inputs'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        modified_source = files[B06_CURRENT_PATH].replace(proof['transition']['current_pin_set_sha256'].encode(), new_pin.encode())
        changes = {method: modified_method, B06_INPUT_MANIFEST_PATH: json.dumps(manifest).encode(), B06_CURRENT_PATH: modified_source}
        self.reject_revision_mutation(changes, 'exact current B06 raw hash')
        changed_proof = json.loads(json.dumps(proof))
        changed_proof['transition']['current_sha256'] = hashlib.sha256(modified_source).hexdigest()
        changed_proof['transition']['current_pin_set_sha256'] = new_pin
        changed_proof['input_manifest']['current_sha256'] = hashlib.sha256(changes[B06_INPUT_MANIFEST_PATH]).hexdigest()
        changes[REVISION_PROOF_PATH] = json.dumps(changed_proof).encode()
        self.reject_revision_mutation(changes, 'reviewed proof raw hash')



if __name__ == "__main__":
    unittest.main()
