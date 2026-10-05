"""National final-energy controls, not useful-heat or target-cohort estimates."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
TOTAL_END_USE='FC_OTH_HH_E'
END_USES=tuple(TOTAL_END_USE+'_'+s for s in ('SH','SC','WH','CK','LE','OE'))
SOURCE_ID='SRC-B02-EUROSTAT-HOUSEHOLD-ENDUSE-2024'


@dataclass(frozen=True)
class FinalEnergyControl:
    reference_year: int
    end_use: str
    energy_product: str
    value_tj: Decimal
    source_flag: str
    source_id: str=SOURCE_ID
    evidence_status: str='DER'
    energy_boundary: str='REPORTED_HOUSEHOLD_FINAL_ENERGY_BY_PRODUCT_AND_END_USE'
    geography: str='HU'

    @property
    def value_gwh(self):
        return self.value_tj*Decimal(5)/Decimal(18)


def load_controls():
    result={}
    with (ROOT/'data/processed/b02/eurostat_household_enduse_hu_2022_2024.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            key=(int(r['reference_year']),r['end_use'],r['energy_product'])
            if key in result or r['source_id']!=SOURCE_ID or r['geography']!='HU' or key[0] not in (2022,2023,2024):raise ValueError('unique pinned HU control required')
            if r['availability']=='MISSING':
                if r['value_tj'] or r['evidence_status']!='Q':raise ValueError('missing is not zero')
                result[key]=None
            elif r['availability']=='PRESENT':
                v=Decimal(r['value_tj'])
                if not v.is_finite() or v<0 or r['evidence_status']!='DER':raise ValueError('finite nonnegative compiled control required')
                result[key]=FinalEnergyControl(*key,v,r['source_flag'])
            else:raise ValueError('unknown availability')
    return result


def control(year: int,end_use: str,energy_product: str) -> FinalEnergyControl:
    v=load_controls().get((year,end_use,energy_product))
    if v is None:raise ValueError('requested source cell unavailable; no zero or interpolation')
    return v


def end_use_balance_residual_tj(year: int,energy_product: str) -> Decimal:
    """Require all six children; retain publisher rounding residual unchanged.

    This sums end uses within one product, never overlapping SIEC families.
    A missing child means this balance cannot be calculated from these cells.
    """
    return control(year,TOTAL_END_USE,energy_product).value_tj-sum((control(year,e,energy_product).value_tj for e in END_USES),Decimal(0))
