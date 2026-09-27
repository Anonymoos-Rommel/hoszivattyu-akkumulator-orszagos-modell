"""B05-P48 exact Mitsubishi/SZU acquisition package contract."""
from __future__ import annotations
from dataclasses import dataclass

Q = "Q"
REPORT_ID_BOUND = "REPORT_ID_BOUND"
QUALIFIED_TRANSIENT_RECORD = "QUALIFIED_TRANSIENT_RECORD"
READY_UNSENT = "READY_UNSENT"

@dataclass(frozen=True)
class AcquisitionResponse:
    exact_product: bool
    tested_subtype_or_model: str | None
    direct_test_binding: bool
    report_id: str | None
    report_date: str | None
    testing_lab: str | None
    tau_eq_reported: bool = False
    seconds_scale_trace: bool = False
    explicit_derivation_method: bool = False

    def classify(self) -> str:
        if not (
            self.exact_product
            and self.tested_subtype_or_model
            and self.direct_test_binding
            and self.report_id
            and self.report_date
            and self.testing_lab
        ):
            return Q
        if self.tau_eq_reported:
            return QUALIFIED_TRANSIENT_RECORD
        if self.seconds_scale_trace and self.explicit_derivation_method:
            return QUALIFIED_TRANSIENT_RECORD
        return REPORT_ID_BOUND

@dataclass(frozen=True)
class AcquisitionTarget:
    organization: str
    email: str
    official_public_route: bool
    dispatch_authorized: bool = False

    def state(self) -> str:
        if not (self.organization and self.email and self.official_public_route):
            return Q
        if self.dispatch_authorized:
            return "AUTHORIZED_TO_SEND"
        return READY_UNSENT

def required_request_fields() -> tuple[str, ...]:
    return (
        "certificate_registration_context",
        "tested_subtype_or_model",
        "direct_test_specimen_binding",
        "report_or_protocol_id",
        "report_date_or_revision",
        "testing_laboratory",
        "test_conditions",
        "tau_eq_presence",
        "seconds_scale_trace_presence",
        "sampling_cadence_if_trace_exists",
        "heat_output_and_electrical_input_channels_if_trace_exists",
        "steady_state_reference_if_trace_exists",
        "derivation_method_if_tau_is_derived",
    )

def p48_boundaries() -> tuple[str, ...]:
    return (
        "ACQUISITION_PACKAGE_READY_IS_NOT_DATA_ACQUIRED",
        "REPORT_ID_BOUND_IS_NOT_PRODUCT_TAU_EQ_PROVEN",
        "SERIAL_NONDISCLOSURE_IS_NOT_NO_DIRECT_TEST_BINDING",
        "OFFICIAL_CONTACT_ROUTE_IS_NOT_RESPONSE",
        "NO_EXTERNAL_SEND_WITHOUT_HUMAN_AUTHORIZATION",
    )
