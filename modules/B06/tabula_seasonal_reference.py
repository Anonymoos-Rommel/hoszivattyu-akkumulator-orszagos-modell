"""Nine historical TABULA seasonal heat references, never current-stock or peak.

Attribution: IEE Projects TABULA + EPISCOPE (www.episcope.eu).
Only pinned Refurbishment variants are supported; this is not a generic workbook
engine. Source-native nonuniform heating and explicit uniform SCN stay separate.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
INPUT_PATH=ROOT/'data/processed/b06/tabula_three_reference_cases.json'
MANIFEST_PATH=ROOT/'registry/b06_tabula_reference_manifest.json'
OPAQUE=('Roof_1','Roof_2','Wall_1','Wall_2','Wall_3','Floor_1','Floor_2')
TRANSPARENT=('Window_1','Window_2','Door_1')
COMPONENTS=OPAQUE+TRANSPARENT


def _calculate(row, uniform_heating=False):
    area=row['A_C_Ref']; effective={}
    for c in COMPONENTS:
        u=row['U_'+c]; fraction=row['f_Measure_'+c]
        measure=row['Code_MeasureType_'+c]; added=row['R_Measure_'+c]
        extra=row['R_Add_UnheatedSpace_'+c] if c in OPAQUE else 0
        if u>0:
            before=1/u+extra
            if c in OPAQUE and measure=='ReplaceInsulation':
                before-=row['d_Insulation_'+c]/.04
        else:
            before=0
        denominator=(extra if measure=='Replace' else before)+added
        modified=1/denominator if denominator else 0
        original=1/(1/u+extra) if u>0 else 0
        effective[c]=(1-fraction)*original+fraction*modified
    total_envelope=sum(row['A_Calc_'+c] for c in COMPONENTS)
    refurbished=sum(row['f_Measure_'+c]*row['A_Calc_'+c] for c in COMPONENTS if row['R_Measure_'+c]>0)/total_envelope
    delta_u=((1-refurbished)*row['delta_U_ThermalBridging_Original']+refurbished*row['delta_U_ThermalBridging_Refurbished']) if row['Code_ThermalBridging_Refurbished'] else row['delta_U_ThermalBridging_Original']
    transmission=sum(row['A_Calc_'+c]*effective[c]*(row['b_Transmission_'+c] if c in OPAQUE else 1) for c in COMPONENTS)+total_envelope*delta_u
    ht=transmission/area
    hv=.34*(row['n_air_use']+row['n_air_infiltration'])*row['h_room']
    if uniform_heating:
        reduction=1
    elif ht<=1:
        reduction=row['F_red_htr1']+(1-ht)/.5*(1-row['F_red_htr1'])
    elif ht>=4:
        reduction=row['F_red_htr4']
    else:
        reduction=row['F_red_htr1']+(ht-1)*(row['F_red_htr4']-row['F_red_htr1'])/3
    degree_days=(row['theta_i']-row['Theta_e'])*row['HeatingDays']
    loss=(ht+hv)*.024*degree_days*reduction
    window_area=sum(row['A_Calc_'+c] for c in ('Window_1','Window_2'))
    g=sum(row['A_Calc_'+c]*(row['g_gl_n_Measure_'+c] if len(str(row['Code_Measure_'+c]))>1 else row['g_gl_n_'+c]) for c in ('Window_1','Window_2'))/window_area if window_area else 0
    solar=0
    for direction in ('Hor','East','South','West','North'):
        orient='Horizontal' if direction=='Hor' else direction
        shading=row['F_sh_hor'] if direction=='Hor' else row['F_sh_vert']
        solar+=row['A_Calc_Window_'+orient]*row['I_Sol_'+direction]*shading*(1-row['F_f'])*row['F_w']*g
    solar/=area
    internal=row['phi_int']*row['HeatingDays']*.024
    tau=row['c_m']/(ht+hv); exponent=.8+tau/30; ratio=(solar+internal)/loss
    utilization=exponent/(exponent+1) if abs(ratio-1)<1e-12 else (1-ratio**exponent)/(1-ratio**(exponent+1))
    annual=loss-utilization*(solar+internal)
    return dict(effective_u=effective,h_transmission=ht,h_ventilation=hv,nonuniform_heating_factor=reduction,
                solar_gain_kwh_m2=solar,annual_heat_kwh_m2=annual,annual_heat_kwh=annual*area)



def source_package():
    import hashlib
    manifest=json.loads(MANIFEST_PATH.read_text())
    if hashlib.sha256(INPUT_PATH.read_bytes()).hexdigest()!=manifest['curated_extract_sha256']:
        raise ValueError('reviewed TABULA reference input hash mismatch')
    package=json.loads(INPUT_PATH.read_text())
    if package['source_id']!=manifest['source_id'] or package['source_sha256']!=manifest['source_sha256']:
        raise ValueError('source identity mismatch')
    if len(package['rows'])!=9 or any(r['values']['Code_TypeVariant']!='Refurbishment' for r in package['rows']):
        raise ValueError('only the nine reviewed Refurbishment variants are supported')
    return package


def calculate_reference(variant_id, *, service="source", indoor_temperature_c=None):
    """Historical source case or explicit uniform-service scenario; never a peak."""
    import math
    package=source_package()
    matches=[r for r in package['rows'] if r['values']['Code_BuildingVariant']==variant_id]
    if len(matches)!=1: raise ValueError('unknown historical reference variant')
    if service not in ('source','uniform'): raise ValueError('explicit source or uniform service required')
    if indoor_temperature_c is not None and service!='uniform':
        raise ValueError('temperature perturbation requires explicit uniform-service scenario')
    row=dict(matches[0]['values'])
    if indoor_temperature_c is not None:
        if not math.isfinite(indoor_temperature_c) or indoor_temperature_c<=row['Theta_e']:
            raise ValueError('finite indoor temperature above seasonal outdoor mean required')
        row['theta_i']=indoor_temperature_c
    result=_calculate(row,service=='uniform')
    result.update(variant_id=variant_id,source_row=matches[0]['source_row'],
                  source_geometry_compatibility_flag=row['Check_EnvArea_ExactToEstim'],
                  evidence_status='DER' if service=='source' else 'SCN',
                  source_id=package['source_id'],service=service,
                  indoor_temperature_c=row['theta_i'],
                  claim_scope='HISTORICAL_ANNUAL_USEFUL_SPACE_HEAT_REFERENCE')
    return result
