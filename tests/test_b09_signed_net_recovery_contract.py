import unittest
from datetime import datetime, timedelta, timezone

from modules.B08.observed_load_contract import CONTROL_AREA_SCHEME, HUNGARY_CONTROL_AREA
from modules.B09.engine import GENERATION_BOUNDARY, SIGNED_NET_GENERATION_BOUNDARY
from modules.B09.observed_generation_contract import ObservedGenerationRecord
from modules.B09.signed_net_recovery_contract import (
    MAVIR_OPERATIONAL_SHA256,
    MAVIR_NET_OPERATIONAL_SOURCE_ID,
    SignedNetRecoveryContractError,
    SignedNetRecoveryRecord,
    materialize_recovered_generation_panel,
)


ENTSOE_REF = ("SRC-B09-ENTSOE-ACTUAL-GENERATION-TYPE-2026",)
HASH = sorted(MAVIR_OPERATIONAL_SHA256)[0]


def a75_row(code, timestamp, power_mw):
    return ObservedGenerationRecord(
        source_series_id=f"SERIES-{code}-{timestamp.isoformat()}",
        timestamp_utc=timestamp,
        interval_end_utc=timestamp + timedelta(minutes=15),
        timestep_hours=0.25,
        power_mw=power_mw,
        production_type_code=code,
        business_type="A01",
        region_id=HUNGARY_CONTROL_AREA,
        region_scheme=CONTROL_AREA_SCHEME,
        evidence_status="Q",
        source_refs=ENTSOE_REF,
    )


class SignedNetRecoveryContractTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        self.end = self.start + timedelta(minutes=30)
        t0 = self.start
        t1 = self.start + timedelta(minutes=15)
        self.a75 = (
            a75_row("B04", t0, None),
            a75_row("B04", t1, 10.0),
            a75_row("B06", t0, 1.5),
            a75_row("B06", t1, 0.0),
        )
        self.recovery = (
            SignedNetRecoveryRecord(
                timestamp_utc=t0,
                timestep_hours=0.25,
                production_type_code="B04",
                signed_power_mw=-5.79,
                source_sha256=HASH,
            ),
        )

    def test_missing_cell_is_recovered_without_overwriting_numeric_a75(self):
        panel = materialize_recovered_generation_panel(
            self.a75,
            self.recovery,
            expected_production_types=("B04", "B06"),
            request_start_utc=self.start,
            request_end_utc=self.end,
        )
        self.assertEqual(panel.recovered_cell_count, 1)
        self.assertEqual(panel.negative_recovery_count, 1)
        recovered = next(
            row for row in panel.records
            if row.source_component_id == "ENTSOE_PSR_B04" and row.timestamp == self.start
        )
        numeric = next(
            row for row in panel.records
            if row.source_component_id == "ENTSOE_PSR_B04"
            and row.timestamp == self.start + timedelta(minutes=15)
        )
        self.assertEqual(recovered.boundary_id, SIGNED_NET_GENERATION_BOUNDARY)
        self.assertEqual(recovered.delivered_generation_kw, 0.0)
        self.assertEqual(recovered.source_withdrawal_kw, 5790.0)
        self.assertEqual(recovered.net_generation_contribution_kw, -5790.0)
        self.assertIn(MAVIR_NET_OPERATIONAL_SOURCE_ID, recovered.source_refs)
        self.assertEqual(numeric.boundary_id, GENERATION_BOUNDARY)
        self.assertEqual(numeric.delivered_generation_kw, 10000.0)
        self.assertEqual(numeric.source_withdrawal_kw, 0.0)

    def test_recovery_key_must_exactly_match_a75_missing_key(self):
        extra = SignedNetRecoveryRecord(
            timestamp_utc=self.start + timedelta(minutes=15),
            timestep_hours=0.25,
            production_type_code="B04",
            signed_power_mw=9.0,
            source_sha256=HASH,
        )
        with self.assertRaises(SignedNetRecoveryContractError):
            materialize_recovered_generation_panel(
                self.a75,
                self.recovery + (extra,),
                expected_production_types=("B04", "B06"),
                request_start_utc=self.start,
                request_end_utc=self.end,
            )

    def test_missing_recovery_fails_closed(self):
        with self.assertRaises(SignedNetRecoveryContractError):
            materialize_recovered_generation_panel(
                self.a75,
                (),
                expected_production_types=("B04", "B06"),
                request_start_utc=self.start,
                request_end_utc=self.end,
            )

    def test_unvalidated_source_hash_fails_closed(self):
        with self.assertRaises(SignedNetRecoveryContractError):
            SignedNetRecoveryRecord(
                timestamp_utc=self.start,
                timestep_hours=0.25,
                production_type_code="B04",
                signed_power_mw=-5.79,
                source_sha256="0" * 64,
            )

    def test_recovery_type_is_limited_to_validated_p6_set(self):
        with self.assertRaises(SignedNetRecoveryContractError):
            SignedNetRecoveryRecord(
                timestamp_utc=self.start,
                timestep_hours=0.25,
                production_type_code="B14",
                signed_power_mw=-1.0,
                source_sha256=HASH,
            )


if __name__ == "__main__":
    unittest.main()
