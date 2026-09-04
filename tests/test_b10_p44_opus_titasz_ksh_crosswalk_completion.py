import csv
from pathlib import Path
import unittest

from modules.B10.integration_closure_contract import current_b10_closure_assessment


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
COMPLETION = ROOT / "registry/dso_service_area_membership_crosswalk_opus_p44.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
MODULE_STATUS = ROOT / "registry/module_status.csv"
DOC = ROOT / "docs/source_packs/P44_B10_OPUS_TITASZ_KSH_CROSSWALK_COMPLETION.md"

OPUS = "SRC-B10-OPUS-TITASZ-M1-2026"
KSH_2019 = "SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS"

EXPECTED_P44 = {
    tuple(line.split("|", 1))
    for line in """26091|Lónya
07995|Lövőpetri
29984|Magosliget
16629|Magy
03683|Magyarhomorog
02626|Martfű
02088|Mánd
17826|Mándok
19655|Máriapócs
33224|Márokpapi
18874|Mátészalka
20668|Mátyus
30234|Mesterszállás
26286|Mezőhék
32656|Mezőladány
31033|Mezőpeterd
18847|Mezősas
04260|Mezőtúr
29799|Méhtelek
07463|Mérk
24217|Mikepércs
31750|Milota
25894|Monostorpályi
04710|Nagyar
22743|Nagycserkesz
21485|Nagydobos
06488|Nagyecsed
27155|Nagyhalász
09478|Nagyhegyes
26976|Nagyhódos
21689|Nagyiván
24785|Nagykálló
08907|Nagykereki
15574|Nagykörű
06309|Nagyrábé
06318|Nagyrév
27988|Nagyszekeres
33783|Nagyvarsány
08420|Napkor
19211|Nábrád
28103|Nádudvar
27119|Nemesborzova
14003|Nyíracsád
06187|Nyíradony
32294|Nyírábrány
14845|Nyírbátor
15802|Nyírbéltek
31158|Nyírbogát
28802|Nyírbogdány
07904|Nyírcsaholy
25973|Nyírcsászári
05041|Nyírderzs
17206|Nyíregyháza
28440|Nyírgelse
09238|Nyírgyulaj
14696|Nyíribrony
31477|Nyírjákó
18290|Nyírkarász
32452|Nyírkáta
25928|Nyírkércs
11095|Nyírlövő
11271|Nyírlugos
12274|Nyírmada
32382|Nyírmártonfalva
23269|Nyírmeggyes
26365|Nyírmihálydi
10807|Nyírparasznya
33145|Nyírpazony
03878|Nyírpilis
28060|Nyírtass
13550|Nyírtelek
09256|Nyírtét
12098|Nyírtura
16522|Nyírvasvári
11129|Olcsva
10834|Olcsvaapáti
22284|Ófehértó
27924|Ópályi
28006|Öcsöd
31769|Ököritófülpös
26550|Ömböly
29382|Örményes
09025|Őr
29559|Panyola
27748|Pap
32577|Papos
31972|Paszab
12186|Pátroha
23685|Pátyod
17084|Penészlek
32692|Penyige
17224|Petneháza
03391|Piricse
11837|Pocsaj
23117|Polgár
17215|Porcsalma
11244|Pócspetri
13860|Pusztadobos
10162|Püspökladány
14739|Rakamaz
31857|Ramocsaháza
14207|Rákóczifalva
12423|Rákócziújfalu
09061|Rápolt
21573|Rétközberencs
24581|Rohod
17428|Rozsály
26116|Sáp
25007|Sáránd
23940|Sárrétudvari
04491|Sényő
23889|Sonkád
19169|Szabolcs
22053|Szabolcsbáka
03586|Szabolcsveresmart
05874|Szajol
04774|Szakoly
18005|Szamosangyalos
22017|Szamosbecs
16300|Szamoskér
10436|Szamossályi
13046|Szamosszeg
31273|Szamosújlak
30085|Szamostatárfalva
23870|Szarvas
31237|Szatmárcseke
05777|Szászberek
21883|Szeghalom
20428|Szelevény
19099|Szentpéterszeg
33437|Szerep
31088|Székely
27854|Szolnok
34388|Szorgalmatos
04312|Tarpa
29911|Tákos
19691|Tetétlen
33358|Terem
31042|Tépe
23214|Téglás
08952|Tiborszállás
24475|Timár
09423|Tiszaadony
17817|Tiszabecs
03850|Tiszabercel
20172|Tiszabezdéd
10773|Tiszabő
22770|Tiszabura
15644|Tiszacsege
24448|Tiszacsécse
06433|Tiszadada
16230|Tiszaderzs
12593|Tiszadob
09113|Tiszaeszlár
13815|Tiszaföldvár
29726|Tiszafüred
30304|Tiszagyenda
30845|Tiszagyulaháza
28699|Tiszaigar
20446|Tiszainoka
29346|Tiszajenő
08554|Tiszakanyár
04446|Tiszakerecseny
30623|Tiszakécske
08794|Tiszakóród
30386|Tiszakürt
23524|Tiszalök
11907|Tiszamogyorós
27252|Tiszanagyfalu
15787|Tiszaörs
03373|Tiszapüspöki
10205|Tiszarád
20181|Tiszaroff
21494|Tiszasas
17695|Tiszasüly
13541|Tiszaszalka
22789|Tiszaszentimre
27544|Tiszaszentmárton
07852|Tiszaszőlős
14447|Tiszatelek
09627|Tiszatenyő
14094|Tiszaug
07597|Tiszavasvári
31866|Tiszavárkony
33747|Tiszavid
27261|Tisztaberek
20260|Tivadar
25876|Told
09557|Tomajmonostora
16957|Tornyospálca
07490|Tószeg
27313|Törökszentmiklós
13213|Tunyogmatolcs
13602|Túristvándi
28228|Túrkeve
08998|Túrricse
09919|Tuzsér
31398|Tyukod
26611|Újfehértó
33659|Újdombrád
23393|Újiráz
10117|Újkenéz
20419|Újléta
15291|Újszász
32568|Újszentmargita
11925|Újtikos
28981|Ura
31820|Uszka
18591|Vaja
27100|Vasmegyer
06938|Vállaj
27322|Vámosatya
08934|Vámosoroszi
08989|Vámospércs
16762|Váncsod
18324|Vásárosnamény
11138|Vekerd
21157|Vezseny
14836|Zagyvarékas
06275|Zajta
16203|Záhony
06257|Zsadány
28750|Zsarolyán
04817|Zsáka
13037|Zsurk""".splitlines()
}


class B10P44OpusTitaszKshCrosswalkCompletionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def historical_opus_rows(self):
        return [row for row in self.rows(TRANCHE) if row["operator_id"] == "OPUS_TITASZ"]

    def p44_rows(self):
        return self.rows(COMPLETION)

    def opus_rows(self):
        return self.historical_opus_rows() + self.p44_rows()

    def test_exact_225_p44_name_code_pairs_are_materialized(self):
        rows = self.p44_rows()
        self.assertEqual(225, len(rows))
        actual = {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}
        self.assertEqual(EXPECTED_P44, actual)

    def test_current_opus_population_is_exactly_395_and_p44_adds_225(self):
        self.assertEqual(170, len(self.historical_opus_rows()))
        self.assertEqual(225, len(self.p44_rows()))
        rows = self.opus_rows()
        self.assertEqual(395, len(rows))
        self.assertEqual(395, len({(row["ksh_settlement_code"], row["settlement_name"]) for row in rows}))

    def test_all_395_opus_rows_preserve_direct_observed_whole_settlement_semantics(self):
        rows = self.opus_rows()
        self.assertEqual(395, len(rows))
        self.assertTrue(all(row["operator_id"] == "OPUS_TITASZ" for row in rows))
        self.assertTrue(all(row["service_area_id"] == "OPUS_TITASZ:SERVICE_AREA" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["usage_location_requirement"] == "NONE" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(set(row["source_ids"].split(";")) == {OPUS, KSH_2019} for row in rows))

    def test_p44_closes_exact_current_opus_m1_population_at_serial_395(self):
        pairs = {(row["ksh_settlement_code"], row["settlement_name"]) for row in self.opus_rows()}
        self.assertIn(("26091", "Lónya"), pairs)
        self.assertIn(("13037", "Zsurk"), pairs)
        self.assertEqual(395, len(pairs))

    def test_source_registry_marks_operator_m1_complete_without_national_promotion(self):
        by_operator = {row["operator_id"]: row for row in self.rows(SOURCES)}
        src = by_operator["OPUS_TITASZ"]
        self.assertEqual(OPUS, src["source_id"])
        self.assertEqual("OFFICIAL_CURRENT_M1_ATTACHMENT", src["source_kind"])
        self.assertEqual("CURRENT_2026", src["currentness_status"])
        self.assertEqual("COMPLETE_OPERATOR_M1_MATERIALIZED", src["extraction_status"])
        self.assertEqual("M1_SETTLEMENT_LIST", src["membership_semantics"])
        for marker in (
            "P20", "1-10", "P40", "11-50", "P41", "51-90",
            "P42", "91-130", "P43", "131-170", "P44", "171-395",
            "395 OBS", "complete current OPUS TITÁSZ M1 settlement population",
            "complete OPUS operator-level M1 settlement coverage only",
        ):
            self.assertIn(marker, src["notes"])

    def test_all_ksh_codes_remain_unique_across_historical_and_completion_surfaces(self):
        rows = self.rows(TRANCHE) + self.rows(COMPLETION)
        codes = [row["ksh_settlement_code"] for row in rows]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertTrue(all(len(code) == 5 and code.isdigit() for code in codes))

    def test_national_crosswalk_blockers_and_readiness_remain_fail_closed(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))
        blockers = set(current_b10_closure_assessment().blocking_refs)
        self.assertIn("NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK", blockers)
        self.assertIn("PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED", blockers)

        by_module = {row["module_id"]: row for row in self.rows(MODULE_STATUS)}
        self.assertEqual("IN_PROGRESS", by_module["B10"]["status"])
        self.assertEqual("15", by_module["B10"]["readiness_percent"])

    def test_source_pack_preserves_completion_boundary_and_non_claims(self):
        text = DOC.read_text(encoding="utf-8")
        for marker in (
            "serials **171–395**",
            "225 whole-settlement memberships",
            "395 materialized rows",
            "serial **171, Lónya**",
            "serial **395, Zsurk**",
            "COMPLETE_OPERATOR_M1_MATERIALIZED",
            "historical tranche + P44 completion tranche",
            "SETTLEMENT NAME != KSH SETTLEMENT ID",
            "KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP",
            "WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP",
            "DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE",
            "COMPLETE OPUS OPERATOR M1 != COMPLETE NATIONAL CROSSWALK",
            "PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION",
            "evidence_status = OBS",
            "readiness remains **15%**",
        ):
            self.assertIn(marker, text)

        for non_claim in (
            "complete national KSH-to-DSO membership coverage",
            "exact programme entity-to-node mapping",
            "headroom sufficiency",
            "limiting-node status",
            "reinforcement need",
            "programme-incremental CAPEX",
        ):
            self.assertIn(non_claim, text)


if __name__ == "__main__":
    unittest.main()
