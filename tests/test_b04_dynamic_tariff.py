from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import unittest
import csv
from pathlib import Path
from modules.B04.dynamic_tariff import HU, STEP, DynamicTariffError, PriceInterval, parse_mvm_table, price_dynamic_backcast_energy


def synthetic_day(day):
    start = datetime(day.year, day.month, day.day, tzinfo=HU).astimezone(timezone.utc)
    stop = (datetime(day.year, day.month, day.day, tzinfo=HU) + timedelta(days=1)).astimezone(timezone.utc)
    lines = []
    while start < stop:
        a, b = start.astimezone(HU), (start + STEP).astimezone(HU)
        lines.append(f'{a:%Y.%m.%d} {a.hour}:{a.minute:02} {b.hour}:{b.minute:02} -1,25')
        start += STEP
    return lines


class DynamicTariffTests(unittest.TestCase):
    def test_dst_days_keep_real_utc_duration_and_negative_prices(self):
        for day, count in [(date(2025,10,26),100), (date(2026,3,29),92), (date(2026,3,28),96)]:
            rows = parse_mvm_table('\n'.join(synthetic_day(day)), day, day+timedelta(days=1), 'SYNTHETIC')
            self.assertEqual(len(rows), count)
            self.assertEqual(len({r.start_utc for r in rows}), count)
            self.assertTrue(all(r.net_energy_huf_per_kwh == Decimal('-1.25') for r in rows))

    def test_missing_duplicate_reordered_or_malformed_rows_fail_closed(self):
        day = date(2025,10,26); lines=synthetic_day(day)
        malformed = lines.copy(); malformed[0]=malformed[0].replace('-1,25','NaN')
        for bad in [lines[:20]+lines[21:], lines[:20]+[lines[20]]+lines[20:], [lines[1],lines[0]]+lines[2:], malformed]:
            with self.assertRaises(DynamicTariffError):
                parse_mvm_table('\n'.join(bad), day, day+timedelta(days=1), 'SYNTHETIC')

    def prices(self, values):
        start = datetime(2025,9,1,tzinfo=timezone.utc)
        return [PriceInterval(start+i*STEP,start+(i+1)*STEP,Decimal(str(v)),'SYNTHETIC') for i,v in enumerate(values)]

    def test_all_consumption_weights_price_before_discount_split(self):
        result=price_dynamic_backcast_energy(self.prices([100,0]), [1,1], 1, 5)
        self.assertEqual(result.consumption_weighted_net_price_huf_per_kwh, 50)
        self.assertEqual(result.net_energy_cost_huf, 55)
        # Sequentially assigning the free/discounted quota would incorrectly give 5.
        self.assertEqual(result.status,'SCN_RETROSPECTIVE_D_ENERGY_ONLY')
        self.assertIn('NETWORK_AND_FIXED_CHARGES',result.excluded)

    def test_spread_is_not_added_twice_and_zero_demand_has_no_division(self):
        result=price_dynamic_backcast_energy(self.prices([20,20]),[1,1],0,5)
        self.assertEqual(result.net_energy_cost_huf,40)
        zero=price_dynamic_backcast_energy(self.prices([20,20]),[0,0],1,5)
        self.assertEqual(zero.net_energy_cost_huf,0)
        self.assertIsNone(zero.consumption_weighted_net_price_huf_per_kwh)

    def test_signed_prices_not_signed_net_import(self):
        self.assertEqual(price_dynamic_backcast_energy(self.prices([-10,-20]),[1,1],0,5).net_energy_cost_huf,-30)
        with self.assertRaises(DynamicTariffError):
            price_dynamic_backcast_energy(self.prices([10,20]),[1,-1],0,5)

    def test_consumer_rejects_misalignment_nonfinite_and_wrong_evidence(self):
        p=self.prices([10,20])
        for prices,load in [(p,[1]), ([p[0],p[0]],[1,1]), ([replace(p[0],evidence_status='OBS'),p[1]],[1,1]), ([replace(p[0],net_energy_huf_per_kwh=Decimal('NaN')),p[1]],[1,1]), ([replace(p[0],start_utc=p[0].start_utc.replace(tzinfo=None)),p[1]],[1,1]), ([replace(p[0],start_utc=p[0].start_utc.astimezone(HU)),p[1]],[1,1])]:
            with self.assertRaises(DynamicTariffError):
                price_dynamic_backcast_energy(prices,load,1,5)

    def test_consumer_rejects_off_grid_quarter_clocks(self):
        for shift in [timedelta(minutes=1),timedelta(seconds=1),timedelta(microseconds=1)]:
            bad=[replace(p,start_utc=p.start_utc+shift,end_utc=p.end_utc+shift) for p in self.prices([10,20])]
            with self.assertRaises(DynamicTariffError):
                price_dynamic_backcast_energy(bad,[1,1],1,5)

    def test_source_registry_notes_are_not_truncated_by_unquoted_commas(self):
        with (Path(__file__).resolve().parents[1]/'registry/sources.csv').open() as f:
            rows=list(csv.reader(f))
        self.assertTrue(all(len(row)==len(rows[0]) for row in rows))
        trane=next(row for row in rows if row[0]=='SRC-B05-TRANE-UNITRANE-UNT-PRC006-E4-2010')
        self.assertIn('no numeric water content is inferred',trane[-1])

    def test_calendar_months_are_not_blended(self):
        start=datetime(2025,9,30,23,45,tzinfo=HU).astimezone(timezone.utc)
        p=[PriceInterval(start+i*STEP,start+(i+1)*STEP,Decimal(20),'SYNTHETIC') for i in range(2)]
        with self.assertRaises(DynamicTariffError):
            price_dynamic_backcast_energy(p,[1,1],1,5)


if __name__=='__main__':unittest.main()
