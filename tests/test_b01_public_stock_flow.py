import csv
from datetime import date
import io
import unittest
from unittest.mock import patch
from modules.B01.public_stock_flow import load_controls,reconcile_year,total_stock_at
from tools.extract_b01_public_stock_flow import parse_count,parse_section


class PublicStockFlowTests(unittest.TestCase):
    def test_all_sixty_county_year_bridges_reconcile(self):
        for year,net in [(2023,17028),(2024,11678),(2025,10508)]:
            rows=reconcile_year(year)
            self.assertEqual(len(rows),20)
            self.assertEqual(sum(r.completed-r.removed for r in rows),net)
            self.assertTrue(all(r.reconciliation_residual==0 for r in rows))
            self.assertTrue(all(not r.occupied_population_identified and not r.technical_eligibility_identified for r in rows))

    def test_census_reference_is_october_not_january(self):
        self.assertEqual(total_stock_at(date(2022,10,1)),4580538)
        self.assertEqual(total_stock_at(date(2026,1,1)),4626092)
        for dt in [date(2022,1,1),date(2026,7,1)]:
            with self.assertRaises(ValueError):total_stock_at(dt)
        with self.assertRaises(ValueError):reconcile_year(2022)

    def test_missing_is_not_zero_and_documented_absence_marker_is_explicit(self):
        self.assertEqual(parse_count('1 619'),1619)
        self.assertEqual(parse_count('–',zero_marker_allowed=True),0)
        for v in ['','..','-','NaN','1,2','-1']:
            with self.assertRaises(ValueError):parse_count(v)

    def fixture(self):
        rows=[['Title','',''],['Terület','Szint','2025'],['Épített lakás','',''],['A','megye','2'],['B','megye','3'],['Ország összesen','ország','5'],['Más mutató','',''],['A','megye','99']]
        out=io.StringIO();csv.writer(out,delimiter=';',lineterminator='\n').writerows(rows);return out.getvalue().encode('iso-8859-2')

    def test_section_selection_and_national_reconciliation(self):
        raw=self.fixture()
        values,national=parse_section(raw,'Épített lakás',[2025],{'A':'A','B':'B'})
        self.assertEqual(values,{('A',2025):2,('B',2025):3});self.assertEqual(national,{2025:5})
        for bad in [raw.replace(b'A;megye;2\n',b''),raw.replace(b'A;megye;2\n',b'A;megye;2\nA;megye;2\n'),raw.replace(b'B;megye;3',b'B;megye;4')]:
            with self.assertRaises(ValueError):parse_section(bad,'Épített lakás',[2025],{'A':'A','B':'B'})

    def test_residual_is_reported_not_forced_to_zero(self):
        stocks,flows=load_controls();county=sorted({c for c,y in flows})[0]
        stocks[county,date(2026,1,1)]+=7
        with patch('modules.B01.public_stock_flow.load_controls',return_value=(stocks,flows)):
            rows=reconcile_year(2025)
        self.assertEqual(sum(r.reconciliation_residual for r in rows),7)


if __name__=='__main__':unittest.main()
