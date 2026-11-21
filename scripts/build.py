"""Complete and validate data/companies.csv, then write the JSONL and SQLite files.

A new row needs only name, category, source_type, source_url, and source_date
(plus domain and impersonates when they apply). This script fills in id,
name_normalized, evidence_level, match_on, domain_source, and added_date.

Usage: python3 scripts/build.py
"""
import csv
import datetime
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "companies.csv"
JSONL_PATH = ROOT / "data" / "companies.jsonl"
SQLITE_PATH = ROOT / "data" / "companies.sqlite"

FIELDS = [
    "id", "name", "aliases", "name_claimed", "name_normalized", "domain", "domain_source",
    "linkedin_url", "ats_url", "category", "evidence_level", "match_on",
    "impersonates", "source_type", "source_url", "source_date", "other_sources",
    "added_date",
]
LIST_FIELDS = {"aliases", "other_sources"}
EVIDENCE_LEVELS = {
    "government_action", "consumer_reports", "news_or_watchdog", "security_research",
    "university_advisory", "impersonated_employer_alert", "rra_internal",
}
EVIDENCE_BY_SOURCE = {
    "FTC": "government_action", "DOJ": "government_action", "FBI": "government_action",
    "CFPB": "government_action", "USPIS": "government_action", "SEC": "government_action",
    "state_AG": "government_action", "other_state": "government_action",
    "court_filing": "government_action",
    "BBB": "consumer_reports",
    "employer_fraud_alert": "impersonated_employer_alert",
    "university_list": "university_advisory",
    "university_career_services": "university_advisory",
    "security_research": "security_research", "platform_alert": "security_research",
    "news_investigation": "news_or_watchdog", "consumer_org": "news_or_watchdog",
    "rra_internal": "rra_internal",
}
INTERNAL_CATEGORIES = {"mlm", "insurance_agency_recruiting", "commission_only_direct_sales"}
DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


def load_rows(path=CSV_PATH):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"unexpected header: {reader.fieldnames}")
        return list(reader)


def normalize_name(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


def fill_derived(rows):
    """Fill the fields that a contributor may leave blank. Return True if a row changed."""
    changed = False
    for r in rows:
        before = dict(r)
        r["name"] = " ".join(r["name"].split())
        r["domain"] = re.sub(r"^www\.", "", re.sub(r"^https?://", "", r["domain"].strip().lower()).split("/")[0])
        if not r["name_normalized"]:
            r["name_normalized"] = normalize_name(r["name"])
        if not r["id"] and r["name_normalized"]:
            r["id"] = "rra-" + hashlib.sha1(r["name_normalized"].encode()).hexdigest()[:10]
        if not r["evidence_level"]:
            r["evidence_level"] = EVIDENCE_BY_SOURCE.get(r["source_type"], "")
        if not r["match_on"]:
            r["match_on"] = "name" if r["evidence_level"] in ("government_action", "rra_internal") else "domain"
        if r["domain"] and not r["domain_source"]:
            r["domain_source"] = "cited_source"
        if not r["added_date"]:
            r["added_date"] = datetime.date.today().isoformat()
        changed = changed or r != before
    return changed


def write_csv(rows, path=CSV_PATH):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def validate(rows):
    """Return a list of error strings. An empty list means the data is valid."""
    errors, ids, names, domains = [], set(), set(), set()
    for n, r in enumerate(rows, start=2):
        where = f"line {n} ({r['name']!r})"
        for key in ("id", "name", "name_normalized", "category", "source_type", "added_date"):
            if not r[key].strip():
                errors.append(f"{where}: {key} is blank")
        if r["source_type"] not in EVIDENCE_BY_SOURCE:
            errors.append(f"{where}: unknown source_type {r['source_type']!r}")
        if r["id"] in ids:
            errors.append(f"{where}: duplicate id")
        if r["name_normalized"] in names:
            errors.append(f"{where}: duplicate name_normalized")
        if r["domain"]:
            if not DOMAIN_RE.match(r["domain"]):
                errors.append(f"{where}: bad domain {r['domain']!r}")
            if r["domain"] in domains:
                errors.append(f"{where}: duplicate domain")
            if not r["domain_source"]:
                errors.append(f"{where}: domain has no domain_source")
            domains.add(r["domain"])
        elif r["match_on"] == "domain":
            errors.append(f"{where}: match_on is domain but domain is blank")
        if r["evidence_level"] not in ("government_action", "rra_internal"):
            # A name from these sources can belong to a real business that the
            # operation copied. The record must identify a domain.
            if not r["domain"] or r["match_on"] != "domain":
                errors.append(f"{where}: this source type needs a domain and match_on = domain")
        ids.add(r["id"])
        names.add(r["name_normalized"])
        if r["evidence_level"] not in EVIDENCE_LEVELS:
            errors.append(f"{where}: unknown evidence_level")
        if r["match_on"] not in ("name", "domain"):
            errors.append(f"{where}: unknown match_on")
        internal = r["source_type"] == "rra_internal"
        if internal != (r["evidence_level"] == "rra_internal"):
            errors.append(f"{where}: source_type and evidence_level disagree")
        if internal != (r["category"] in INTERNAL_CATEGORIES):
            errors.append(f"{where}: category does not fit the source_type")
        if not internal and not re.match(r"^https?://", r["source_url"]):
            errors.append(f"{where}: source_url is missing or not a URL")
        for key in ("linkedin_url", "ats_url"):
            if r[key] and not r[key].startswith("https://"):
                errors.append(f"{where}: {key} is not an https URL")
    return errors


def to_record(row):
    rec = {}
    for key in FIELDS:
        value = row[key]
        if key in LIST_FIELDS:
            rec[key] = [v.strip() for v in value.split(";") if v.strip()]
        else:
            rec[key] = value if value != "" else None
    return rec


def write_jsonl(rows, path=JSONL_PATH):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(to_record(r), ensure_ascii=False) + "\n")


def write_sqlite(rows, path=SQLITE_PATH):
    Path(path).unlink(missing_ok=True)
    con = sqlite3.connect(path)
    cols = ", ".join(f"{c} TEXT" + (" PRIMARY KEY" if c == "id" else "") for c in FIELDS)
    con.execute(f"CREATE TABLE companies ({cols})")
    marks = ", ".join("?" for _ in FIELDS)
    con.executemany(
        f"INSERT INTO companies VALUES ({marks})",
        [[r[c] if r[c] != "" else None for c in FIELDS] for r in rows],
    )
    con.execute("CREATE INDEX idx_companies_domain ON companies(domain)")
    con.execute("CREATE INDEX idx_companies_name_normalized ON companies(name_normalized)")
    con.commit()
    con.execute("VACUUM")
    con.close()


def main():
    rows = load_rows()
    changed = fill_derived(rows)
    errors = validate(rows)
    if errors:
        raise SystemExit("\n".join(errors))
    if changed:
        write_csv(rows)
    write_jsonl(rows)
    write_sqlite(rows)
    print(f"{len(rows)} records written")


if __name__ == "__main__":
    main()
