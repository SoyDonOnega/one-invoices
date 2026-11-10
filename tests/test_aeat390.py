import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "one-invoices" / "scripts"))
import aeat303  # noqa: E402
import aeat390  # noqa: E402
import register  # noqa: E402
from test_register import EU, ISSUED  # noqa: E402

REFS = Path(__file__).resolve().parent.parent / "skills" / "one-invoices" / "references"
CFG = {"nif": "00000000T", "surname": "Apellido Apellido", "first_name": "Nombre", "activity": "Programadores",
       "activity_code": "A03", "iae": "763"}


class Aeat390Test(unittest.TestCase):
    def setUp(self):
        self.design = aeat303.load_design(2026, "390")
        v = register.validate
        self.issued = [v("issued", ISSUED), v("issued", {**ISSUED, "number": "2026-003", "date": "2026-06-30"})]
        self.received = [v("received", EU),
                         v("received", {**EU, "number": "ES-1", "supplier": "Shop", "supplier_tax_id": "B99999999",
                                        "country": "ES", "kind": "domestic", "date": "2026-02-10", "base": "100",
                                        "vat": "10", "vat_rate": "10", "total": "110"}),
                         v("received", {**EU, "number": "PC-1", "supplier": "Shop", "supplier_tax_id": "B99999999",
                                        "country": "ES", "kind": "investment", "date": "2026-11-20", "base": "1000",
                                        "vat": "210", "total": "1210"})]

    def test_design_metadata_and_lengths(self):
        d = json.loads((REFS / "390-2026.json").read_text(encoding="utf-8"))
        self.assertEqual((d["model"], d["year"], d["version"]), ("390", 2026, "100"))
        lengths = {n: f[-1]["pos"] + f[-1]["len"] - 1 for n, f in d["pages"].items() if f[-1]["pos"]}
        self.assertEqual([lengths[p] for p in aeat390.PAGES], [1188, 1806, 531, 1840, 854, 862, 781])

    def test_boxes_match_the_design_labels(self):
        expected = {"551": "servicios - Tipo 21% - Base", "605": "corrientes bienes y servic. - Tipo 21% - Base",
                    "613": "bienes de inversion - Tipo 21% - Base", "637": "Adqui. intra. servicios - Tipo 21% - Base",
                    "47": "Total cuotas IVA", "64": "Suma de deducciones", "86": "Resultado de la liquidación",
                    "95": "Total resultados a ingresar", "108": "Total volumen de operaciones"}
        fields = {}
        for name in aeat390.PAGES[1:]:
            fields.update(aeat303.box_fields(self.design["pages"][name]))
        for box, text in expected.items():
            self.assertIn(text, fields[box]["desc"], box)

    def test_year_equals_sum_of_four_303(self):
        b, _ = aeat390.compute(self.issued, self.received, 2026)
        q = [aeat303.compute(self.issued, self.received, 2026, n)[0] for n in (1, 2, 3, 4)]
        self.assertEqual(b["47"], sum(x["27"] for x in q))
        self.assertEqual(b["64"], sum(x["45"] for x in q))
        self.assertEqual(b["65"], b["47"] - b["64"])

    def test_results_of_the_year(self):
        b, _ = aeat390.compute(self.issued, self.received, 2026)
        # Q1 ends at -10.00 (carried forward), so Q2 pays 252.00 - 10.00.
        _, log = aeat303.history(self.issued, self.received, 2027, 1)
        self.assertEqual([b4["71"] for *_, b4, _ in log], [Decimal("-10.00"), Decimal("242.00"), 0, Decimal("42.00")])
        self.assertEqual(b["95"], Decimal("284.00"))
        self.assertEqual((b["97"], b["662"]), (0, 0))
        self.assertEqual(b["99"], Decimal("2400.00"))

    def test_not_subject_issued_services(self):
        v = register.validate
        zero = {**ISSUED, "vat_rate": "0", "vat": "0", "irpf": "0"}
        issued = self.issued + [v("issued", {**zero, "number": "EU-1", "client_tax_id": "DE123456789", "kind": "eu-services",
                                             "base": "500", "total": "500"}),
                                v("issued", {**zero, "number": "US-1", "client_tax_id": "US123", "kind": "non-eu-services",
                                             "base": "300", "total": "300"})]
        b, _ = aeat390.compute(issued, self.received, 2026)
        self.assertEqual((b["99"], b["103"], b["110"]), (Decimal("2400.00"), Decimal("500.00"), Decimal("300.00")))
        self.assertEqual(b["108"], Decimal("3200.00"))
        self.assertEqual(b["47"], aeat390.compute(self.issued, self.received, 2026)[0]["47"])

    def test_file_layout(self):
        b, _ = aeat390.compute(self.issued, self.received, 2026)
        text = aeat390.build(self.design, CFG, 2026, b)
        self.assertEqual(len(text), 328 + 1188 + 1806 + 531 + 1840 + 854 + 862 + 781 + 18)
        self.assertTrue(text.startswith("<T390020260A0000><AUX>"))
        self.assertTrue(text.endswith("</T390020260A0000>"))
        p1 = text[328:]
        self.assertEqual(p1[:11], "<T39001000>")
        self.assertEqual(p1[13:22], "00000000T")


if __name__ == "__main__":
    unittest.main()
