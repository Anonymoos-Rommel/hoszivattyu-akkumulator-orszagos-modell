"""Synthetic regressions for direct-API evidence and boundary validation."""
import unittest
from dataclasses import replace
from datetime import datetime, timezone
from modules.B07.engine import BatterySpec, BatteryModelError, B08PhysicalHandoff
from modules.B08.engine import GridBoundaryRecord, B08ContractError
from modules.B11.physical_displacement_contract import EvidenceValue, EvidenceStatus, GasDisplacementInputs, calculate_physical_gas_displacement

class InputConsistencyTests(unittest.TestCase):
    def test_b07_boundary_and_status_rejection(self):
        spec = BatterySpec(10,10,0,1,5,5,.9,.9,1)
        for name, vals in {'capacity_boundary':['NOMINAL','Q',None], 'power_boundary':['DC','Q',None], 'efficiency_boundary':['ROUND_TRIP','Q',None], 'status':['OBS','DER','Q','ASS','POL','UNKNOWN',None]}.items():
            for val in vals:
                with self.subTest(field=name,value=val), self.assertRaises(BatteryModelError): replace(spec, **{name:val})

    def test_b08_direct_factory_parity(self):
        base=dict(timestamp=datetime(2025,1,1,tzinfo=timezone.utc),source_entity_id='TEST',region_id='R1',region_scheme='TEST',b01_state_id='S3',source_refs=('TEST_ONLY',))
        for truth, statuses in [('REAL',['OBS','DER','Q']),('SCN',['SCN','Q'])]:
            for upstream in statuses:
                for evidence in statuses:
                    handoff=B08PhysicalHandoff(1,0,0,0,1,1,.5,upstream,1)
                    direct=lambda:GridBoundaryRecord(**base,timestep_hours=1,truth_context=truth,evidence_status=evidence,net_grid_import_kw=1,net_grid_export_kw=0,physical_up_flex_kw=1,physical_down_flex_kw=1,battery_charge_kw=0,battery_discharge_kw=0,soc_fraction=.5,handoff_status=upstream,upstream_timestep_hours=1)
                    factory=lambda:GridBoundaryRecord.from_b07_handoff(**base,truth_context=truth,evidence_status=evidence,handoff=handoff)
                    with self.subTest(truth=truth,upstream=upstream,evidence=evidence):
                        if upstream==evidence or evidence=='Q': self.assertEqual(direct(),factory())
                        else:
                            for call in (direct,factory):
                                with self.assertRaises(B08ContractError):call()

    def test_b11_bad_numeric_each_field(self):
        ev=lambda x,u:EvidenceValue(x,u,EvidenceStatus.OBS,'TEST_ONLY')
        good=GasDisplacementInputs(ev(1000,'m3/year'),ev(.5,'fraction'),ev(.2,'fraction'),ev(.1,'fraction'))
        for field in good.__dataclass_fields__:
            for value in (True,False,None,float('nan'),float('inf'),'1',complex(1,0)):
                with self.subTest(field=field,value=str(value)), self.assertRaises(ValueError):
                    calculate_physical_gas_displacement(replace(good,**{field:replace(getattr(good,field),value=value)}))

    def test_b11_all_obs_der_combinations_are_derived(self):
        from itertools import product
        for statuses in product((EvidenceStatus.OBS,EvidenceStatus.DER),repeat=4):
            values=[EvidenceValue(x,u,s,'TEST_ONLY') for x,u,s in zip((1000,.5,.2,.1),('m3/year','fraction','fraction','fraction'),statuses)]
            with self.subTest(statuses=statuses):
                r=calculate_physical_gas_displacement(GasDisplacementInputs(*values))
                self.assertEqual(r.output_status,EvidenceStatus.DER)
                self.assertEqual((r.post_retrofit_gas_m3,r.displaced_gas_m3,r.remaining_gas_m3),(800,360,440))

if __name__=='__main__':unittest.main()
