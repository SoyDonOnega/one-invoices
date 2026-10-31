import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "one-invoices" / "scripts"))
import register  # noqa: E402

ISSUED = {"number": "2026-001", "date": "2026-10-31", "client": "Shakers", "client_tax_id": "b12345678",
          "base": "1200", "vat_rate": "21", "vat": "252", "irpf": "84", "total": "1368", "pdf": ""}
EU = {"number": "IE-1", "date": "2026-11-05", "supplier": "Anthropic Ireland", "supplier_tax_id": "IE1234567X",
      "country": "IE", "kind": "eu-services", "base": "18.00", "vat_rate": "21", "vat": "0", "total": "18.00", "pdf": ""}


class RegisterTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.note = Path(self.dir.name) / "Facturación.md"
        self.note.write_text("# Facturación\n\nIntro text.\n", encoding="utf-8")
        register.init(self.note)

    def tearDown(self):
        self.dir.cleanup()

    def test_init_adds_both_tables_once(self):
        self.assertEqual(register.init(self.note), [])
        text = self.note.read_text(encoding="utf-8")
        self.assertIn("Intro text.", text)
        self.assertEqual(text.count("## Issued invoices"), 1)
        self.assertEqual(text.count("## Received invoices"), 1)

    def test_add_and_read(self):
        register.add(self.note, "issued", ISSUED)
        rows = register.read(self.note, "issued")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["total"], Decimal("1368.00"))
        self.assertEqual(rows[0]["client_tax_id"], "B12345678")

    def test_totals_must_add_up(self):
        with self.assertRaisesRegex(register.RegisterError, "total is 1300.00"):
            register.add(self.note, "issued", {**ISSUED, "total": "1300"})

    def test_duplicate_refused(self):
        register.add(self.note, "issued", ISSUED)
        with self.assertRaisesRegex(register.RegisterError, "already in the register"):
            register.add(self.note, "issued", ISSUED)

    def test_append_only(self):
        register.add(self.note, "issued", ISSUED)
        before = self.note.read_text(encoding="utf-8")
        register.add(self.note, "issued", {**ISSUED, "number": "2026-002"})
        after = self.note.read_text(encoding="utf-8")
        first_row = [l for l in before.splitlines() if "2026-001" in l][0]
        self.assertIn(first_row, after)
        self.assertLess(after.index("2026-001"), after.index("2026-002"))

    def test_eu_services_self_assess_vat(self):
        r = register.add(self.note, "received", EU)
        self.assertEqual(r["vat"], Decimal("3.78"))
        self.assertEqual(register.read(self.note, "received")[0]["vat"], Decimal("3.78"))

    def test_unknown_kind(self):
        with self.assertRaisesRegex(register.RegisterError, "kind must be one of"):
            register.add(self.note, "received", {**EU, "kind": "other"})

    def test_header_changed_by_hand(self):
        text = self.note.read_text(encoding="utf-8").replace("| Nº | Date | Client |", "| No | Date | Client |")
        self.note.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(register.RegisterError, "column 1: expected 'Nº', found 'No'"):
            register.add(self.note, "issued", ISSUED)


if __name__ == "__main__":
    unittest.main()
