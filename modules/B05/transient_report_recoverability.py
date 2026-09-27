"""B05-P45 exact VDE report recoverability and content-admission boundary."""
from __future__ import annotations
from dataclasses import dataclass

Q = "Q"
EXACT_REPORT_REFERENCE_ONLY = "EXACT_REPORT_REFERENCE_ONLY"
PUBLIC_SURFACE_ONLY = "PUBLIC_SURFACE_ONLY"
QUALIFIED_PRODUCT_TRANSIENT_CONTENT = "QUALIFIED_PRODUCT_TRANSIENT_CONTENT"

@dataclass(frozen=True)
class ReportReference:
    report_id: str
    exact_product: bool
    official_source: bool
    contains_numeric_transient_content: bool = False

    def classify(self) -> str:
        if not (self.report_id and self.exact_product and self.official_source):
            return Q
        if self.contains_numeric_transient_content:
            return QUALIFIED_PRODUCT_TRANSIENT_CONTENT
        return EXACT_REPORT_REFERENCE_ONLY

@dataclass(frozen=True)
class PublicSearchResult:
    exact_id_queried: bool
    official_domains_queried: bool
    report_copy_recovered: bool
    source_native_transient_excerpt_recovered: bool

    def classify(self) -> str:
        if not (self.exact_id_queried and self.official_domains_queried):
            return Q
        if self.report_copy_recovered or self.source_native_transient_excerpt_recovered:
            return QUALIFIED_PRODUCT_TRANSIENT_CONTENT
        return PUBLIC_SURFACE_ONLY

@dataclass(frozen=True)
class PublicCertificationExport:
    exact_product: bool
    cdh_exposed: bool
    tau_eq_exposed: bool
    seconds_scale_trace_exposed: bool

    def admits_tau_eq(self) -> bool:
        return bool(
            self.exact_product
            and self.tau_eq_exposed
        )

    def admits_trace_derivation(self) -> bool:
        return bool(
            self.exact_product
            and self.seconds_scale_trace_exposed
        )

def p45_boundaries() -> tuple[str, ...]:
    return (
        "REPORT_ID_REFERENCE_IS_NOT_REPORT_CONTENT",
        "PUBLIC_INDEX_SEARCH_MISS_IS_NOT_REPORT_NONEXISTENCE",
        "PUBLIC_EXPORT_ABSENCE_IS_NOT_INTERNAL_REPORT_ABSENCE",
        "CERTIFICATE_PASS_STATUS_IS_NOT_RAW_TRANSIENT_TRACE",
        "CDH_IS_NOT_TAU_EQ",
        "STATIC_SEASONAL_EXPORT_IS_NOT_SECONDS_SCALE_TRANSIENT_RECORD",
    )
