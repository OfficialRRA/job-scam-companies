# How to add or change a record

Thank you for your help. Each record names a business in public, so each record needs evidence.

## The rule for a new record

A new record needs a public source that names the entity. We accept these sources:

- A government action: FTC, DOJ, FBI, CFPB, USPIS, SEC, or a state attorney general.
- A court filing. Use `court_filing` as the `source_type`.
- A BBB Scam Tracker report.
- A news investigation or a security research report.
- A university career office warning.
- A fraud alert that an employer published about an operation that copies it.

We do not accept a social media post, a forum thread, or a review site as the only source.

## Way 1: open an issue

1. Go to the Issues tab and select "New issue".
2. Select the "Add a company" template.
3. Fill in the name, the domain, the category, and the source link.
4. A maintainer opens the source, checks it, and adds the record.

## Way 2: open a pull request

1. Fork the repository.
2. Add one row to `data/companies.csv` for each entity. Keep the column order.
3. Fill in `name`, `category`, `source_type`, `source_url`, and `source_date`. Leave the other fields blank unless a step below tells you to fill one in.
4. Fill in `domain` only when the source ties the domain to the entity.
5. If the source is not a government action or a court filing, the record needs a domain. Put the domain in `name` and in `domain`. Put the name that the operation used in `name_claimed`.
6. If the operation copies a real business, put the real business in `impersonates`. Do not put the real business in `name`.
7. Run `python3 scripts/build.py`. This command fills in `id`, `name_normalized`, `evidence_level`, `match_on`, `domain_source`, and `added_date`. It checks the data and writes the JSONL and SQLite files.
8. Run `python3 -m unittest discover -s tests`.
9. Open the pull request. Put the source link in the description.

## What a maintainer checks

- The source page opens and names the entity.
- The name is specific. A generic name can match an unrelated business, so we decline it.
- The domain belongs to the entity and not to a real business with a similar name.
- The category fits. See the category table in `README.md`.

## The other data files

This guide is for `data/companies.csv`. The other files have a different source:

- `data/lookalike_domains.csv`: the build script makes it. Do not edit it. Change `companies.csv`.
- `data/dol_debarred_employers.csv` and `data/staffing_wage_violations.csv`: copies of US Department of Labor data. Open an issue if a row differs from the source.
- `data/ats_hosts.csv`: open an issue with the host and a link that shows it is a hiring platform.

## Corrections and removals

Use the "Correction or removal" issue template, or send an email to alexs@reverserecruitingagency.com.

## Records with `source_type` = `rra_internal`

Only RRA adds these records. They show employers that RRA skips because of the business model. They make no claim of fraud.
