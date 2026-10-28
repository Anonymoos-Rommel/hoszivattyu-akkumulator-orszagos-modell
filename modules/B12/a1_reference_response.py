"""Source-bound A1 reference response; no entitlement or cash-date defaults.

The physical window is UTC 2025, priced at the existing frozen 2026 B04 rates.
Native BillInputs are optional, structurally validated SCN inputs, not observed
invoices or newly qualified full-case accounting outputs. This module writes
nothing and never imports the historical build_response.py research script.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
from pathlib import Path
from types import MappingProxyType
from zoneinfo import ZoneInfo

from modules.B04 import engine as b04
from . import input_accounting_contract as native
from .a1_profile_projection import ProjectionBinding, ProjectionError, load_payload, parse_profile, REPOSITORY_PROJECTION_BINDING


class A1ReferenceError(ValueError):
    """Missing, changed or contradictory reference evidence."""


START = datetime(2025, 1, 1, tzinfo=timezone.utc)
CUT = datetime(2025, 7, 31, 22, tzinfo=timezone.utc)
END = datetime(2026, 1, 1, tzinfo=timezone.utc)
LOCAL = ZoneInfo("Europe/Budapest")
SCENARIO = "B08-D02-ONE-NEW-NONELECTRIC-SH-HOUSEHOLD-REFERENCE-UTC2025-V1"
AREA = "MVM D\u00e9m\u00e1sz"
# The price/case source admission keeps its original implementation lineage.
# Current implementation identity is separate and exact, never a rewritten
# historical manifest or permission for an arbitrary caller-supplied revision.
NATIVE_C01_BASELINE_SHA = "ced2880d4dda1f91e8f1ae72014f945806e1768e0befa954c5f684e1f2bdbd6a"
NATIVE_IMPLEMENTATION_SHA = "9aa201924cf08862233927b6e09d4ae1fa3e1c8f6663d7f27c7f4e356fa4c590"
PROFILE_COLUMNS = (
    "interval_start_utc", "interval_end_utc", "hours", "common_base_reference_kw",
    "no_programme_selected_reference_kw", "programme_selected_reference_kw",
    "unit_incremental_W55_device_reference_kw", "unit_incremental_W55_device_reference_kWh",
    "unit_incremental_W55_device_reference_mw", "native_national_hourly_mean_mw_reference_only",
    "HMV_electricity_kw", "outside_unit_auxiliary_correction_kw", "physical_net_increment_kw", "truth_context",
)
UNITS = MappingProxyType({"hours": "h", "common_base_reference_kw": "kW",
    "unit_incremental_W55_device_reference_kw": "kW",
    "unit_incremental_W55_device_reference_kWh": "kWh",
    "unit_incremental_W55_device_reference_mw": "MW"})


def _require(ok, message):
    if not ok:
        raise A1ReferenceError(message)


def _json(raw):
    return json.loads(raw.decode("utf-8-sig"), parse_float=Decimal)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _path(root, relative):
    _require(isinstance(relative, str) and bool(relative), "explicit relative source path required")
    p = (root / relative).resolve()
    _require(not Path(relative).is_absolute() and p.is_relative_to(root), "source path escapes bundle")
    return p


def _number(text):
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise A1ReferenceError("finite nonnegative source Decimal required") from exc
    _require(value.is_finite() and value >= 0, "finite nonnegative source Decimal required")
    return value


@dataclass(frozen=True)
class ReferencePeriod:
    id: str
    start_utc: datetime
    end_utc_exclusive: datetime
    hours: int
    base_kwh: Decimal
    hp_kwh: Decimal

    @property
    def service_period(self):
        # Cover the actual partial local dates; exact timestamps stay alongside.
        return native.Period(self.start_utc.astimezone(LOCAL).date(),
                             (self.end_utc_exclusive - timedelta(microseconds=1)).astimezone(LOCAL).date())


@dataclass(frozen=True)
class A1Reference:
    bundle_root: Path
    periods: tuple[ReferencePeriod, ...]
    provenance: tuple[tuple[str, str], ...]
    source_ids: tuple[str, ...]
    scenario_id: str = SCENARIO
    complete_local_civil_year: bool = False
    projection_binding: ProjectionBinding | None = None


@dataclass(frozen=True)
class BillContext:
    case: native.Case
    money_basis: native.MoneyBasis
    settlement_dates: object  # exact S1/S2 date mapping, no implicit t0
    meter_id: str
    scope_ref: str
    service_basis_ref: str
    application: native.Reference
    allocation: native.Reference
    coverage: native.Reference
    scenario_ref: str
    event_prefix: str


@dataclass(frozen=True)
class A1Response:
    status: str
    missing: tuple[str, ...]
    periods: tuple
    totals: object
    bills: tuple[native.BillInput, ...]
    reference: A1Reference
    full_cashflow: None = None
    full_capex: None = None
    roi: None = None


def summarize_hourly_profile(raw: bytes) -> tuple[ReferencePeriod, ...]:
    """Validate units/chronology and integrate source precision, without prices.

    This low-level parser does not admit source evidence. load_reference also
    requires the original manifest, physical receipt, SCN and current code pins.
    """
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
    _require(tuple(reader.fieldnames or ()) == PROFILE_COLUMNS, "hourly column/unit contract mismatch")
    sums = [[0, Decimal(0), Decimal(0)], [0, Decimal(0), Decimal(0)]]
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        count = 0
        for i, row in enumerate(reader):
            _require(None not in row and all(v is not None for v in row.values()), "malformed hourly CSV row")
            try:
                left = datetime.fromisoformat(row["interval_start_utc"])
                right = datetime.fromisoformat(row["interval_end_utc"])
            except ValueError as exc:
                raise A1ReferenceError("invalid hourly timestamp") from exc
            _require(left.utcoffset() == right.utcoffset() == timedelta(0), "UTC timestamps required")
            _require(left == START + timedelta(hours=i) and right == left + timedelta(hours=1),
                     "missing, duplicate, unordered or shifted hourly support")
            hours = _number(row["hours"])
            base = _number(row["common_base_reference_kw"])
            old = _number(row["no_programme_selected_reference_kw"])
            new = _number(row["programme_selected_reference_kw"])
            hp = _number(row["unit_incremental_W55_device_reference_kw"])
            energy = _number(row["unit_incremental_W55_device_reference_kWh"])
            mw = _number(row["unit_incremental_W55_device_reference_mw"])
            _require(hours == 1 and old == base and new == base + hp and energy == hp * hours and mw == hp / 1000,
                     "hour/kW/kWh/MW or common-base conservation mismatch")
            _require(row["truth_context"] == "SCN" and all(row[k] == "" for k in
                     ("HMV_electricity_kw", "outside_unit_auxiliary_correction_kw", "physical_net_increment_kw")),
                     "SH-only unknown components must stay unknown")
            bucket = sums[0 if left < CUT else 1]
            bucket[0] += 1
            bucket[1] += base * hours
            bucket[2] += energy
            count += 1
    _require(count == 8760 and [s[0] for s in sums] == [5086, 3674], "exact UTC2025 8760-hour window required")
    return tuple(ReferencePeriod(key, left, right, *s) for key, left, right, s in
                 (("S1", START, CUT, sums[0]), ("S2", CUT, END, sums[1])))


def _verified_bundle(root, projection_binding=None):
    root = Path(root).resolve()
    binding = _json((root / "A1_INPUT_BINDING.json").read_bytes())
    proof = {}
    documents = {}
    for name in ("accepted_c01_manifest", "legacy_a1_manifest"):
        item = binding[name]
        raw = _path(root, item["path"]).read_bytes()
        _require(_hash(raw) == item["sha256"], f"{name}: changed evidence manifest")
        documents[name] = _json(raw)
        proof[name] = _hash(raw)
    c01 = {r["path"]: r["sha256"] for r in documents["accepted_c01_manifest"]["files"]}
    for relative, expected in binding["active_implementation"].items():
        if relative == "repo/modules/B12/input_accounting_contract.py":
            _require(c01.get(relative) == binding.get("accepted_C01_B12_baseline_sha256") == NATIVE_C01_BASELINE_SHA
                     and expected == NATIVE_IMPLEMENTATION_SHA,
                     "native revision must preserve accepted C01 baseline and exact current implementation pin")
            proof["accepted_C01_B12_baseline"] = NATIVE_C01_BASELINE_SHA
        else:
            _require(c01.get(relative) == expected, "active implementation must match accepted C01 pin")
        actual = _hash(_path(root, binding["deployed_implementation_paths"][relative]).read_bytes())
        _require(actual == expected, "accepted C01 implementation or tariff drift")
        proof[relative] = actual
    for relative, imported in (("repo/modules/B04/engine.py", b04.__file__),
                               ("repo/modules/B12/input_accounting_contract.py", native.__file__)):
        _require(relative in binding["active_implementation"] and _path(root, binding["deployed_implementation_paths"][relative]) == Path(imported).resolve(),
                 "bound implementation must be the actual imported producer/adapter")
    legacy = documents["legacy_a1_manifest"]["sources"]
    _require(binding["legacy_B12_adapter_sha256_historical_only"] == legacy["B12_adapter"]["sha256"],
             "historical A1 B12 identity lost")
    _require(binding["active_B12_adapter_sha256"] == NATIVE_IMPLEMENTATION_SHA,
             "active B12 identity must be separately bound")
    raw_sources = {}
    projection_meta = None
    projected_raw = None
    if projection_binding is not None:
        try:
            projected_raw, projection_meta, projection_proof = load_payload(root, projection_binding,
                ancestor_sha256=legacy["physical_profile"]["sha256"], scenario_id=SCENARIO)
        except ProjectionError as exc:
            raise A1ReferenceError("projection: " + str(exc)) from exc
        proof.update(projection_proof)
    required = {"physical_profile", "physical_receipt", "physical_SCN", "B04_engine", "B04_tariffs",
                "B04_source_verification", "B04_source_pack"}
    _require(set(binding["source_paths"]) == required, "complete reference-source mapping required")
    for key, relative in binding["source_paths"].items():
        if key == "physical_profile" and projected_raw is not None:
            raw_sources[key] = projected_raw
            proof[key] = _hash(projected_raw)
            continue
        raw = _path(root, relative).read_bytes()
        _require(_hash(raw) == legacy[key]["sha256"], f"{key}: source hash mismatch")
        raw_sources[key] = raw
        proof[key] = _hash(raw)
    _require(_path(root, binding["source_paths"]["B04_tariffs"]) ==
             (b04.ROOT / "data/processed/residential_electricity_tariff_schedule.csv").resolve(),
             "B04 must consume the hash-bound tariff table")
    proof["historical_B12_adapter"] = legacy["B12_adapter"]["sha256"]
    return raw_sources, tuple(sorted(proof.items())), projection_meta


def load_reference(bundle_root, *, projection_binding=REPOSITORY_PROJECTION_BINDING) -> A1Reference:
    """Load repository minimal5 data; explicit None retains the legacy14 contract.

    The default is a pinned repository-relative representation, not fallback
    discovery. Missing/malformed minimal5 input fails closed. Legacy14 callers
    must explicitly pass projection_binding=None and supply its original bytes.
    """
    raw, proof, projection_meta = _verified_bundle(bundle_root, projection_binding)
    scenario = _json(raw["physical_SCN"])
    receipt = _json(raw["physical_receipt"])
    _require(scenario["id"] == receipt["id"] == SCENARIO and scenario["truth_context"] == "SCN"
             and scenario["PV"] == scenario["battery"] == "ABSENT_SCN", "wrong physical SCN")
    _require(receipt["hourly_rows"] == 8760 and receipt["start_utc"] == START.isoformat()
             and receipt["end_utc_exclusive"] == END.isoformat(), "physical receipt time coverage mismatch")
    source_hash = (_hash(raw["physical_profile"]) if projection_meta is None else projection_meta["ancestor"]["sha256"])
    _require(receipt["output_sha256"]["UNIT_INCREMENT_HOURLY_8760.csv"] == source_hash
             and receipt["output_sha256"]["APPROVED_REFERENCE_SCN.json"] == _hash(raw["physical_SCN"]),
             "physical receipt must bind the consumed hourly data and SCN")
    periods = (summarize_hourly_profile(raw["physical_profile"]) if projection_meta is None else
               tuple(ReferencePeriod(*p) for p in parse_profile(raw["physical_profile"])))
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        for field, value in (
            ("no_programme_selected_boundary_annual_kWh", sum(p.base_kwh for p in periods)),
            ("unit_incremental_device_reference_annual_kWh", sum(p.hp_kwh for p in periods)),
            ("programme_selected_boundary_annual_kWh", sum(p.base_kwh + p.hp_kwh for p in periods))):
            # The historical receipt printed rounded float totals. Compare at its
            # recorded decimal scale, keeping the full CSV precision in outputs.
            expected = Decimal(receipt[field])
            _require(value.quantize(Decimal(1).scaleb(expected.as_tuple().exponent)) == expected,
                     "CSV energy does not reconcile to the source receipt precision")
    tariffs = list(csv.DictReader(io.StringIO(raw["B04_tariffs"].decode("utf-8-sig"), newline="")))
    low = [r for r in tariffs if r["distributor_area"] == AREA and r["tariff_band"] == "A1 discounted"]
    high = [r for r in tariffs if r["tariff_id"] == "A1-ALL-MARKET"]
    _require(len(low) == len(high) == 1, "exact A1 distributor rows required")
    source_ids = tuple(sorted(set((low[0]["source_id"] + ";" + high[0]["source_id"]).split(";"))))
    verification_ids = {r["source_id"] for r in _json(raw["B04_source_verification"])["sources"]}
    _require({"SRC-B04-MVM-M1-2026", "SRC-B04-MVM-RESIDENTIAL-TARIFF-2026"} <= verification_ids,
             "frozen tariff source verification missing")
    return A1Reference(Path(bundle_root).resolve(), periods, proof, source_ids, projection_binding=projection_binding)


def _parameter_errors(parameters, name):
    if not isinstance(parameters, dict) or set(parameters) != {"S1", "S2"}:
        return (f"{name}: explicit S1/S2 mapping required",)
    return tuple(f"{name}.{key}: finite nonnegative Decimal required" for key, value in parameters.items()
                 if type(value) is not Decimal or not value.is_finite() or value < 0)


def _context_errors(context):
    if type(context) is not BillContext:
        return ("context: explicit BillContext required; C01 t0 is not a payment date",)
    errors = []
    if type(context.case) is not native.Case or type(context.money_basis) is not native.MoneyBasis:
        return ("context: native Case and MoneyBasis required",)
    try:
        native.validate_case(context.case)
    except native.B12ContractError as exc:
        return (f"context.case: {exc}",)
    basis = context.money_basis
    if (basis != context.case.monetary_basis or basis.currency != "HUF" or basis.nominal_real != "NOMINAL"
            or type(basis.price_date) is not date or basis.price_date.year != 2026
            or type(basis.convention) is not native.Reference or basis.convention.kind != "EXTERNAL_ADMISSION"):
        errors.append("context.money_basis: explicit case-matching nominal HUF2026 basis required")
    if not isinstance(context.settlement_dates, dict) or set(context.settlement_dates) != {"S1", "S2"}:
        errors.append("context.settlement_dates: exact S1/S2 settlement dates required")
    elif any(type(v) is not date for v in context.settlement_dates.values()):
        errors.append("context.settlement_dates: exact dates required; no t0 default")
    for key in ("meter_id", "scope_ref", "service_basis_ref", "scenario_ref", "event_prefix"):
        value = getattr(context, key)
        if not isinstance(value, str) or not value.strip() or value.startswith(native.SYNTHETIC):
            errors.append(f"context.{key}: explicit non-fixture identity required")
    if context.scope_ref != context.case.scope.scope_id or context.service_basis_ref != context.case.service_basis_ref:
        errors.append("context: case scope/service identity mismatch")
    for key in ("application", "allocation", "coverage"):
        ref = getattr(context, key)
        if type(ref) is not native.Reference or ref.kind != "EXTERNAL_ADMISSION":
            errors.append(f"context.{key}: explicit application/allocation/coverage reference required")
    return tuple(errors)


def evaluate_reference(reference: A1Reference, *, allowances=None, billed_months=None, context=None) -> A1Response:
    """Use one common q/m mapping for the two alternatives; never select a point.

    A missing/invalid context retains evaluated energy charges, but returns no
    BillInput. References supply explicit SCN use context; their presence is not
    an E2 qualification or an individual tariff entitlement determination.
    """
    fresh = load_reference(reference.bundle_root, projection_binding=reference.projection_binding)
    _require(fresh == reference, "reference data/provenance changed after loading")
    errors = _parameter_errors(allowances, "allowances") + _parameter_errors(billed_months, "billed_months")
    if errors:
        return A1Response("INCOMPLETE_PARAMETERS", errors, (), None, (), reference)
    rows = []
    producer_bills = []
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        for p in reference.periods:
            old = b04.price_a1(p.base_kwh, allowances[p.id], billed_months[p.id], AREA)
            new = b04.price_a1(p.base_kwh + p.hp_kwh, allowances[p.id], billed_months[p.id], AREA)
            _require(old.source_ids == new.source_ids == reference.source_ids, "B04 source lineage changed")
            rows.append(MappingProxyType(dict(id=p.id, baseline_consumption_gross_HUF=old.consumption_charge_huf,
                programme_consumption_gross_HUF=new.consumption_charge_huf, common_fixed_gross_HUF=old.fixed_charge_huf,
                baseline_total_gross_HUF=old.total_huf, programme_total_gross_HUF=new.total_huf,
                incremental_consumption_gross_HUF=new.consumption_charge_huf-old.consumption_charge_huf)))
            producer_bills.append((p, old, new))
        totals = MappingProxyType({k: sum((r[k] for r in rows), Decimal(0)) for k in rows[0] if k != "id"})
        errors = _context_errors(context)
        if errors:
            return A1Response("EVALUATED_CONTEXT_INCOMPLETE", errors, tuple(rows), totals, (), reference)
        bills = []
        try:
            native.validate_case(context.case)
            for p, old, new in producer_bills:
                service = p.service_period
                cash = native.Period(context.settlement_dates[p.id], context.settlement_dates[p.id])
                def scalar(value, unit, period):
                    return native.Scalar(value, unit, "SCN", period, context.money_basis.basis_id,
                                         reference.source_ids, context.scenario_ref, "E3", None, None, None)
                for leg, bill, quantity in (("baseline", old, p.base_kwh),
                                           ("programme", new, p.base_kwh + p.hp_kwh)):
                    identity = f"{context.event_prefix}:{p.id}:{leg}"
                    bills.append(native.BillInput.from_b04(bill,
                        consumption_gross=scalar(bill.consumption_charge_huf, "HUF", service),
                        fixed_gross=scalar(bill.fixed_charge_huf, "HUF", service),
                        total_gross=scalar(bill.total_huf, "HUF", service),
                        bill_id=identity, event_id=identity, leg=leg, carrier="ELECTRICITY",
                        end_use="COMMON_BASE_REFERENCE" if leg == "baseline" else "COMMON_BASE_PLUS_W55_SH_REFERENCE",
                        tariff_load_scope="RESIDENTIAL_GENERAL_LOAD", tariff_connection_scope="PROFILED_LOW_VOLTAGE",
                        physical_ref=f"{reference.scenario_id}:sha256:{dict(reference.provenance)['physical_profile']}",
                        service_basis_ref=context.service_basis_ref, meter_id=context.meter_id, distributor=AREA,
                        tariff_layer="FINAL_RETAIL_GROSS", product="A1", revision=bill.tariff_snapshot_date.isoformat(),
                        eligibility=context.application, service_period=service, period=cash,
                        quantity=scalar(quantity, "kWh", service), billed_months=scalar(billed_months[p.id], "month", service),
                        discounted_allocation=scalar(allowances[p.id], "kWh", service), scope_ref=context.scope_ref,
                        fixed_charge_key=f"{context.meter_id}:{p.id}", coverage=context.coverage,
                        gas_reference_state_ref=None, allocation_ref=context.allocation))
            # Validate against existing rows as well: changed IDs/end-use labels
            # cannot hide duplicate/overlapping meter coverage or fixed fees.
            for new in bills:
                for old in context.case.bills.rows:
                    if (new.leg == old.leg and new.meter_id == old.meter_id and
                            new.service_period.start <= old.service_period.end and
                            old.service_period.start <= new.service_period.end):
                        raise native.B12ContractError("A1 full selected-meter reference overlaps existing bill coverage")
            section = native.Section("ROWS", context.case.bills.rows + tuple(bills), context.coverage, ())
            native.validate_case(replace(context.case, bills=section))
        except native.B12ContractError as exc:
            return A1Response("EVALUATED_CONTEXT_INCOMPLETE", (f"context: {exc}",), tuple(rows), totals, (), reference)
    return A1Response("NATIVE_SCN_BILLINPUTS_STRUCTURALLY_VALID_REVIEW_NOT_QUALIFIED", (), tuple(rows),
                      totals, tuple(bills), reference)
