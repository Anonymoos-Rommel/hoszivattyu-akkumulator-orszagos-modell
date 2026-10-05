"""Pinned source-native trade/production observations, never supply capacity.

Values, missing cells, confidentiality and non-applicable quantities remain
distinct. There is no count conversion, price-per-device, apparent-consumption,
import-share, domestic-content or programme rollout calculation in this module.
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / 'registry/b18_supply_source_reference_manifest.json'
TRADE_SOURCE = 'SRC-B18-COMEXT-HU-CN84186100-2025'
PRODUCTION_SOURCE = 'SRC-B18-PRODCOM-HU-28211400-2025'
POLICY = {
    'materialization_scope': 'RESEARCH_REFERENCE_ONLY',
    'raw_storage_policy': 'EXTERNAL_ONLY',
    'public_raw_reuse_status': 'REPOSITORY_COPY_NOT_CLEARED',
    'national_supply_capacity_status': 'NOT_ESTABLISHED',
    'national_import_share_status': 'NOT_ESTABLISHED',
    'model_use_status': 'SOURCE_SPECIFIC_REVIEW_REQUIRED',
}
TRADE_METRICS = ('VALUE_IN_EUROS', 'QUANTITY_IN_100KG', 'SUPPLEMENTARY_QUANTITY')
PRODUCTION_METRICS = ('PRODVAL', 'PRODQNT', 'OWNPRODVAL', 'OWNPRODQNT',
                      'SCPRODVAL', 'SCPRODQNT', 'EXPVAL', 'IMPVAL', 'EXPQNT', 'IMPQNT')
PRODUCTION_FLAGS = {
    'PRODVAL': 'PVALFLAG', 'PRODQNT': 'PQNTFLAG',
    'OWNPRODVAL': 'OWNVALFLAG', 'OWNPRODQNT': 'OWNQNTFLAG',
    'SCPRODVAL': 'SCVALFLAG', 'SCPRODQNT': 'SCQNTFLAG',
}
PRODUCTION_INDICATORS = (
    'PRODVAL', 'PVALFLAG', 'PVALBASE', 'EXPVAL', 'IMPVAL', 'PRODQNT', 'QNTUNIT',
    'PQNTFLAG', 'PQNTBASE', 'EXPQNT', 'IMPQNT', 'OWNPRODVAL', 'OWNVALFLAG',
    'OWNVALBASE', 'OWNPRODQNT', 'OWNQNTFLAG', 'OWNQNTBASE', 'SCPRODVAL',
    'SCVALFLAG', 'SCVALBASE', 'SCPRODQNT', 'SCQNTFLAG', 'SCQNTBASE')
PINS = {
    TRADE_SOURCE: {
        'sha256': '58bc362738335491a31cb4f5e7e81a30badb8b5bd6452c4ddf27da4cea94f19b',
        'byte_count': 14763, 'dataset_id': 'DS-045409', 'product_code': '84186100',
        'classification': 'CN_2025', 'reference_year': 2025,
        'source_updated_at': '2026-09-15T11:00:00+0200',
        'dimensions': ['freq', 'reporter', 'partner', 'product', 'flow', 'indicators', 'time'],
        'sizes': [1, 1, 278, 1, 2, 3, 1],
    },
    PRODUCTION_SOURCE: {
        'sha256': 'db1164f0bfe1b69f9c3a8a022c4dcc2d617db1f8b8480f6662f49cab544d7c78',
        'byte_count': 3494, 'dataset_id': 'DS-059367', 'product_code': '28211400',
        'classification': 'PRODCOM_2025_CPA_2_2', 'reference_year': 2025,
        'source_updated_at': '2026-09-29T11:00:00+0200',
        'dimensions': ['freq', 'reporter', 'product', 'indicators', 'time'],
        'sizes': [1, 1, 1, 23, 1],
    },
}
BRIDGE = {
    'cn_2025': '84186100', 'prodcom_2025': '28211400',
    'prior_prodcom': '28251380', 'prior_last_reference_year': 2024,
    'excluded_reversible_prodcom_2025': '28251252',
    'excluded_reversible_cn_2025': '84158100',
    'cn_2025_supplementary_unit': None,
    'time_series_substitution_authorized': False,
}


class SupplySourceReferenceError(ValueError):
    """Source identity or bounded interpretation failed."""


@dataclass(frozen=True)
class SupplySelection:
    source_id: str
    dataset_id: str
    product_code: str
    classification: str
    reference_year: int
    source_updated_at: str
    reporter: str
    partner: str | None
    flow: str | None
    metrics: tuple[str, ...]


@dataclass(frozen=True)
class SupplyReferenceRecord:
    source_id: str
    source_sha256: str
    dataset_id: str
    classification: str
    product_code: str
    source_product_label: str
    source_updated_at: str
    reference_year: int
    reporter: str
    partner: str | None
    flow: str | None
    metric: str
    source_metric_label: str
    value: Decimal | None
    unit: str | None
    source_cell_index: int
    source_flag_cell_index: int | None
    source_flag: str | None
    source_status: str | None
    value_status: str
    evidence_status: str


@dataclass(frozen=True)
class SupplyReference:
    selection: SupplySelection
    records: tuple[SupplyReferenceRecord, ...]
    materialization_scope: str = field(default=POLICY['materialization_scope'], init=False)
    raw_storage_policy: str = field(default=POLICY['raw_storage_policy'], init=False)
    national_supply_capacity_status: str = field(default='NOT_ESTABLISHED', init=False)
    national_import_share_status: str = field(default='NOT_ESTABLISHED', init=False)


def source_manifest():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
    if (manifest.get('reference_id') != 'B18-D02-SUPPLY-SOURCE-REFERENCE-V1'
            or any(manifest.get(k) != v for k, v in POLICY.items())
            or manifest.get('classification_bridge') != BRIDGE):
        raise SupplySourceReferenceError('source-only policy/classification authority changed')
    artifacts = manifest.get('source_artifacts', [])
    if len(artifacts) != len(PINS) or {a.get('source_id') for a in artifacts} != set(PINS):
        raise SupplySourceReferenceError('exact source artifacts required')
    for artifact in artifacts:
        if any(artifact.get(k) != v for k, v in PINS[artifact['source_id']].items()):
            raise SupplySourceReferenceError('source snapshot authority changed')
    return manifest


def _selection_spec(selection):
    if not isinstance(selection, SupplySelection) or selection.source_id not in PINS:
        raise SupplySourceReferenceError('explicit supported source selection required')
    spec = PINS[selection.source_id]
    for key in ('dataset_id', 'product_code', 'classification', 'reference_year', 'source_updated_at'):
        if getattr(selection, key) != spec[key]:
            raise SupplySourceReferenceError(f'incompatible {key}; no source substitution')
    if type(selection.reference_year) is not int or selection.reporter != 'HU':
        raise SupplySourceReferenceError('explicit HU annual reference required')
    if selection.source_id == TRADE_SOURCE:
        if selection.partner not in ('WORLD', 'INT_EU27_2020', 'EXT_EU27_2020') or selection.flow not in ('1', '2'):
            raise SupplySourceReferenceError('select exactly one partner aggregate and native trade flow')
        supported = TRADE_METRICS
    else:
        if selection.partner is not None or selection.flow is not None:
            raise SupplySourceReferenceError('production dataset has no partner or flow axis')
        supported = PRODUCTION_METRICS
    if (not isinstance(selection.metrics, tuple) or not selection.metrics
            or any(m not in supported for m in selection.metrics)
            or len(set(selection.metrics)) != len(selection.metrics)):
        raise SupplySourceReferenceError('distinct source-native metrics required; no capacity claims')
    return spec


def _unique_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise SupplySourceReferenceError('duplicate JSON key')
        result[k] = v
    return result


def _decode(data, selection, spec):
    """Decode only the selected pinned JSON-stat source; never coerce flags to zero."""
    try:
        obj = json.loads(data, parse_float=Decimal, parse_int=int,
                         parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')),
                         object_pairs_hook=_unique_pairs)
        if (obj['version'] != '2.0' or obj['class'] != 'dataset' or obj['source'] != 'ESTAT'
                or obj['extension']['id'] != selection.dataset_id
                or obj['updated'] != selection.source_updated_at
                or obj['id'] != spec['dimensions'] or obj['size'] != spec['sizes']
                or any(type(n) is not int for n in obj['size'])):
            raise SupplySourceReferenceError('JSON-stat identity/grain mismatch')
        axes = {}
        for dim, size in zip(obj['id'], obj['size']):
            axis = obj['dimension'][dim]['category']['index']
            if (not isinstance(axis, dict) or len(axis) != size
                    or any(type(i) is not int for i in axis.values())
                    or sorted(axis.values()) != list(range(size))):
                raise SupplySourceReferenceError('non-bijective JSON-stat axis')
            axes[dim] = axis
        for dim, value in [('freq', 'A'), ('reporter', 'HU'), ('time', '2025'), ('product', selection.product_code)]:
            if axes[dim] != {value: 0}:
                raise SupplySourceReferenceError('source scope mismatch')
        indicators = TRADE_METRICS if selection.source_id == TRADE_SOURCE else PRODUCTION_INDICATORS
        if axes['indicators'] != {m: i for i, m in enumerate(indicators)}:
            raise SupplySourceReferenceError('native indicator schema mismatch')
        if selection.source_id == TRADE_SOURCE and axes['flow'] != {'1': 0, '2': 1}:
            raise SupplySourceReferenceError('native trade flow schema mismatch')
        values = obj['value']
        statuses = obj.get('status', {})
        for mapping in (values, statuses):
            if (not isinstance(mapping, dict) or any(not k.isdigit() or str(int(k)) != k
                    or int(k) >= math.prod(obj['size']) for k in mapping)):
                raise SupplySourceReferenceError('invalid sparse cell map')
        coordinates = dict(freq='A', reporter='HU', product=selection.product_code, time='2025')
        if selection.partner is not None:
            coordinates.update(partner=selection.partner, flow=selection.flow)

        def index(metric):
            coords = {**coordinates, 'indicators': metric}
            return sum(axes[d][coords[d]] * math.prod(obj['size'][i + 1:]) for i, d in enumerate(obj['id']))

        result = []
        for metric in selection.metrics:
            pos = index(metric)
            raw = values.get(str(pos))
            status = statuses.get(str(pos))
            flag_metric = PRODUCTION_FLAGS.get(metric) if selection.source_id == PRODUCTION_SOURCE else None
            flag_pos = index(flag_metric) if flag_metric else None
            flag = values.get(str(flag_pos)) if flag_pos is not None else None
            if flag not in (None, ':C', '-') or status is not None:
                raise SupplySourceReferenceError('unreviewed native cell flag/status')
            if raw is not None and (isinstance(raw, bool) or not isinstance(raw, (int, Decimal))):
                raise SupplySourceReferenceError('non-numeric measure; flag is not a value')
            value = Decimal(raw) if raw is not None else None
            if value is not None and (not value.is_finite() or value < 0 or flag is not None):
                raise SupplySourceReferenceError('invalid value or conflict with source flag')
            if metric in ('VALUE_IN_EUROS', 'PRODVAL', 'OWNPRODVAL', 'SCPRODVAL', 'EXPVAL', 'IMPVAL'):
                unit = 'EUR'
            elif metric == 'QUANTITY_IN_100KG':
                unit = '100_KG_NET_MASS'
            else:
                # CN84186100 has no supplementary unit in 2025. The selected
                # PRODCOM code also has no applicable published quantity unit.
                unit = None
                if value is not None or (selection.source_id == PRODUCTION_SOURCE and values.get(str(index('QNTUNIT'))) is not None):
                    raise SupplySourceReferenceError('unreviewed quantity/unit; device counts forbidden')
            value_status = ('CONFIDENTIAL' if flag == ':C' else
                            'NOT_APPLICABLE' if flag == '-' else
                            'OBSERVED' if value is not None else
                            'NO_SUPPLEMENTARY_UNIT' if metric == 'SUPPLEMENTARY_QUANTITY' else 'MISSING')
            result.append(SupplyReferenceRecord(
                selection.source_id, spec['sha256'], selection.dataset_id, selection.classification,
                selection.product_code, obj['dimension']['product']['category']['label'][selection.product_code],
                selection.source_updated_at, selection.reference_year,
                selection.reporter, selection.partner, selection.flow, metric,
                obj['dimension']['indicators']['category']['label'][metric], value, unit,
                pos, flag_pos, flag, status, value_status, 'OBS' if value is not None else 'Q'))
        return tuple(result)
    except (KeyError, TypeError, IndexError, ValueError, UnicodeError) as exc:
        if isinstance(exc, SupplySourceReferenceError):
            raise
        raise SupplySourceReferenceError('invalid source-native JSON-stat document') from exc


def read_supply_reference(path, selection):
    source_manifest()
    spec = _selection_spec(selection)
    with Path(path).open('rb') as handle:
        data = handle.read(spec['byte_count'] + 1)
    if len(data) != spec['byte_count'] or hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise SupplySourceReferenceError('exact source bytes/hash required')
    return SupplyReference(selection, _decode(data, selection, spec))


def reference_summary(reference):
    if not isinstance(reference, SupplyReference):
        raise SupplySourceReferenceError('source reference required')
    _selection_spec(reference.selection)
    return {'reference_id': 'B18-D02-SUPPLY-SOURCE-REFERENCE-V1', **POLICY,
            'source_id': reference.selection.source_id,
            'source_sha256': PINS[reference.selection.source_id]['sha256'],
            'record_count': len(reference.records),
            'observed_numeric_cells': sum(r.value is not None for r in reference.records),
            'non_numeric_cells': sum(r.value is None for r in reference.records),
            'cross_source_substitution': 'FORBIDDEN',
            'national_capacity_or_import_share': None}
