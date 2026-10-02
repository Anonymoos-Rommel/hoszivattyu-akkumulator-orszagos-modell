"""Paired JRC national annual calibration reference, not participant heat demand."""
from __future__ import annotations
import csv
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from modules.B01.non_district_population import EXPECTED_NON_DISTRICT_HEATED_DWELLINGS,EXPECTED_DISTRICT_HEATED_DWELLINGS
from modules.B02.jrc_household_controls import SOURCE_ID,value,TJ_PER_KTOE
from modules.B02.household_energy_controls import control

ROOT=Path(__file__).resolve().parents[2]
COHORTS=('Solids','LPG','Oil','Gas','Biomass','Geo','DistrHeat','AdvElc','ConvElc')
CIRCULATION_COHORTS=COHORTS[:7]
# Exact 41.868 TJ/ktoe / 3.6 TJ/GWh. Construct the terminating decimal
# directly so a caller's low precision before import cannot round the constant.
GWH_PER_KTOE=Decimal('11.63')


def load_native_cells():
    result={}
    with (ROOT/'data/processed/b02/jrc_sh_dhw_cohorts_2022_2023.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            code=r['native_code'];year=int(r['reference_year']);key=(year,code)
            v=Decimal(r['value'])
            if key in result or r['source_id']!=SOURCE_ID or year not in (2022,2023) or '.HU.' not in code or r['source_unit']!=code.split('.')[1] or r['availability']!='PRESENT' or r['evidence_status']!='DER' or not v.is_finite() or v<0:raise ValueError('unique finite native paired source cell required')
            result[key]=v
    return result


def _prefix(metric,cohort):
    unit='number' if metric=='NUM' else 'ktoe'
    return f'{metric}.{unit}.HU.Res.HH.Thermal.SH.{cohort}'


def _cell(cells,year,code):
    try:return cells[year,code]
    except KeyError as exc:raise ValueError('missing native cohort cell: '+code) from exc


def cohort_accounting(year=2022):
    cells=load_native_cells();out=[]
    for c in COHORTS:
        p=_prefix('NUM',c);count=_cell(cells,year,p)
        children=sum((v for (y,k),v in cells.items() if y==year and k.startswith(p+'.WH.')),Decimal(0))
        if count!=count.to_integral_value() or children!=count:raise ValueError('DHW branch counts must reconcile to parent SH cohort')
        tes=_prefix('TES',c)
        circ=_cell(cells,year,tes+'.SH.Elec') if c in CIRCULATION_COHORTS else Decimal(0)
        sh=_cell(cells,year,tes+'.SH');wh=_cell(cells,year,tes+'.WH')
        solar=sum((v for (y,k),v in cells.items() if y==year and k.startswith(tes+'.WH.') and k.endswith('.Solar.Solar')),Decimal(0))
        out.append(dict(cohort=c,households=int(count),space_heating_tes_ktoe=sh,water_heating_tes_ktoe=wh,circulation_tes_ktoe=circ,solar_dhw_tes_ktoe=solar))
    if sum(r['households'] for r in out)!=value('RES_summary',6,year,'number'):raise ValueError('native household total mismatch')
    for field,row in [('space_heating_tes_ktoe',4),('water_heating_tes_ktoe',17),('circulation_tes_ktoe',14),('solar_dhw_tes_ktoe',26)]:
        if abs(sum((r[field] for r in out),Decimal(0))-value('RES_hh_tes',row,year,'ktoe'))>Decimal('1e-9'):raise ValueError('native thermal aggregate mismatch: '+field)
    return tuple(out)


@dataclass(frozen=True)
class AnnualHeatReference:
    reference_year: int
    native_non_district_households: int
    ksh_normalization_dwellings: int
    space_heating_excluding_circulation_gwh: Decimal
    water_heating_including_solar_gwh: Decimal
    circulation_gwh: Decimal
    solar_dhw_included_gwh: Decimal
    existing_advanced_electric_sh_included_gwh: Decimal
    evidence_status: str='DER'
    evidence_tier: str='E2_PROVISIONAL_BASE'
    claim_scope: str='NATIONAL_ANNUAL_CALIBRATION_REFERENCE'
    normalization_scope: str='KSH_DWELLING_EQUIVALENT_NOT_OBSERVED_MEAN'
    programme_scaling_allowed: bool=False

    @property
    def normalized_sh_kwh_per_dwelling_equivalent(self):
        return self.space_heating_excluding_circulation_gwh*Decimal(1000000)/self.ksh_normalization_dwellings

    @property
    def normalized_dhw_kwh_per_dwelling_equivalent(self):
        return self.water_heating_including_solar_gwh*Decimal(1000000)/self.ksh_normalization_dwellings


def annual_heat_reference():
    """One 2022 source-native vector; no household-count rescaling of energy.

    Exclude the entire district-space-heating cohort and all its DHW branches.
    Keep solar DHW and existing advanced electric SH visible; neither is a
    default heat-pump replacement opportunity. No participants parameter exists.
    """
    admission=json.loads((ROOT/'registry/b02_v1_annual_heat_admission.json').read_text())
    if admission['admission_status']!='E2_PROVISIONAL_BASE' or admission['reference_year']!=2022 or admission['geography']!='HU' or not admission['validation_debt'] or admission['claim_scope']!='NATIONAL_ANNUAL_CALIBRATION_REFERENCE' or hashlib.sha256((ROOT/admission['input_artifact']).read_bytes()).hexdigest()!=admission['input_artifact_sha256']:
        raise ValueError('current scoped E2 admission and exact source extract required')
    rows=[r for r in cohort_accounting(2022) if r['cohort']!='DistrHeat']
    sums={key:sum((r[key] for r in rows),Decimal(0)) for key in ('space_heating_tes_ktoe','water_heating_tes_ktoe','circulation_tes_ktoe','solar_dhw_tes_ktoe')}
    advanced=next(r['space_heating_tes_ktoe'] for r in rows if r['cohort']=='AdvElc')
    return AnnualHeatReference(2022,sum(r['households'] for r in rows),EXPECTED_NON_DISTRICT_HEATED_DWELLINGS,(sums['space_heating_tes_ktoe']-sums['circulation_tes_ktoe'])*GWH_PER_KTOE,sums['water_heating_tes_ktoe']*GWH_PER_KTOE,sums['circulation_tes_ktoe']*GWH_PER_KTOE,sums['solar_dhw_tes_ktoe']*GWH_PER_KTOE,advanced*GWH_PER_KTOE)


def district_split_sensitivity():
    """Keep total H8000 FEC fixed; change the paired SH/WH shares only.

    Native JRC efficiencies remain fixed. This is a coherent structural
    diagnostic, not a confidence interval or a re-estimated national reference.
    """
    year=2022
    euro=[control(year,'FC_OTH_HH_E_'+e,'H8000').value_tj for e in ('SH','WH')]
    fec=[value('RES_hh_fec',r,year,'ktoe')*TJ_PER_KTOE for r in (11,24)]
    tes=[value('RES_hh_tes',r,year,'ktoe')*TJ_PER_KTOE for r in (11,24)]
    total=sum(fec);alt_fec=[total*x/sum(euro) for x in euro]
    alt_tes=[f*t/q for f,t,q in zip(alt_fec,tes,fec)]
    delta=[a-b for a,b in zip(alt_tes,tes)]
    national=[value('RES_hh_tes',r,year,'ktoe')*TJ_PER_KTOE for r in (4,17)]
    # The same excluded H8000 component changes in national and district ledgers.
    # Subtracting an updated district quantity from a frozen national TES would
    # manufacture a spurious non-district change.
    cells=load_native_cells()
    district=[_cell(cells,year,_prefix('TES','DistrHeat')+'.'+end)*TJ_PER_KTOE for end in ('SH','WH')]
    cancellation=tuple(((n+d)-(x+d)-(n-x))/Decimal('3.6') for n,x,d in zip(national,district,delta))
    return dict(status='SCN_COHERENT_DISTRICT_END_USE_REALLOCATION',affected_scope='EXCLUDED_H8000_DISTRICT_BRANCH',fixed_final_energy_tj=total,original_final_energy_tj=tuple(fec),alternative_final_energy_tj=tuple(alt_fec),original_useful_energy_tj=tuple(tes),alternative_useful_energy_tj=tuple(alt_tes),delta_useful_gwh=tuple(d/Decimal('3.6') for d in delta),non_district_delta_useful_gwh=cancellation,canonical_reference_replaced=False)


def district_other_dhw_allocation_sensitivity():
    """Explicit count-intensity SCN for non-H8000 district DHW assignment.

    Keep native non-H8000 DHW intensity fixed while using the KSH district
    count as a diagnostic count-equivalent. This is not a calibrated estimate
    or confidence bound. Transfer energy between cohorts; never create energy.
    """
    year=2022;district=next(r for r in cohort_accounting(year) if r['cohort']=='DistrHeat')
    original_district_other=(district['water_heating_tes_ktoe']-value('RES_hh_tes',24,year,'ktoe'))*GWH_PER_KTOE
    ratio=Decimal(EXPECTED_DISTRICT_HEATED_DWELLINGS)/district['households']
    alternative_district_other=original_district_other*ratio
    transfer=alternative_district_other-original_district_other
    reference=annual_heat_reference().water_heating_including_solar_gwh
    if not Decimal(0)<=transfer<=reference:raise ValueError('diagnostic reassignment must remain inside available cohort energy')
    return dict(status='SCN_FIXED_NATIVE_DISTRICT_OTHER_DHW_INTENSITY',native_district_households=district['households'],ksh_district_dwelling_equivalent=EXPECTED_DISTRICT_HEATED_DWELLINGS,original_district_other_dhw_gwh=original_district_other,alternative_district_other_dhw_gwh=alternative_district_other,original_non_district_dhw_gwh=reference,alternative_non_district_dhw_gwh=reference-transfer,non_district_delta_gwh=-transfer,national_energy_delta_gwh=Decimal(0),canonical_reference_replaced=False)
