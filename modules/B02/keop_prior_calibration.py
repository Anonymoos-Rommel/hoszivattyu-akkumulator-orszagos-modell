"""Controlled historical-prior calibration experiment, not E2 household types.

WBL counts and P21 group margins are hard controls. The 2011 prior informs
relative type composition only among source types valid in the same year.
Historical within-year type composition is transferred as ASS and treated as
conditionally independent of omitted county/wall/area/comfort/heating fields in this experiment.
This is not an admitted population-energy joint. Finite WBL bands require an explicit ASS year-distribution model; open tails
are never closed by an invented construction year. Physical fields stay tied
to one type_id. No component-wise low/high Cartesian buildings are created.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import defaultdict
from functools import lru_cache
from math import fsum,isclose
from pathlib import Path
from modules.B02.calibrated_archetype_linkage import build_calibrated_linkage,FULL_PROJECTION
from modules.B02.keop23_wbl_crosswalk import load_types,candidates_for,WBL_PERIOD_INTERVALS,GROUPS

ROOT=Path(__file__).resolve().parents[2]
UNIFORM='UNIFORM_FINITE_BAND_ASS'
EARLY='EARLY_WEIGHTED_FINITE_BAND_SCN'
LATE='LATE_WEIGHTED_FINITE_BAND_SCN'
CASES={'REFERENCE_EXPERIMENT':('CENTRAL',UNIFORM),'P21_FLAT_DIAGNOSTIC':('FLAT',UNIFORM),'EARLY_YEAR_DIAGNOSTIC':('CENTRAL',EARLY),'LATE_YEAR_DIAGNOSTIC':('CENTRAL',LATE)}


@lru_cache(maxsize=1)
def prior_counts():
    path=ROOT/'data/processed/b02/keop23_dwelling_prior_2011.csv'
    manifest=json.loads((ROOT/'registry/b02_keop23_prior_manifest.json').read_text())
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['curated_extract_sha256']:
        raise ValueError('reviewed historical prior artifact hash mismatch')
    with path.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    out={int(r['type_id']):int(r['source_typology_dwellings']) for r in rows}
    if len(rows)!=23 or set(out)!=set(range(1,24)) or sum(out.values())!=4363754 or any(v<=0 for v in out.values()):raise ValueError('exact23-type historical dwelling prior required')
    if any(r['census_reference_year']!='2011' or r['allowed_use']!='HISTORICAL_RELATIVE_PRIOR_ONLY' or r['source_id']!=manifest['source_id'] or r['evidence_status']!='DER' or r['building_group']!=load_types()[int(r['type_id'])].building_group for r in rows):raise ValueError('historical prior source/group/scope mismatch')
    return out



@lru_cache(maxsize=1)
def historical_area_surface():
    prior=prior_counts()
    with (ROOT/'data/processed/b02/keop23_dwelling_prior_2011.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    if sum(int(r['source_dwelling_area_m2']) for r in rows)!=336839750:raise ValueError('historical KSH area control mismatch')
    out={}
    for r in rows:
        i=int(r['type_id']);a=int(r['source_dwelling_area_m2'])/prior[i];factor=float(r['source_reference_area_factor'])
        expected=1.0 if i<=12 else (1.1 if 19<=i<=22 else 1.05)
        if factor!=expected or r['area_allowed_use']!='HISTORICAL_DWELLING_AREA_AND_FULL_HEATING_REFERENCE_ONLY':raise ValueError('source-applied area bridge mismatch')
        out[i]=(a,factor)
    return out


def _covers(item,year):
    return (item.construction_start_year is None or year>=item.construction_start_year) and (item.construction_end_year is None or year<=item.construction_end_year)


@lru_cache(maxsize=None)
def conditional_type_weights(period,group,age_bridge=UNIFORM):
    if age_bridge not in (UNIFORM,EARLY,LATE):raise ValueError('explicit admitted experimental age bridge required')
    rule=candidates_for(period,group);types=load_types();prior=prior_counts();lo,hi=WBL_PERIOD_INTERVALS[period]
    candidates=rule.candidate_type_ids
    result=dict.fromkeys(candidates,0.0)
    if lo is None or hi is None:
        # Every candidate must cover the entire open target tail. Otherwise an
        # additional tail model is needed; do not invent a start/end year.
        for i in candidates:
            t=types[i]
            if (lo is None and t.construction_start_year is not None) or (hi is None and t.construction_end_year is not None) or (lo is not None and not _covers(t,lo)) or (hi is not None and not _covers(t,hi)):
                raise ValueError('open-tail allocation is not identified by shared support')
        denominator=sum(prior[i] for i in candidates)
        result={i:prior[i]/denominator for i in candidates}
    else:
        years=range(lo,hi+1);n=hi-lo+1
        year_weights=[1.0 if age_bridge==UNIFORM else float(n-j if age_bridge==EARLY else j+1) for j in range(n)]
        total=fsum(year_weights)
        for year,yw in zip(years,year_weights):
            eligible=[i for i in candidates if _covers(types[i],year)]
            if not eligible:raise ValueError('uncovered construction year')
            denominator=sum(prior[i] for i in eligible)
            for i in eligible:result[i]+=yw/total*prior[i]/denominator
    if not isclose(fsum(result.values()),1,abs_tol=1e-12) or any(v<0 for v in result.values()):raise ValueError('conditional type weights do not conserve mass')
    return tuple(sorted(result.items()))


def _p21_context():
    rows,summary=build_calibrated_linkage();out={}
    for row in rows:
        key=(row['settlement_type_code'],row['construction_period_code'])
        v=(float(row['central_family_probability']),float(row['flat_family_probability']))
        if key in out and out[key]!=v:raise ValueError('P21 probability unexpectedly varies within declared context')
        out[key]=v
    return out,summary


def run_calibration_experiment():
    """Run four coherent diagnostics; no arbitrary national type-total target.

    Returns compact scenario/type totals and actual coverage diagnostics.
    All four conserve each observed WBL cell before district exclusion. FLAT
    changes only the already-canonical P21 group-shape diagnostic. EARLY/LATE
    change only the whole finite-band year distribution, not isolated inputs.
    """
    context,p21=_p21_context();types=load_types();areas=historical_area_surface()
    area_upper={'SQM_LT30':30,'SQM30-39':40,'SQM40-49':50,'SQM50-59':60,'SQM60-79':80,'SQM80-99':100,'SQM100-119':120,'SQM_GE120':None}
    accum={case:defaultdict(float) for case in CASES};area_comparison={case:defaultdict(float) for case in CASES};max_cell_error=dict.fromkeys(CASES,0.0);count=0;observed_all=0;observed_non_district=0
    with (ROOT/'data/processed/b02/ksh_wbl_joint_cells_2022.csv').open(newline='',encoding='utf-8') as f:
        for raw in csv.DictReader(f):
            if raw['projection_id']!=FULL_PROJECTION:continue
            count+=1;n=int(raw['dwelling_count']);observed_all+=n
            non_district=raw['heating_mode_code']!='HEAT12'
            if non_district:observed_non_district+=n
            period=raw['construction_period_code'];key=(raw['settlement_type_code'],period)
            for case,(group_shape,age_bridge) in CASES.items():
                p=context[key][0 if group_shape=='CENTRAL' else 1];cell=[]
                for group,gprob in zip(GROUPS,(p,1-p)):
                    for type_id,tprob in conditional_type_weights(period,group,age_bridge):
                        mass=n*gprob*tprob;cell.append(mass)
                        accum[case]['ALL',type_id]+=mass
                        if non_district:accum[case]['NON_DISTRICT',type_id]+=mass
                        upper=area_upper[raw['floor_area_code']]
                        if upper is not None and types[type_id].heated_floor_area_per_dwelling_m2>=upper:
                            area_comparison[case]['ALL']+=mass
                            if non_district:area_comparison[case]['NON_DISTRICT']+=mass
                max_cell_error[case]=max(max_cell_error[case],abs(fsum(cell)-n))
    if count!=116452 or observed_all!=4008541 or observed_non_district!=3389817:raise ValueError('canonical occupied joint/population mismatch')
    output=[]
    for case in CASES:
        for scope,target in [('ALL',observed_all),('NON_DISTRICT',observed_non_district)]:
            masses={i:accum[case][scope,i] for i in types};total=fsum(masses.values())
            if abs(total-target)>1e-5 or max_cell_error[case]>1e-8:raise ValueError('observed cell/stock conservation failed')
            family=fsum(masses[i] for i in types if types[i].building_group=='FAMILY_HOUSE')
            if scope=='ALL' and abs(family-p21.family_target_dwellings)>1e-5:raise ValueError('P21 group control mismatch')
            output.append(dict(case=case,population_scope=scope,observed_dwellings=target,model_weight_sum=total,family_expected=family,multi_expected=total-family,prototype_heated_area_exposure_m2=fsum(masses[i]*types[i].heated_floor_area_per_dwelling_m2 for i in types),prototype_heated_volume_exposure_m3=fsum(masses[i]*types[i].heated_floor_area_per_dwelling_m2*types[i].ceiling_height_m for i in types),historical_dwelling_area_exposure_m2=fsum(masses[i]*areas[i][0] for i in types),full_heating_reference_exposure_m2=fsum(masses[i]*areas[i][0]*areas[i][1] for i in types),area_transfer_status='ASS_2011_TYPE_MEANS_ON_2022_COUNTS_NOT_CURRENT_OBSERVATION',maximum_cell_residual=max_cell_error[case],type_weights=masses,numeric_proxy_area_above_wbl_band_upper_assignment_mass=area_comparison[case][scope],area_comparison_status='DIAGNOSTIC_ONLY_AREA_SEMANTICS_NOT_IDENTICAL',omitted_type_conditioning_fields=['county','wall_material','floor_area_band','comfort','heating_fuel','heating_mode_except_population_exclusion'],evidence_status='SCN',weight_admission='EXPERIMENT_ONLY_NOT_E2',physical_status='PROTOTYPE_GEOMETRY_AND_HISTORICAL_AREA_ARE_SEPARATE_EXPOSURES'))
    return tuple(output)
