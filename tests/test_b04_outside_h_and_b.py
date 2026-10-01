import unittest
from datetime import date
from decimal import Decimal
from unittest.mock import patch
from modules.B04.engine import price_h_outside,price_b_alap,TariffInputError,_rows

H_SCOPE='ELIGIBLE_HEAT_PUMP_AND_DIRECT_AUXILIARIES'
B_SCOPE='DECLARED_ELIGIBLE_CONTROLLED_LOAD'
CONNECTION='PROFILED_LOW_VOLTAGE'
class OutsideHAndBTests(unittest.TestCase):
 def outside(self,quantity=100,allowance=80,months=1,area='MVM Démász',start=date(2026,7,1),end=date(2026,7,31),scope=H_SCOPE,connection=CONNECTION):
  return price_h_outside(quantity,allowance,months,area,start,end,load_scope=scope,connection_scope=connection)
 def test_all_outside_area_rates_and_separate_explicit_allocation(self):
  for area,rate in [('MVM Démász','36.386'),('E.ON Dél/E.ON Észak/OPUS','35.293'),('ELMŰ','36.208'),('MVM Émász','35.992')]:
   b=self.outside(area=area)
   self.assertEqual(b.total_huf,Decimal(80)*Decimal(rate)+Decimal(20)*Decimal('70.104')+Decimal('153.035'))
   self.assertIn('SRC-B04-MEKH-SYSTEM-FEES-2024',b.source_ids)
   self.assertEqual(b.status,'SCN_CONSTANT_2026_TARIFF_SNAPSHOT')
  self.assertEqual(self.outside(allowance=0).discounted_kwh,0)
  self.assertEqual(self.outside(allowance=200).discounted_kwh,100)
  self.assertEqual(self.outside(months='0.5').fixed_charge_huf,Decimal('76.5175'))
 def test_season_and_connection_scope_are_not_inferred(self):
  self.outside(start=date(2026,4,16),end=date(2026,10,14))
  for start,end in [(date(2026,4,15),date(2026,4,16)),(date(2026,10,14),date(2026,10,15)),(date(2026,7,2),date(2026,7,1))]:
   with self.assertRaises(TariffInputError):self.outside(start=start,end=end)
  for c in ('Q','SMART_METER','NONRESIDENTIAL'):
   with self.assertRaises(TariffInputError):self.outside(connection=c)
  for s in ('BATTERY','GENERAL_LOAD','EXPORT'):
   with self.assertRaises(TariffInputError):self.outside(scope=s)
 def test_b_alap_has_its_own_excess_price_and_fixed_fee_once(self):
  for area,rate in [('MVM Démász','22.962'),('E.ON Dél/E.ON Észak/OPUS','23.520'),('ELMŰ','23.152'),('MVM Émász','22.682')]:
   b=price_b_alap(2524,2523,12,area,load_scope=B_SCOPE)
   self.assertEqual(b.total_huf,Decimal(2523)*Decimal(rate)+Decimal('60.935')+Decimal('601.98'))
   self.assertEqual(b.excess_kwh,1)
  with self.assertRaises(TariffInputError):price_b_alap(1,1,1,'MVM Démász',load_scope='Q')
 def test_unknown_duplicate_or_unreviewed_mapping_fails_closed(self):
  original=_rows
  for mode in ('Q','DUPLICATE','NO_AUTHORITY'):
   def altered(name):
    rows=[dict(r) for r in original(name)]
    if name=='h_tariff_schedule.csv':
     row=next(r for r in rows if r['tariff_id']=='H-DÉMÁSZ-OUTSIDE-DISCOUNTED')
     if mode=='Q':row['final_price_status']='Q'
     elif mode=='DUPLICATE':rows.append(dict(row))
     else:row['source_id']='SRC-B04-MVM-M1-2026'
    return rows
   with patch('modules.B04.engine._rows',side_effect=altered):
    with self.assertRaises(TariffInputError):self.outside()
  with self.assertRaises(TariffInputError):self.outside(area='UNKNOWN')
 def test_invalid_quantities_rejected(self):
  for value in (-1,'NaN','Infinity',None):
   for field in ('quantity','allowance','months'):
    with self.assertRaises(TariffInputError):self.outside(**{field:value})
   with self.assertRaises(TariffInputError):price_b_alap(value,10,1,'MVM Démász',load_scope=B_SCOPE)
 def test_each_derivation_source_is_required_at_runtime(self):
  original = _rows
  for source in ('SRC-B04-MEKH-SYSTEM-FEES-2024', 'SRC-B04-MVM-M1-2026', 'SRC-B04-MVM-RESIDENTIAL-TARIFF-2026'):
   def altered(name):
    rows = [dict(r) for r in original(name)]
    if name == 'h_tariff_schedule.csv':
     for r in rows:
      r['source_id'] = ';'.join(x for x in r['source_id'].split(';') if x != source)
    return rows
   with patch('modules.B04.engine._rows', side_effect=altered):
    with self.assertRaises(TariffInputError):self.outside()
 def test_zero_consumption_still_has_one_connection_fee(self):
  h = self.outside(quantity=0)
  b = price_b_alap(0, 100, 1, 'MVM Démász', load_scope=B_SCOPE)
  self.assertEqual(h.consumption_charge_huf, 0)
  self.assertEqual(h.total_huf, Decimal('153.035'))
  self.assertEqual(b.consumption_charge_huf, 0)
  self.assertEqual(b.total_huf, Decimal('50.165'))
 def test_historical_future_dates_only_select_season_not_tariff_revision(self):
  for year in (2025, 2027):
   b = self.outside(start=date(year, 7, 1), end=date(year, 7, 31))
   self.assertEqual(b.tariff_snapshot_date, date(2026, 10, 1))
   self.assertIn('NOT_HISTORICAL_OR_FUTURE_INVOICE', b.price_basis)
 def test_b_ambiguous_or_unadmitted_rate_fails_closed(self):
  original = _rows('residential_electricity_tariff_schedule.csv')
  high = next(r for r in original if r['tariff_id'] == 'B-ALAP-ALL-MARKET')
  variants = [
   [r for r in original if r['tariff_id'] != 'B-ALAP-ALL-MARKET'],
   original + [dict(high)],
   [dict(r, status='Q') if r is high else dict(r) for r in original],
   [dict(r, source_id='') if r is high else dict(r) for r in original],
  ]
  for rows in variants:
   with patch('modules.B04.engine._rows', return_value=rows):
    with self.assertRaises(TariffInputError):price_b_alap(100, 80, 1, 'MVM Démász', load_scope=B_SCOPE)
 def test_b_all_numeric_arguments_reject_invalid_values(self):
  for bad in (-1, 'NaN', 'Infinity', None):
   for index in range(3):
    args = [100, 80, 1]
    args[index] = bad
    with self.assertRaises(TariffInputError):price_b_alap(*args, 'MVM Démász', load_scope=B_SCOPE)

if __name__=='__main__':unittest.main()
