# Job-scam company list

A public list of companies and domains that job seekers should check before they apply, interview, or share personal data. Reverse Recruiting Agency (RRA) keeps it. We use it to decide which employers we skip when we apply to jobs for our clients.

About 1,000 records in two groups. About 965 are entities that an outside source named in job-seeker fraud. Each of those records says who named the entity, when, and where you can read the source. The other 34 are employers that RRA skips because of the business model. Those have no outside source and carry no claim of fraud.

## Why this exists

Fake employers, fake recruiters, and pay-to-work schemes take money, time, and personal data from people who look for work. Career coaches, recruiters, and reverse recruiters each keep a private list of names to avoid. A shared list in the open helps everyone, and anyone can check it and correct it.

RRA applies to jobs for its clients every day, so we built a list to keep our clients away from these entities. This repository is the public copy.

## Who maintains it

Reverse Recruiting Agency, a job search service: https://reverserecruitingagency.com

Maintainer: Alex Shinkarovsky, founder.

- Email: alexs@reverserecruitingagency.com
- LinkedIn: https://www.linkedin.com/in/alexshinkarovsky

## Read this first

- A record means "a source named this entity". It does not prove fraud. Read the source before you act on a record.
- Scam operations often copy the name of a real business. For those records, the `domain` is the identifier, and `name` holds the domain. The name that the operation used is in `name_claimed`. It can belong to a real business, so do not match on it. The `match_on` field tells you which field to match.
- The real business that an operation copied is in `impersonates`. That business is a victim. Never block it.
- Records with `source_type` = `rra_internal` are a different kind of record. See "Two kinds of records".

## Two kinds of records

| Kind | `evidence_level` | What it means |
|---|---|---|
| Named by an outside source | `government_action`, `consumer_reports`, `news_or_watchdog`, `security_research`, `university_advisory`, `impersonated_employer_alert` | A regulator, court filing, consumer report, news investigation, security researcher, university career office, or the copied employer named the entity. `source_url` links to it. |
| RRA internal | `rra_internal` | RRA does not apply to these employers for clients, because of the business model: multi-level marketing, insurance agency recruiting, or commission-only direct sales. RRA makes no claim of fraud or wrongdoing about them. There is no outside source. |

## Files

| File | Use it for |
|---|---|
| `data/companies.csv` | The canonical file. One row per entity. GitHub shows it as a searchable table. |
| `data/companies.jsonl` | One JSON object per line. Good for LLM pipelines and scripts. |
| `data/companies.sqlite` | One table, `companies`, with indexes on `domain` and `name_normalized`. |
| `schema/company.schema.json` | JSON Schema for one record. |
| `llms.txt` | A short guide for LLMs and agents. |

## Fields

| Field | Meaning |
|---|---|
| `id` | Stable identifier. It does not change when other fields change. |
| `name` | For government sources and RRA internal records: the entity name as the source wrote it. For all other sources: the domain. |
| `aliases` | Other names for the same entity, separated by `; `. |
| `name_claimed` | The name that the operation used, when the record is identified by its domain. It can belong to a real business. Do not match on it. |
| `name_normalized` | `name` in lower case with every character that is not a letter or a digit removed. Use it for matching. |
| `domain` | Website domain, lower case, no `www.`. Blank when no source ties a domain to the entity. Records from sources other than a government action always have a domain. |
| `domain_source` | Where the domain came from: `cited_source` or `rra_internal`. |
| `linkedin_url` | LinkedIn company page. Blank unless the page's own website field matches `domain`. |
| `ats_url` | Job board or applicant tracking page. Blank unless it is tied to `domain`. |
| `category` | See "Categories". |
| `evidence_level` | See "Two kinds of records". |
| `match_on` | `domain` or `name`: the field to match against. |
| `impersonates` | The real business that the operation copied. Never block this business. |
| `source_type` | Who named the entity: `FTC`, `DOJ`, `FBI`, `CFPB`, `USPIS`, `state_AG`, `BBB`, `news_investigation`, `security_research`, `university_list`, `employer_fraud_alert`, `rra_internal`, and others. |
| `source_url` | The page that names the entity. |
| `source_date` | Date of the action, report, or article. `YYYY-MM-DD`, `YYYY-MM`, or `YYYY`, as exact as the source allows. |
| `other_sources` | More source URLs for the same entity, separated by `; `. |
| `added_date` | Date the record entered this list. |

## Categories

| `category` | Meaning |
|---|---|
| `fake_job_offer` | An operation that sends job offers for jobs that do not exist. |
| `fake_recruiter_impersonation` | A domain or entity that poses as a real employer or recruiter. |
| `reshipping_mule` | "Package handler" or "quality inspector" jobs that move stolen goods. |
| `fake_check` | A job that sends a check and asks for part of the money back. |
| `task_scam` | Paid "tasks" that require a deposit. |
| `work_from_home` | Work-from-home schemes named in enforcement actions. |
| `pay_for_placement` | Fees charged for a job, a job list, or a guaranteed placement. |
| `fake_staffing_agency` | An entity that poses as a staffing firm. |
| `visa_h1b_shell` | Shell employers named in visa fraud cases. |
| `business_opportunity` | Business-opportunity schemes named in enforcement actions. |
| `mlm` | Multi-level marketing (RRA internal). |
| `insurance_agency_recruiting` | Insurance agencies that recruit contractors through job posts (RRA internal). |
| `commission_only_direct_sales` | Door-to-door and in-store sales offices that pay commission only (RRA internal). |

## Examples

SQLite:

```sql
SELECT name, category, source_type, source_url, source_date
FROM companies
WHERE domain = 'example-careers.com'
   OR name_normalized = 'examplecompanyllc';
```

Python:

```python
import json
records = [json.loads(line) for line in open("data/companies.jsonl")]
by_domain = {r["domain"]: r for r in records if r["domain"]}
```

## Method

1. We collected entities from public sources: FTC, DOJ, FBI, CFPB, and state attorney general actions, BBB Scam Tracker reports, news investigations, security research, university career office lists, and fraud alerts that employers publish about operations that copy them.
2. We opened each source page and confirmed that it names the entity. Outside the `rra_internal` group, a record with no confirmed source is not in the list.
3. We removed entities with generic names, because a generic name can match an unrelated business.
4. A government action names a legal entity, so those records match on the name. Every other source can repeat a name that the operation copied from a real business. Those records must have a domain, and they match on the domain only. We left out consumer-report records with two or fewer reports.
5. We kept only the categories that affect job seekers.
6. We fill `domain`, `linkedin_url`, and `ats_url` only when evidence ties the value to the entity. A blank field is correct when there is no evidence.

## Limits

- The list is incomplete. An entity that is absent from the list is not safe for that reason.
- Some sources are old. An entity can close, change owners, or settle a case. Check `source_date`.
- `consumer_reports` records come from reports that consumers sent to the BBB. The BBB did not investigate each one.
- Scam domains change quickly. A domain in this list can be dead or can have a new owner.

## Add a company

Anyone can add to the list. There are two ways. `CONTRIBUTING.md` has the full steps.

1. Open an issue with the "Add a company" template. Give the name, the domain if you know it, and a public source that names the entity. This way needs no Git knowledge.
2. Open a pull request that adds a row to `data/companies.csv`. Fill in the name, the category, and the source fields. Run `python3 scripts/build.py`, which fills in the other fields, and `python3 -m unittest discover -s tests` before you send it.

Every new record needs a public source that we can open and read. We do not add a record from a private report alone. If you have a private report, send the details to the email address above and we look for a public source.

## Corrections and removals

If a record is wrong, or if it names your business, open an issue with the "Correction or removal" template or send an email to alexs@reverserecruitingagency.com. Give the record `id` and the evidence. We answer each request, and we correct or remove a record when the evidence supports it.

## Related work

- `davefano/job-scam`: an open-source browser extension that scores LinkedIn profiles, company pages, and job posts for suspicion. https://github.com/davefano/job-scam

## Licence

Data: CC BY 4.0 (`LICENSE-DATA`). Code: MIT (`LICENSE`).

## Disclaimer

This list is information, and it is not legal advice. Each record repeats what its source says. RRA does not state that an entity in this list broke a law. RRA makes no claim of wrongdoing about a record with `source_type` = `rra_internal`. Use the list at your own risk and read the source.
