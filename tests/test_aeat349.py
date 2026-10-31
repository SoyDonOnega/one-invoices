import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "skills" / "one-invoices" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import aeat303  # noqa: E402
import aeat349  # noqa: E402
import register  # noqa: E402
from test_register import EU, ISSUED  # noqa: E402

CFG = {"nif": "00000000T", "name": "Apellido Apellido Nombre", "phone": "600000000", "contact_name": "Apellido Nombre"}


class Aeat349Test(unittest.TestCase):
    def setUp(self):
        self.design = aeat303.load_design(2026, "349")
        self.received = [register.validate("received", EU),
                         register.validate("received", {**EU, "number": "IE-2", "date": "2026-12-05", "base": "20.00",
                                                        "total": "20.00"}),
                         register.validate("received", {**EU, "number": "IE-3", "date": "2027-01-05"})]
        self.issued = [register.validate("issued", ISSUED)]

    def test_design_records_are_500_long(self):
        for name, fields in self.design["pages"].items():
            for a, b in zip(fields, fields[1:]):
                self.assertEqual(a["pos"] + a["len"], b["pos"], name)
            self.assertEqual(fields[-1]["pos"] + fields[-1]["len"] - 1, 500, name)

    def test_one_record_per_operator_and_key(self):
        ops = aeat349.operations(self.issued, self.received, 2026, 4)
        self.assertEqual(list(ops), [("IE1234567X", "I")])
        self.assertEqual(ops[("IE1234567X", "I")]["base"], Decimal("38.00"))

    def test_file_layout(self):
        ops = aeat349.operations(self.issued, self.received, 2026, 4)
        text = aeat349.build(self.design, CFG, 2026, 4, ops, "3492026400000")
        recs = text.split("\r\n")
        self.assertEqual(recs[-1], "")
        t1, t2 = recs[0], recs[1]
        self.assertEqual([len(r) for r in recs[:-1]], [500, 500])
        self.assertEqual(t1[:17], "13492026" + "00000000T")
        self.assertEqual(t1[135:137], "4T")
        self.assertEqual(t1[137:146], "000000001")
        self.assertEqual(t1[146:161], "000000000003800")
        self.assertEqual(t2[:17], "23492026" + "00000000T")
        self.assertEqual(t2[75:92], "IE" + "1234567X".ljust(15))
        self.assertEqual(t2[132], "I")
        self.assertEqual(t2[133:146], "0000000003800")

    def test_nothing_to_declare_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            note = Path(d) / "Register"
            register.init(note)
            cfg = Path(d) / "c.json"
            cfg.write_text(json.dumps({**CFG, "register_dir": str(note), "output_dir": d}), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "aeat349.py"), str(cfg), "2026", "4"],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)
            self.assertIn("nothing to declare", r.stdout)
            self.assertFalse((Path(d) / "349").exists())


if __name__ == "__main__":
    unittest.main()
