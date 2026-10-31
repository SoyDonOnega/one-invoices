import json
import unittest
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent / "skills" / "one-invoices" / "references"


class DesignTest(unittest.TestCase):
    def setUp(self):
        self.d = json.loads((REFS / "303-2026.json").read_text(encoding="utf-8"))

    def test_metadata(self):
        self.assertEqual((self.d["model"], self.d["year"], self.d["version"]), ("303", 2026, "101"))
        self.assertTrue(self.d["source_url"].startswith("https://sede.agenciatributaria.gob.es/"))

    def test_fields_are_contiguous(self):
        for name, fields in self.d["pages"].items():
            numbered = [f for f in fields if f["pos"] is not None]
            self.assertEqual([f["n"] for f in fields], list(range(1, len(fields) + 1)), name)
            for a, b in zip(numbered, numbered[1:]):
                self.assertEqual(a["pos"] + a["len"], b["pos"], f"{name}: field {a['n']} -> {b['n']}")

    def test_page_lengths(self):
        lengths = {n: f[-1]["pos"] + f[-1]["len"] - 1 for n, f in self.d["pages"].items() if f[-1]["pos"]}
        self.assertEqual(lengths["DP30301"], 1581)
        self.assertEqual(lengths["DP30303"], 1017)
        self.assertEqual(lengths["DP303DID"], 823)

    def test_comp_column_does_not_shift_descriptions(self):
        # DP30302 and DP30305 have an extra "Comp" column before "Descripción".
        for name in ("DP30302", "DP30305"):
            self.assertTrue(all(f["desc"] not in ("", "C") for f in self.d["pages"][name]), name)


if __name__ == "__main__":
    unittest.main()
