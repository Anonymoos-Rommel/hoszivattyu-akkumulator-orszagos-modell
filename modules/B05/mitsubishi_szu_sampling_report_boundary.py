"""B05-P47 Mitsubishi SZU certification sampling/report identity gates."""
from __future__ import annotations
from dataclasses import dataclass

Q = "Q"
CERTIFICATE_SCOPE_ONLY = "CERTIFICATE_SCOPE_ONLY"
SAMPLED_CERTIFICATION_SCOPE = "SAMPLED_CERTIFICATION_SCOPE"
CROSS_REGISTRATION_IDENTITY = "CROSS_REGISTRATION_IDENTITY"
EXACT_TEST_BINDING = "EXACT_TEST_BINDING"
QUALIFIED_TRANSIENT_RECORD = "QUALIFIED_TRANSIENT_RECORD"

@dataclass(frozen=True)
class CertificateScope:
    registration: str
    exact_product_in_scope: bool
    testing_lab_named: bool
    report_id: str | None = None
    tested_sample_id: str | None = None

    def classify(self) -> str:
        if not (self.registration and self.exact_product_in_scope and self.testing_lab_named):
            return Q
        if self.report_id and self.tested_sample_id:
            return EXACT_TEST_BINDING
        return CERTIFICATE_SCOPE_ONLY

@dataclass(frozen=True)
class SamplingArchitecture:
    certified_subtypes: int
    tested_subtypes: int

    def classify(self) -> str:
        if self.certified_subtypes <= 0 or self.tested_subtypes <= 0:
            return Q
        if self.tested_subtypes < self.certified_subtypes:
            return SAMPLED_CERTIFICATION_SCOPE
        return "EVERY_SUBTYPE_TESTED"

@dataclass(frozen=True)
class RegistrationComparison:
    registration_a: str
    registration_b: str
    same_outdoor_product: bool

    def classify(self) -> str:
        if not self.registration_a or not self.registration_b:
            return Q
        if self.registration_a == self.registration_b:
            return Q
        return CROSS_REGISTRATION_IDENTITY if self.same_outdoor_product else Q

@dataclass(frozen=True)
class ExactTransientRecord:
    exact_product: bool
    tested_specimen_binding: bool
    source_native_report_id: bool
    tau_eq_reported: bool
    seconds_scale_trace: bool
    explicit_derivation_method: bool

    def classify(self) -> str:
        if not (
            self.exact_product
            and self.tested_specimen_binding
            and self.source_native_report_id
        ):
            return Q
        if self.tau_eq_reported:
            return QUALIFIED_TRANSIENT_RECORD
        if self.seconds_scale_trace and self.explicit_derivation_method:
            return QUALIFIED_TRANSIENT_RECORD
        return EXACT_TEST_BINDING

def p47_boundaries() -> tuple[str, ...]:
    return (
        "REGISTRATION_ID_IS_NOT_TEST_REPORT_ID",
        "CERTIFIED_SUBTYPE_IS_NOT_PROVEN_DIRECTLY_TESTED_SUBTYPE",
        "SAME_OUTDOOR_UNIT_CAN_SPAN_MULTIPLE_REGISTRATIONS",
        "PASS_STATUS_IS_NOT_RAW_TRANSIENT_TRACE",
        "PUBLIC_REPORT_ID_NONRECOVERY_IS_NOT_REPORT_NONEXISTENCE",
        "CDH_IS_NOT_TAU_EQ",
    )
