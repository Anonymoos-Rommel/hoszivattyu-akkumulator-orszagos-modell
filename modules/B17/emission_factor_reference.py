"""Read pinned official method defaults without selecting programme inputs.

The reviewed numeric panel and original PDF bytes remain external. This module
only reads; it does not materialize files, convert units, choose factors, weight
activity, apply GWP, or calculate emissions, exposure, health or monetary gains.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'registry/b17_emission_factor_reference_manifest.json'
MANIFEST_SHA256 = 'f014003803f9997c590a9e79fbd2b0752e217194bdec44643dfa94647c8cf78e'
REFERENCE_ID = 'B17-D01-EMISSION-FACTOR-REFERENCE-V1'
IPCC = 'SRC-B17-IPCC-2006-STATIONARY'
EEA = 'SRC-B17-EEA-SMALL-COMBUSTION-2023'
POLICY = {
    'materialization_scope': 'OFFICIAL_METHOD_FACTOR_REFERENCE_ONLY',
    'raw_storage_policy': 'EXTERNAL_ONLY',
    'public_raw_reuse_status': 'REPOSITORY_COPY_NOT_CLEARED',
    'programme_input_status': 'NOT_ADMITTED',
    'national_emissions_status': 'NOT_ESTABLISHED',
    'health_status': 'NOT_ESTABLISHED',
    'valuation_status': 'NOT_ESTABLISHED',
    'gwp_status': 'NOT_SELECTED',
    'readiness_percent': 0,
    'slice_status': 'INTEGRATING',
    'accepted_artifacts': [],
}
NUMBERS = frozenset(('value', 'lower', 'upper'))
METADATA = frozenset((
    'record_id', 'original_row_ordinal', 'source_id', 'source_sha256',
    'source_coordinate', 'fuel', 'device', 'source_fuel_device_scope',
    'pollutant', 'unit', 'calorific_basis', 'method_tier', 'sector', 'abatement',
    'abatement_source_status', 'numerical_abatement_adjustment', 'uncertainty_type',
    'pm_measurement_boundary', 'evidence_class', 'transcription_status',
    'application_status', 'carbon_reporting', 'notes', 'missing_bridge',
))


class EmissionFactorReferenceError(ValueError):
    """Pinned identity, source fidelity or reference-only interpretation failed."""


@dataclass(frozen=True)
class EmissionFactorRecord:
    record_id: str
    original_row_ordinal: int
    source_id: str
    source_sha256: str
    source_coordinate: str
    fuel: str
    device: str
    source_fuel_device_scope: str
    pollutant: str
    value: Decimal
    lower: Decimal
    upper: Decimal
    unit: str
    calorific_basis: str
    method_tier: int
    sector: str
    abatement: str
    abatement_source_status: str
    numerical_abatement_adjustment: str
    uncertainty_type: str
    pm_measurement_boundary: str | None
    evidence_class: str
    transcription_status: str
    application_status: str
    carbon_reporting: str
    notes: str
    missing_bridge: str
    original_abatement: str
    original_fuel_device_scope: str


@dataclass(frozen=True)
class EmissionFactorReference:
    records: tuple[EmissionFactorRecord, ...]
    panel_sha256: str
    original_panel_sha256: str
    qualification_sha256: str
    verified_source_ids: tuple[str, ...]
    programme_input_status: str = field(default='NOT_ADMITTED', init=False)
    national_emissions_status: str = field(default='NOT_ESTABLISHED', init=False)
    gwp_status: str = field(default='NOT_SELECTED', init=False)


@dataclass(frozen=True)
class ContextReference:
    source_id: str
    source_sha256: str
    document_title: str
    authority: str
    original_url: str
    retrieved_at: str
    document_date_or_revision: str
    reference_period: str
    claim_scope: str
    currentness_checked_at: str
    currentness_scope: str
    source_evidence_status: str
    reference_role: str = field(default='CONTEXT_ONLY_NOT_FACTOR_SELECTION', init=False)
    programme_input_status: str = field(default='NOT_ADMITTED', init=False)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EmissionFactorReferenceError('duplicate JSON key')
        result[key] = value
    return result


def _json(data):
    def nonfinite(_):
        raise EmissionFactorReferenceError('nonfinite JSON value')
    try:
        return json.loads(data, parse_float=Decimal, parse_int=int,
                          parse_constant=nonfinite, object_pairs_hook=_unique_pairs)
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        if isinstance(exc, EmissionFactorReferenceError):
            raise
        raise EmissionFactorReferenceError('invalid JSON evidence') from exc


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def source_manifest():
    """Return the exact public metadata authority; callers cannot supply new pins."""
    try:
        data = MANIFEST_PATH.read_bytes()
    except OSError as exc:
        raise EmissionFactorReferenceError('public reference manifest unavailable') from exc
    if _sha(data) != MANIFEST_SHA256:
        raise EmissionFactorReferenceError('public provenance/interpretation manifest changed')
    manifest = _json(data)
    if (not isinstance(manifest, dict) or manifest.get('reference_id') != REFERENCE_ID
            or any(manifest.get(k) != v for k, v in POLICY.items())):
        raise EmissionFactorReferenceError('reference-only policy changed')
    return manifest


def _pinned_bytes(path, pin):
    try:
        count = pin['byte_count']
        if type(count) is not int or count <= 0:
            raise EmissionFactorReferenceError('positive integer byte-count pin required')
        path = Path(path)
        if not path.is_file():
            raise EmissionFactorReferenceError('regular external evidence file required')
        with path.open('rb') as handle:
            data = handle.read(count + 1)
        if len(data) != count or _sha(data) != pin['sha256']:
            raise EmissionFactorReferenceError('exact external bytes/hash required: ' + pin['source_id'])
        return data
    except (OSError, TypeError, KeyError) as exc:
        raise EmissionFactorReferenceError('external evidence unavailable or malformed') from exc


def _source_bytes(path, spec):
    # A hash alone does not transform a successful HTML fetch into a PDF or make
    # a historical/failed ID an admitted authority. Never infer identity aliases.
    if spec['content_type'] == 'application/pdf':
        if spec['acquisition_status'] != 'SUCCESSFUL_DOCUMENT':
            raise EmissionFactorReferenceError('successful document acquisition required')
    elif spec['content_type'] == 'text/html':
        if spec['acquisition_status'] != 'SUCCESSFUL_REFERENCE_PAGE':
            raise EmissionFactorReferenceError('successful contextual page required')
    else:
        raise EmissionFactorReferenceError('unreviewed source content type')
    data = _pinned_bytes(path, spec)
    if spec['content_type'] == 'application/pdf' and not data.startswith(b'%PDF-'):
        raise EmissionFactorReferenceError('PDF signature required; HTML placeholder is not evidence')
    return data


def _decimal(value):
    # No binary-float round trip, string/boolean coercion or blank-to-zero fill.
    if type(value) is int:
        return Decimal(value)
    if not isinstance(value, Decimal) or not value.is_finite():
        raise EmissionFactorReferenceError('finite numeric Decimal lexeme required')
    return value


def _metadata_digest(row):
    metadata = {key: value for key, value in row.items() if key not in NUMBERS}
    try:
        data = json.dumps(metadata, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise EmissionFactorReferenceError('invalid original row metadata') from exc
    return _sha(data)


def _decode_panel(panel_data, original_data, qualification_data, manifest):
    """Validate all rows and lineage before returning any numeric reference."""
    panel, originals, qualification = map(_json, (panel_data, original_data, qualification_data))
    try:
        lineage = manifest['lineage']
        if (not isinstance(panel, dict) or set(panel) != {
                'schema_version', 'reference_id', 'original_panel_sha256', 'qualification_sha256', 'rows'}
                or type(panel['schema_version']) is not int or panel['schema_version'] != 1
                or panel['reference_id'] != REFERENCE_ID
                or panel['original_panel_sha256'] != lineage['original_panel']['sha256']
                or panel['qualification_sha256'] != lineage['qualification']['sha256']):
            raise EmissionFactorReferenceError('normalized panel identity/lineage mismatch')
        rows, specs = panel['rows'], manifest['records']
        count = manifest['external_panel']['record_count']
        if (not isinstance(originals, list) or not isinstance(rows, list)
                or len(originals) != count or len(rows) != count or len(specs) != count):
            raise EmissionFactorReferenceError('exact original and normalized row set required')
        corrections = qualification['corrections']
        if (not isinstance(corrections, list) or
                [{k: v for k, v in c.items() if k != 'numbers_unchanged'} for c in corrections]
                != manifest['metadata_corrections']):
            raise EmissionFactorReferenceError('qualified correction lineage mismatch')
        for pin, actual in zip(qualification['original_artifacts'],
                               (lineage['original_panel'], lineage['original_source_manifest'])):
            if pin['sha256'] != actual['sha256'] or pin['bytes'] != actual['byte_count']:
                raise EmissionFactorReferenceError('qualified original artifact mismatch')
        if len(qualification['original_artifacts']) != 2:
            raise EmissionFactorReferenceError('exact qualified original artifact identities required')
        correction_map = {}
        for correction in corrections:
            ordinal = correction['row_one_based']
            if (type(ordinal) is not int or not 1 <= ordinal <= count
                    or ordinal in correction_map
                    or type(correction['json_index_zero_based']) is not int
                    or correction['json_index_zero_based'] != ordinal - 1):
                raise EmissionFactorReferenceError('duplicate/malformed qualified correction ordinal')
            correction_map[ordinal] = correction
        source_specs = {s['source_id']: s for s in manifest['source_artifacts']}
        if len(source_specs) != 2 or set(source_specs) != {IPCC, EEA}:
            raise EmissionFactorReferenceError('exact factor source identities required')
        seen, semantic_keys, result = set(), set(), []
        for ordinal, (row, original, spec) in enumerate(zip(rows, originals, specs), 1):
            if not isinstance(row, dict) or set(row) != METADATA | NUMBERS or not isinstance(original, dict):
                raise EmissionFactorReferenceError('exact normalized/original row schema required')
            rid = row['record_id']
            if not isinstance(rid, str) or rid in seen or rid != spec['record_id']:
                raise EmissionFactorReferenceError('duplicate, reordered or unknown stable record identity')
            seen.add(rid)
            if (type(row['original_row_ordinal']) is not int or row['original_row_ordinal'] != ordinal
                    or type(row['method_tier']) is not int or row['method_tier'] not in (1, 2)):
                raise EmissionFactorReferenceError('exact original ordinal and method tier required')
            if {k: row[k] for k in METADATA} != spec['metadata']:
                raise EmissionFactorReferenceError('changed source boundary/metadata: ' + rid)
            if _metadata_digest(original) != spec['original_metadata_sha256']:
                raise EmissionFactorReferenceError('original row metadata lineage mismatch: ' + rid)
            sid = row['source_id']
            if sid not in source_specs or row['source_sha256'] != source_specs[sid]['sha256']:
                raise EmissionFactorReferenceError('source pin/identity mismatch')
            if any(row[k] != original[k] for k in ('source_id', 'source_coordinate', 'pollutant')):
                raise EmissionFactorReferenceError('original source row identity mismatch')
            key = (sid, row['source_coordinate'], row['source_fuel_device_scope'], row['pollutant'])
            if key in semantic_keys:
                raise EmissionFactorReferenceError('duplicate source-native factor identity')
            semantic_keys.add(key)
            numbers = {k: _decimal(row[k]) for k in NUMBERS}
            if any(numbers[k] != _decimal(original[k]) for k in NUMBERS):
                raise EmissionFactorReferenceError('corrected panel changed a source numeric cell')
            if not Decimal(0) <= numbers['lower'] <= numbers['value'] <= numbers['upper']:
                raise EmissionFactorReferenceError('negative or unordered source interval')
            correction = correction_map.get(ordinal)
            if correction:
                if (any(original[k] != v for k, v in correction['key'].items())
                        or original[correction['field']] != correction['original']
                        or any(original[k] != v for k, v in correction['numbers_unchanged'].items())):
                    raise EmissionFactorReferenceError('qualified correction does not match original row')
                target = 'source_fuel_device_scope' if correction['field'] == 'fuel_device_scope' else correction['field']
                if row[target] != correction['qualified_interpretation']:
                    raise EmissionFactorReferenceError('required qualified correction missing')
            result.append(EmissionFactorRecord(
                **{k: row[k] for k in METADATA}, **numbers,
                original_abatement=original['abatement'],
                original_fuel_device_scope=original.get('fuel_device_scope', original.get('fuel'))))
        return tuple(result)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError) as exc:
        if isinstance(exc, EmissionFactorReferenceError):
            raise
        raise EmissionFactorReferenceError('malformed factor evidence or lineage') from exc


def read_emission_factor_reference(panel_path, original_panel_path, qualification_path, source_paths):
    """Read all reviewed factors with explicit paths keyed by the two exact source IDs.

    The original panel and independent qualification are mandatory lineage inputs.
    No path is taken from external JSON; caller paths have no identity authority.
    All pins and source signatures pass before rows become available.
    """
    manifest = source_manifest()
    specs = manifest['source_artifacts']
    if not isinstance(source_paths, Mapping) or set(source_paths) != {s['source_id'] for s in specs}:
        raise EmissionFactorReferenceError('exact explicit factor source mapping required; no aliases or context substitutions')
    for spec in specs:
        _source_bytes(source_paths[spec['source_id']], spec)
    panel = _pinned_bytes(panel_path, manifest['external_panel'])
    original = _pinned_bytes(original_panel_path, manifest['lineage']['original_panel'])
    qualification = _pinned_bytes(qualification_path, manifest['lineage']['qualification'])
    records = _decode_panel(panel, original, qualification, manifest)
    return EmissionFactorReference(
        records, manifest['external_panel']['sha256'], manifest['lineage']['original_panel']['sha256'],
        manifest['lineage']['qualification']['sha256'], tuple(s['source_id'] for s in specs))


def read_context_reference(path, source_id):
    """Verify a successful contextual artifact; return metadata only, never a factor.

    Failed acquisitions, discovery pages, superseded vintages and aliases are
    deliberately absent. Context does not select Hungarian activity-year factors,
    electricity response, device weights, refrigerant assumptions or GWP.
    """
    manifest = source_manifest()
    specs = {s['source_id']: s for s in manifest['contextual_source_artifacts']}
    if not isinstance(source_id, str) or source_id not in specs:
        raise EmissionFactorReferenceError('explicit qualified contextual source ID required; no aliases')
    spec = specs[source_id]
    if spec['reference_role'] != 'CONTEXT_ONLY_NOT_FACTOR_SELECTION':
        raise EmissionFactorReferenceError('context cannot select a factor')
    _source_bytes(path, spec)
    names = ('source_id', 'document_title', 'authority', 'original_url', 'retrieved_at',
             'document_date_or_revision', 'reference_period', 'claim_scope',
             'currentness_checked_at', 'currentness_scope', 'source_evidence_status')
    return ContextReference(**{k: spec[k] for k in names}, source_sha256=spec['sha256'])
