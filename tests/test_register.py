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
        self.note = Path(self.dir.name) / "Register"
        register.init(self.note)

    def tearDown(self):
        self.dir.cleanup()

    def pdf(self, name="download (1).pdf"):
        src = Path(self.dir.name) / "Downloads" / name
        src.parent.mkdir(exist_ok=True)
        src.write_bytes(b"%PDF-1.4 test")
        return src

    def test_add_with_pdf_moves_and_links(self):
        src, folder = self.pdf(), Path(self.dir.name) / "Received Ñ"
        register.add_with_pdf(self.note, "received", EU, src, folder)
        dest = folder / "2026-11_Anthropic_IE-1.pdf"
        self.assertTrue(dest.exists())
        self.assertFalse(src.exists())
        row = register.read(self.note, "received")[0]
        self.assertTrue(row["pdf"].endswith("Received%20%C3%91/2026-11_Anthropic_IE-1.pdf"))
        text = (self.note / "2026-11_Anthropic_IE-1.md").read_text(encoding="utf-8")
        self.assertIn(register.pdf_link(dest), text)

    def test_add_with_pdf_leaves_file_on_bad_row(self):
        src, folder = self.pdf(), Path(self.dir.name) / "Received"
        with self.assertRaises(register.RegisterError):
            register.add_with_pdf(self.note, "received", {**EU, "total": "99"}, src, folder)
        register.add(self.note, "received", EU)
        with self.assertRaisesRegex(register.RegisterError, "already in the register"):
            register.add_with_pdf(self.note, "received", EU, src, folder)
        self.assertTrue(src.exists())
        self.assertFalse(folder.exists())

    def test_add_with_pdf_never_overwrites(self):
        folder = Path(self.dir.name) / "Received"
        folder.mkdir()
        (folder / "2026-11_Anthropic_IE-1.pdf").write_bytes(b"old")
        src = self.pdf()
        with self.assertRaisesRegex(register.RegisterError, "already exists"):
            register.add_with_pdf(self.note, "received", EU, src, folder)
        self.assertTrue(src.exists())

    def test_init_creates_folder_once(self):
        self.assertFalse(register.init(self.note))
        self.assertTrue(self.note.is_dir())

    def test_note_properties(self):
        register.add(self.note, "issued", ISSUED)
        text = (self.note / "2026-10_Shakers_2026-001.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nregister: issued\nnumber: \"2026-001\"\ndate: 2026-10-31\n"))
        self.assertIn("\nbase: 1200.00\nvat_rate: 21\nvat: 252.00\nirpf: 84.00\ntotal: 1368.00\n---\n", text)

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
        first = (self.note / "2026-10_Shakers_2026-001.md").read_text(encoding="utf-8")
        register.add(self.note, "issued", {**ISSUED, "number": "2026-002", "date": "2026-11-30"})
        self.assertEqual((self.note / "2026-10_Shakers_2026-001.md").read_text(encoding="utf-8"), first)
        self.assertEqual([r["number"] for r in register.read(self.note, "issued")], ["2026-001", "2026-002"])

    def test_render_writes_nothing(self):
        out = register.note_text("received", register.validate("received", EU), "/x/Received/2026-11_Anthropic_IE-1.pdf")
        self.assertIn('pdf: "file:///x/Received/2026-11_Anthropic_IE-1.pdf"', out)
        self.assertEqual(list(self.note.iterdir()), [])

    def test_eu_services_self_assess_vat(self):
        r = register.add(self.note, "received", EU)
        self.assertEqual(r["vat"], Decimal("3.78"))
        self.assertEqual(register.read(self.note, "received")[0]["vat"], Decimal("3.78"))

    def test_unknown_kind(self):
        with self.assertRaisesRegex(register.RegisterError, "kind must be one of"):
            register.add(self.note, "received", {**EU, "kind": "other"})

    def test_note_broken_by_hand(self):
        (self.note / "bad.md").write_text("no properties here\n", encoding="utf-8")
        with self.assertRaisesRegex(register.RegisterError, "bad.md: no properties block"):
            register.read(self.note, "issued")

    def test_other_notes_ignored(self):
        (self.note / "other.md").write_text("---\nregister: other\n---\n", encoding="utf-8")
        self.assertEqual(register.read(self.note, "issued"), [])


    def test_issued_kind_defaults_to_domestic(self):
        r = register.add(self.note, "issued", ISSUED)
        self.assertEqual(r["kind"], "domestic")
        text = (self.note / "2026-10_Shakers_2026-001.md").read_text(encoding="utf-8")
        self.assertIn('\nkind: "domestic"\n', text)

    def test_issued_note_without_kind_reads_as_domestic(self):
        register.add(self.note, "issued", ISSUED)
        f = self.note / "2026-10_Shakers_2026-001.md"
        f.write_text(f.read_text(encoding="utf-8").replace('kind: "domestic"\n', ""), encoding="utf-8")
        self.assertEqual(register.read(self.note, "issued")[0]["kind"], "domestic")

    def test_issued_zero_rate_needs_a_foreign_kind(self):
        zero = {**ISSUED, "vat_rate": "0", "vat": "0", "irpf": "0", "total": "1200"}
        with self.assertRaisesRegex(register.RegisterError, "not 4, 10 or 21"):
            register.validate("issued", zero)
        self.assertEqual(register.validate("issued", {**zero, "kind": "non-eu-services", "client_tax_id": "US123"})["kind"],
                         "non-eu-services")
        self.assertEqual(register.validate("issued", {**zero, "kind": "eu-services", "client_tax_id": "de123456789"})
                         ["client_tax_id"], "DE123456789")

    def test_issued_foreign_kind_checks(self):
        zero = {**ISSUED, "vat_rate": "0", "vat": "0", "irpf": "0", "total": "1200", "client_tax_id": "DE123456789"}
        with self.assertRaisesRegex(register.RegisterError, "must be 0"):
            register.validate("issued", {**ISSUED, "kind": "eu-services", "client_tax_id": "DE123456789"})
        with self.assertRaisesRegex(register.RegisterError, "client tax ID 'B12345678' must start with an EU country code"):
            register.validate("issued", {**zero, "kind": "eu-services", "client_tax_id": "B12345678"})
        with self.assertRaisesRegex(register.RegisterError, "kind must be one of"):
            register.validate("issued", {**zero, "kind": "investment"})
        with self.assertRaisesRegex(register.RegisterError, "starts with an EU country code"):
            register.validate("issued", {**zero, "kind": "non-eu-services"})

if __name__ == "__main__":
    unittest.main()
