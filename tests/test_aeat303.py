import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "one-invoices" / "scripts"))
import aeat303  # noqa: E402
import register  # noqa: E402
from test_register import EU, ISSUED  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden"
CFG = {"nif": "00000000T", "name": "Apellido Apellido Nombre"}


def field(text: str, page_start: int, f: dict) -> str:
    return text[page_start + f["pos"] - 1: page_start + f["pos"] - 1 + f["len"]]


class Aeat303Test(unittest.TestCase):
    def setUp(self):
        self.design = aeat303.load_design(2026)
        self.dir = tempfile.TemporaryDirectory()
        self.note = Path(self.dir.name) / "Register"
        register.init(self.note)
        register.add(self.note, "issued", ISSUED)
        register.add(self.note, "received", EU)
        register.add(self.note, "received", {**EU, "number": "ES-1", "supplier": "Shop", "supplier_tax_id": "B99999999",
                                             "country": "ES", "kind": "domestic", "base": "100", "vat": "21", "total": "121"})
        register.add(self.note, "received", {**EU, "number": "ND-1", "supplier": "Lunch", "supplier_tax_id": "B88888888",
                                             "country": "ES", "kind": "not-deductible", "base": "10", "vat": "1", "vat_rate": "10",
                                             "total": "11"})
        register.add(self.note, "issued", {**ISSUED, "number": "2027-001", "date": "2027-01-31"})

    def tearDown(self):
        self.dir.cleanup()

    def boxes(self):
        return aeat303.compute(register.read(self.note, "issued"), register.read(self.note, "received"), 2026, 4)

    def test_boxes(self):
        b, src = self.boxes()
        self.assertEqual((b["07"], b["09"]), (Decimal("1200.00"), Decimal("252.00")))
        self.assertEqual((b["10"], b["11"], b["36"], b["37"]), (Decimal("18.00"), Decimal("3.78"), Decimal("18.00"), Decimal("3.78")))
        self.assertEqual((b["28"], b["29"]), (Decimal("100.00"), Decimal("21.00")))
        self.assertEqual(b["27"], Decimal("255.78"))
        self.assertEqual(b["45"], Decimal("24.78"))
        self.assertEqual(b["71"], Decimal("231.00"))
        self.assertIn("issued 2026-001 (2026-10-31)", src["09"])
        self.assertNotIn("ND-1", " ".join(sum(src.values(), [])))

    def test_not_subject_issued_services(self):
        zero = {**ISSUED, "vat_rate": "0", "vat": "0", "irpf": "0"}
        register.add(self.note, "issued", {**zero, "number": "EU-1", "client": "Acme GmbH", "client_tax_id": "DE123456789",
                                           "kind": "eu-services", "base": "500", "total": "500"})
        register.add(self.note, "issued", {**zero, "number": "US-1", "client": "Acme Inc", "client_tax_id": "US123",
                                           "kind": "non-eu-services", "base": "300", "total": "300"})
        b, src = self.boxes()
        self.assertEqual((b["59"], b["120"]), (Decimal("500.00"), Decimal("300.00")))
        self.assertEqual((b["07"], b["27"], b["71"]), (Decimal("1200.00"), Decimal("255.78"), Decimal("231.00")))
        self.assertEqual(src["59"], ["issued EU-1 (2026-10-31)"])
        text = aeat303.build(self.design, CFG, 2026, 4, b, "I", "")
        f = {x["n"]: x for x in self.design["pages"]["DP30303"]}
        start3 = 328 + 1581
        self.assertEqual(field(text, start3, f[5]), "00000000000050000")
        self.assertEqual(field(text, start3, f[7]), "00000000000030000")

    def test_file_layout(self):
        b, _ = self.boxes()
        text = aeat303.build(self.design, CFG, 2026, 4, b, "I", "")
        p = self.design["pages"]
        self.assertTrue(text.startswith("<T303020264T0000><AUX>"))
        self.assertTrue(text.endswith("</T303020264T0000>"))
        start1 = 328
        self.assertEqual(text[start1:start1 + 11], "<T30301000>")
        f = {x["n"]: x for x in p["DP30301"]}
        self.assertEqual(field(text, start1, f[6]), "I")
        self.assertEqual(field(text, start1, f[8]).rstrip(), "APELLIDO APELLIDO NOMBRE")
        self.assertEqual(field(text, start1, f[42]), "02100")
        self.assertEqual(field(text, start1, f[43]), "00000000000025200")
        self.assertEqual(field(text, start1, f[86]), "00000000000023100")
        start3 = start1 + 1581
        self.assertEqual(text[start3:start3 + 11], "<T30303000>")
        self.assertEqual(len(text), 328 + 1581 + 1017 + 823 + 18)

    def test_negative_result_uses_n_prefix(self):
        f = {"n": 1, "len": 17, "type": "N", "content": "", "desc": "x"}
        self.assertEqual(aeat303.encode(f, Decimal("-12.34")), "N0000000000001234")
        with self.assertRaises(aeat303.GenError):
            aeat303.encode({**f, "type": "Num"}, Decimal("-1"))

    def test_text_is_iso_8859_1_upper_without_accents(self):
        f = {"n": 1, "len": 12, "type": "An", "content": "", "desc": "x"}
        self.assertEqual(aeat303.encode(f, "Óñega, Façé"), "OÑEGA  FAÇE ")

    def test_zero_quarter(self):
        b, _ = aeat303.compute([], [], 2026, 3)
        self.assertEqual(b["71"], Decimal(0))
        self.assertIn("zero return", aeat303.summary(self.design, 2026, 3, b, {}, "N"))

    def test_year_without_design(self):
        with self.assertRaisesRegex(aeat303.GenError, "no record design of model 303 for 2031"):
            aeat303.load_design(2031)

    def test_carry_forward_from_negative_quarter(self):
        # Q4 2026: one domestic purchase only -> -300.00; Q1 2027: 500.00 before compensation.
        buy = {**EU, "number": "PC-1", "supplier": "Shop", "supplier_tax_id": "B99999999", "country": "ES",
               "kind": "investment", "date": "2026-12-10", "base": "1428.57", "vat": "300.00", "total": "1728.57"}
        sale = {**ISSUED, "number": "2027-01", "date": "2027-02-28", "base": "2380.95", "vat": "500.00", "irpf": "0",
                "total": "2880.95"}
        issued, received = [register.validate("issued", sale)], [register.validate("received", buy)]
        chain = aeat303.pending(issued, received, 2027, 1)
        self.assertEqual(chain, [(2026, 4, Decimal("300.00"))])
        b, _ = aeat303.compute(issued, received, 2027, 1, Decimal("300.00"))
        self.assertEqual((b["110"], b["78"], b["87"], b["71"]),
                         (Decimal("300.00"), Decimal("300.00"), Decimal(0), Decimal("200.00")))
        self.assertEqual(aeat303.pending(issued, received, 2027, 2), [])

    def test_carry_larger_than_result_stays_pending(self):
        b, _ = aeat303.compute([], [], 2027, 1, Decimal("50.00"))
        self.assertEqual((b["78"], b["87"], b["71"]), (Decimal(0), Decimal("50.00"), Decimal(0)))

    def test_config_pointer(self):
        real = Path(self.dir.name) / "one-invoices.json"
        real.write_text(json.dumps(CFG), encoding="utf-8")
        ptr = Path(self.dir.name) / "config.json"
        ptr.write_text(json.dumps({"config": str(real)}), encoding="utf-8")
        self.assertEqual(aeat303.load_config(str(ptr)), CFG)
        self.assertEqual(aeat303.load_config(str(real)), CFG)

    def test_eu_supplier_needs_country_prefix(self):
        with self.assertRaisesRegex(register.RegisterError, "EU country code"):
            register.validate("received", {**EU, "supplier_tax_id": "1234567X"})

    def test_cli_writes_and_refuses_overwrite(self):
        out = Path(self.dir.name) / "out"
        cfg = Path(self.dir.name) / "config.json"
        cfg.write_text(json.dumps({**CFG, "register_dir": str(self.note), "output_dir": str(out)}), encoding="utf-8")
        self.assertEqual(aeat303.main([str(cfg), "2026", "4"]), 0)
        self.assertTrue((out / "303" / "2026-T4.txt").exists())
        self.assertIn("| [71] |", (out / "303" / "2026-T4.md").read_text(encoding="utf-8"))
        self.assertEqual(aeat303.main([str(cfg), "2026", "4"]), 1)
        self.assertEqual(aeat303.main([str(cfg), "2026", "4", "--force", "--type", "U", "--iban", "ES0000000000000000000000"]), 0)


@unittest.skipUnless((GOLDEN / "golden.json").exists(), "no AEAT export in tests/golden/ yet (task 4.3)")
class GoldenTest(unittest.TestCase):
    """tests/golden/golden.json: {"year", "quarter", "type", "iban", "nif", "name", "boxes": {"07": "1200.00", ...},
    "file": "<file exported from the AEAT site>"}."""

    def test_matches_aeat_export(self):
        g = json.loads((GOLDEN / "golden.json").read_text(encoding="utf-8"))
        boxes = {k: Decimal(v) for k, v in g["boxes"].items()}
        text = aeat303.build(aeat303.load_design(g["year"]), g, g["year"], g["quarter"], boxes, g["type"], g.get("iban", ""))
        expected = (GOLDEN / g["file"]).read_bytes().decode("latin-1")
        self.assertEqual(text, expected)


if __name__ == "__main__":
    unittest.main()
