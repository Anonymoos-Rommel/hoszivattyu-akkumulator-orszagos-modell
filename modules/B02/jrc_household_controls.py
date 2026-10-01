"""JRC model controls and matched-boundary diagnostics; no E2 base admission."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from modules.B02.household_energy_controls import control

ROOT=Path(__file__).resolve().parents[2]
SOURCE_ID='SRC-B02-JRC-IDEES-HU-2023'
TJ_PER_KTOE=Decimal('41.868')


@dataclass(frozen=True)
class JrcControl:
    sheet: str
    row: int
    reference_year: int
    native_code: str
    unit: str
    value: Decimal | None
    source_formula: str
    evidence_status: str='DER'
    admission_scope: str='RESEARCH_CALIBRATION_CONTROLS_ONLY'


def load_controls():
    result={}
    with (ROOT/'data/processed/b02/jrc_household_controls_2022_2023.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            key=(r['sheet'],int(r['source_row']),int(r['reference_year']))
            if key in result or key[2] not in (2022,2023) or r['source_id']!=SOURCE_ID or '.HU.' not in r['native_code'] or r['source_unit']!=r['native_code'].split('.')[1]:raise ValueError('unique native HU JRC cell required')
            if r['availability']=='MISSING':
                if r['value'] or r['evidence_status']!='Q':raise ValueError('missing must remain missing')
                value=None
            elif r['availability']=='PRESENT':
                value=Decimal(r['value'])
                if not value.is_finite() or value<0 or r['evidence_status']!='DER':raise ValueError('finite nonnegative model value required')
            else:raise ValueError('invalid availability')
            result[key]=JrcControl(*key,r['native_code'],r['source_unit'],value,r['source_formula'],r['evidence_status'])
    return result


def value(sheet,row,year,unit):
    v=load_controls().get((sheet,row,year))
    if v is None or v.value is None or v.unit!=unit:raise ValueError('source value unavailable or unit mismatch')
    return v.value


def efficiency_residual(year,row):
    """Compare native TES/FEC with the workbook's cached efficiency ratio."""
    fec=value('RES_hh_fec',row,year,'ktoe');tes=value('RES_hh_tes',row,year,'ktoe')
    if fec<=0:raise ValueError('ratio undefined for zero final energy')
    return tes/fec-value('RES_hh_eff',row,year,'ratio')


def eurostat_comparisons(year):
    """JRC minus current Eurostat at the SAME year/product/end-use boundary.

    Gas includes natural gas plus biogas on both sides. Space-heating total
    excludes ambient heat on both sides. No inferred programme denominator.
    Differences are diagnostics, not estimates of independent-source error.
    """
    def eu(end,product):return control(year,end,product).value_tj
    base='FC_OTH_HH_E'
    rows=[
        ('TOTAL_WITH_AMBIENT',value('RES_summary',28,year,'ktoe'),eu(base,'TOTAL')),
        ('GAS_AND_BIOGAS_TOTAL',value('RES_summary',33,year,'ktoe')+value('RES_summary',36,year,'ktoe'),eu(base,'G3000')+eu(base,'R5300')),
        ('SPACE_HEATING_EXCLUDING_AMBIENT',value('RES_hh_fec',4,year,'ktoe'),eu(base+'_SH','TOTAL')-eu(base+'_SH','RA600')),
        ('WATER_HEATING_TOTAL',value('RES_hh_fec',17,year,'ktoe'),eu(base+'_WH','TOTAL')),
        ('GAS_AND_BIOGAS_SPACE_HEATING',value('RES_hh_fec',8,year,'ktoe'),eu(base+'_SH','G3000')+eu(base+'_SH','R5300')),
        ('GAS_AND_BIOGAS_WATER_HEATING',value('RES_hh_fec',21,year,'ktoe'),eu(base+'_WH','G3000')+eu(base+'_WH','R5300')),
    ]
    output=[]
    for name,ktoe,observed in rows:
        jrc=ktoe*TJ_PER_KTOE;delta=jrc-observed
        output.append(dict(quantity=name,reference_year=year,unit='TJ',jrc_compiled_value=jrc,eurostat_compiled_value=observed,residual=delta,relative_to_eurostat=delta/observed if observed else None,status='UNRESOLVED_REVISION_OR_DECOMPOSITION_DIFFERENCE'))
    return output


def gas_end_use_rebase_sensitivity(year):
    """Controlled diagnostic: retain native JRC efficiency, replace gas FEC only.

    Two entire SH/WH vectors are compared, not independent low/high variables.
    This tests source decomposition, not uncertainty in equipment efficiency,
    target selection, comfort, weather, heat-pump performance or national impact.
    It neither averages sources nor admits a new canonical useful-heat base.
    """
    out=[]
    for row,end in ((8,'SH'),(21,'WH')):
        jrc_fec=value('RES_hh_fec',row,year,'ktoe')*TJ_PER_KTOE
        jrc_tes=value('RES_hh_tes',row,year,'ktoe')*TJ_PER_KTOE
        if jrc_fec<=0:raise ValueError('positive gas FEC required')
        efficiency=jrc_tes/jrc_fec
        euro_fec=sum((control(year,'FC_OTH_HH_E_'+end,p).value_tj for p in ('G3000','R5300')),Decimal(0))
        alternate=euro_fec*efficiency
        out.append(dict(reference_year=year,end_use=end,unit='TJ_useful',native_jrc_tes=jrc_tes,matched_eurostat_fec_with_same_jrc_efficiency=alternate,delta=alternate-jrc_tes,status='SCN_CONTROLLED_SOURCE_DECOMPOSITION_SENSITIVITY',canonical_base_admitted=False))
    return out
