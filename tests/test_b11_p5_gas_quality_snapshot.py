import unittest

from modules.B11.gas_reference_contract import CalorificBasis, GasReferenceState, MoistureBasis

from datetime import date

from modules.B11.gas_quality_snapshot_contract import (
    GasQualitySnapshot,
    MappingStatus,
    ParticipantGasPointMapping,
    authorize_programme_gas_quality,
    historical_point_value_authorizes_current_programme_period,
    public_source_access_authorizes_repository_materialization,
)
from modules.B11.gas_volume_bridge_contract import EvidenceStatus, PhysicalEvidence


def _snapshot(start=date(2026, 1, 1), end=date(2026, 12, 31)):
    return GasQualitySnapshot(
        point_id="POINT-A",
        period_start=start,
        period_end=end,
        gcv_mj_m3=PhysicalEvidence(39.0, "MJ/m3_GCV", EvidenceStatus.SCN, "fixture", reference_state=_STATE, calorific_basis=_BASIS),
        lhv_mj_m3=PhysicalEvidence(35.0, "MJ/m3_LHV", EvidenceStatus.SCN, "fixture", reference_state=_STATE, calorific_basis=_BASIS),
        source_ref="fixture",
        source_reference_period="fixture",
        repository_materialization_authorized=False,
    )


def _mapping(status=MappingStatus.EXACT, point_id="POINT-A"):
    return ParticipantGasPointMapping(
        participant_scope_id="PROGRAMME-SCOPE",
        point_id=point_id,
        status=status,
        source_ref="fixture",
    )

# Synthetic fixture conventions, not Hungarian gas-quality calibration.
_STATE = GasReferenceState(10.0, 100000.0, MoistureBasis.DRY)
_BASIS = CalorificBasis(20.0, "SYNTHETIC-QUALITY-CONTEXT")


class B11P5GasQualitySnapshotTests(unittest.TestCase):
    def test_exact_point_and_period_authorize_pair(self):
        pair = authorize_programme_gas_quality(
            _snapshot(), _mapping(), date(2026, 2, 1), date(2026, 11, 30)
        )
        assert pair.gcv_mj_m3.unit == "MJ/m3_GCV"
        assert pair.lhv_mj_m3.unit == "MJ/m3_LHV"
        assert pair.gcv_mj_m3.status == EvidenceStatus.SCN


    def test_historical_period_cannot_authorize_current_period(self):
        try:
            authorize_programme_gas_quality(
                _snapshot(date(2024, 1, 1), date(2024, 12, 31)),
                _mapping(),
                date(2026, 1, 1),
                date(2026, 12, 31),
            )
        except ValueError as exc:
            assert "does not cover programme period" in str(exc)
        else:
            raise AssertionError("historical snapshot must not authorize current programme period")


    def test_partial_mapping_blocks_authorization(self):
        try:
            authorize_programme_gas_quality(
                _snapshot(), _mapping(MappingStatus.PARTIAL), date(2026, 1, 1), date(2026, 12, 31)
            )
        except ValueError as exc:
            assert "exact participant" in str(exc)
        else:
            raise AssertionError("partial mapping must fail closed")


    def test_point_mismatch_blocks_authorization(self):
        try:
            authorize_programme_gas_quality(
                _snapshot(), _mapping(point_id="POINT-B"), date(2026, 1, 1), date(2026, 12, 31)
            )
        except ValueError as exc:
            assert "do not match" in str(exc)
        else:
            raise AssertionError("point mismatch must fail closed")


    def test_q_gas_quality_is_not_zero(self):
        snapshot = GasQualitySnapshot(
            point_id="POINT-A",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 12, 31),
            gcv_mj_m3=PhysicalEvidence(None, "MJ/m3_GCV", EvidenceStatus.Q, reference_state=_STATE, calorific_basis=_BASIS),
            lhv_mj_m3=PhysicalEvidence(None, "MJ/m3_LHV", EvidenceStatus.Q, reference_state=_STATE, calorific_basis=_BASIS),
            source_ref="fixture",
            source_reference_period="fixture",
            repository_materialization_authorized=False,
        )
        try:
            authorize_programme_gas_quality(snapshot, _mapping(), date(2026, 1, 1), date(2026, 12, 31))
        except ValueError as exc:
            assert "Q evidence" in str(exc)
        else:
            raise AssertionError("Q gas quality must block authorization")


    def test_public_access_is_not_materialization_authority(self):
        assert public_source_access_authorizes_repository_materialization() is False
        assert historical_point_value_authorizes_current_programme_period() is False



if __name__ == "__main__":
    unittest.main()
