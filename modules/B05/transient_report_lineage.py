"""B05-P44 transient-report lineage and fail-closed content boundaries."""
from __future__ import annotations
from dataclasses import dataclass

Q = "Q"
REPORT_LINEAGE_BOUND = "REPORT_LINEAGE_BOUND"
TRANSIENT_CONTENT_QUALIFIED = "TRANSIENT_CONTENT_QUALIFIED"
STRONG_PLATFORM_LINK_NOT_PRODUCT_IDENTITY = "STRONG_PLATFORM_LINK_NOT_PRODUCT_IDENTITY"
QUALIFIED_FCU_EMITTER_OBS = "QUALIFIED_FCU_EMITTER_OBS"
POLICY_DEFAULT_ONLY = "POLICY_DEFAULT_ONLY"

@dataclass(frozen=True)
class ProductTransientReport:
    report_id: str
    exact_product_identity: bool
    recognised_lab: bool
    en14825_test_basis: bool
    tau_eq_reported: bool = False
    seconds_scale_trace: bool = False
    explicit_derivation_method: bool = False

    def classify(self) -> str:
        if not (self.report_id and self.exact_product_identity and
                self.recognised_lab and self.en14825_test_basis):
            return Q
        if self.tau_eq_reported:
            return TRANSIENT_CONTENT_QUALIFIED
        if self.seconds_scale_trace and self.explicit_derivation_method:
            return TRANSIENT_CONTENT_QUALIFIED
        return REPORT_LINEAGE_BOUND

@dataclass(frozen=True)
class CrossBrandPlatformEvidence:
    common_production_site: bool
    shared_report_reference: bool
    matching_static_performance: bool
    explicit_product_equivalence: bool = False

    def classify(self) -> str:
        if self.explicit_product_equivalence:
            return "EXPLICIT_PRODUCT_EQUIVALENCE"
        if (self.common_production_site and self.shared_report_reference and
                self.matching_static_performance):
            return STRONG_PLATFORM_LINK_NOT_PRODUCT_IDENTITY
        return Q

@dataclass(frozen=True)
class FanCoilHeatingTransient:
    source_id: str
    exact_fcu_identity: bool
    heating_mode: bool
    explicit_input_step: bool
    emitter_heat_output_response: bool
    response_time_s: float | None

    def classify(self) -> str:
        if not self.source_id or self.response_time_s is None or self.response_time_s <= 0:
            return Q
        if not (self.exact_fcu_identity and self.heating_mode and
                self.explicit_input_step and self.emitter_heat_output_response):
            return Q
        return QUALIFIED_FCU_EMITTER_OBS

def classify_tau_eq_default(value_s: float, authority: str) -> str:
    if value_s <= 0 or not authority:
        return Q
    return POLICY_DEFAULT_ONLY

def p44_boundaries() -> tuple[str, ...]:
    return (
        "EN14825_REPORT_EXISTS_IS_NOT_TAU_EQ_CONTENT",
        "CDH_IS_NOT_TAU_EQ",
        "PUBLIC_FORM_ABSENCE_IS_NOT_INTERNAL_REPORT_ABSENCE",
        "CROSS_BRAND_PLATFORM_EVIDENCE_IS_NOT_PRODUCT_IDENTITY",
        "ROOM_SYSTEM_RESPONSE_IS_NOT_FCU_EMITTER_OUTPUT_RESPONSE",
        "POLICY_DEFAULT_IS_NOT_PRODUCT_OBS",
    )
