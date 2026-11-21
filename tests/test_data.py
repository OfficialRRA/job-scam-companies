import json
import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402

PRIVATE_MARKERS = ["@", "reverserecruit", "per alex", "added via settings", "client"]


class DataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts" / "build.py")], check=True)
        cls.rows = build.load_rows()

    def test_data_is_valid(self):
        self.assertEqual(build.validate(self.rows), [])

    def test_three_formats_hold_the_same_records(self):
        with open(build.JSONL_PATH, encoding="utf-8") as f:
            records = [json.loads(line) for line in f]
        con = sqlite3.connect(build.SQLITE_PATH)
        count = con.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        con.close()
        self.assertEqual(len(records), len(self.rows))
        self.assertEqual(count, len(self.rows))
        self.assertEqual([r["id"] for r in records], [r["id"] for r in self.rows])

    def test_no_row_names_the_impersonated_brand_as_the_entity(self):
        for r in self.rows:
            if not r["impersonates"]:
                continue
            brands = {build.re.sub(r"[^a-z0-9]", "", b.lower()) for b in build.re.split(r"[/;,]", r["impersonates"])}
            self.assertNotIn(r["name_normalized"], brands, r["name"])

    def test_no_private_text_in_the_data(self):
        for r in self.rows:
            text = " ".join(v for k, v in r.items() if k not in ("source_url", "other_sources")).lower()
            for marker in PRIVATE_MARKERS:
                self.assertNotIn(marker, text, r["name"])

    def test_validate_reports_bad_rows(self):
        bad = dict(self.rows[0], source_url="", source_type="FTC", evidence_level="government_action",
                   category="fake_job_offer", domain="not a domain", match_on="name")
        errors = build.validate([bad])
        self.assertTrue(any("source_url" in e for e in errors))
        self.assertTrue(any("bad domain" in e for e in errors))

    def test_a_contributor_row_is_completed(self):
        row = dict.fromkeys(build.FIELDS, "")
        row.update(name="  Example  Fake Hiring LLC ", category="fake_job_offer", source_type="FTC",
                   source_url="https://www.ftc.gov/example", source_date="2026-01-02",
                   domain="https://www.Example-Fake-Hiring.com/jobs")
        self.assertTrue(build.fill_derived([row]))
        self.assertEqual(build.validate([row]), [])
        self.assertEqual(row["name_normalized"], "examplefakehiringllc")
        self.assertEqual(row["domain"], "example-fake-hiring.com")
        self.assertEqual(row["match_on"], "name")
        self.assertRegex(row["id"], r"^rra-[0-9a-f]{10}$")

    def test_a_consumer_report_row_without_a_domain_is_rejected(self):
        row = dict.fromkeys(build.FIELDS, "")
        row.update(name="Some Real Sounding Co", category="fake_job_offer", source_type="BBB",
                   source_url="https://www.bbb.org/x", source_date="2026")
        build.fill_derived([row])
        self.assertTrue(any("needs a domain" in e for e in build.validate([row])))

    def test_stored_rows_need_no_completion(self):
        self.assertFalse(build.fill_derived([dict(r) for r in self.rows]))

    def test_lookalike_file_matches_the_records(self):
        import csv
        with open(ROOT / "data" / "lookalike_domains.csv", newline="", encoding="utf-8") as f:
            got = list(csv.DictReader(f))
        want = set()
        for r in self.rows:
            for b in [b.strip() for b in r["impersonates"].split(" / ") if b.strip()]:
                for d in [r["domain"], *build.alias_domains(r)]:
                    if d:
                        want.add((b, d))
        self.assertEqual({(g["impersonated_business"], g["lookalike_domain"]) for g in got}, want)
        self.assertEqual(len(got), len(want))

    def test_every_domain_is_in_the_sqlite_domain_table(self):
        con = sqlite3.connect(ROOT / "data" / "companies.sqlite")
        got = {d for (d,) in con.execute("SELECT domain FROM company_domains")}
        con.close()
        want = {d for r in self.rows for d in [r["domain"], *build.alias_domains(r)] if d}
        self.assertEqual(got, want)

    def test_a_bad_date_and_a_repeated_alias_domain_are_reported(self):
        rows = [dict(r) for r in self.rows[:2]]
        rows[0]["source_date"] = "2026/05"
        rows[1]["aliases"] = rows[0]["domain"] or "example-scam.com"
        rows[0]["aliases"] = "example-scam.com"
        errors = "\n".join(build.validate(rows))
        self.assertIn("source_date", errors)
        self.assertIn("alias domain", errors)

    def test_companion_files_have_the_documented_header(self):
        import csv
        heads = {
            "dol_debarred_employers.csv": "name,city,state,program,list,reason,start_date,end_date,source_url,retrieved_date",
            "staffing_wage_violations.csv": ",".join(__import__("filter_whd").OUT_COLUMNS),
        }
        for name, head in heads.items():
            with open(ROOT / "data" / name, newline="", encoding="utf-8") as f:
                self.assertEqual(",".join(next(csv.reader(f))), head, name)

    def test_names_with_commas_and_quotes_survive(self):
        tricky = [r for r in self.rows if "," in r["name"] or '"' in r["name"]]
        self.assertTrue(tricky)
        con = sqlite3.connect(build.SQLITE_PATH)
        for r in tricky[:20]:
            got = con.execute("SELECT name FROM companies WHERE id = ?", (r["id"],)).fetchone()[0]
            self.assertEqual(got, r["name"])
        con.close()


if __name__ == "__main__":
    unittest.main()
