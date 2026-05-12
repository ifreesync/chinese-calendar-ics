# Host on GitHub

## Steps

1. Create a repo and push this folder. Default branch is usually `main` (workflow also runs on `master`).
2. Enable Actions under Settings - Actions - General. Run Publish ICS calendars manually once from the Actions tab.

## iPhone subscription URL

Use a public repo if possible. Private repos need auth for raw files; iOS subscribed calendars usually cannot authenticate.

URL pattern:

https://raw.githubusercontent.com/OWNER/REPO/BRANCH/out/combined.ics

Replace OWNER, REPO, BRANCH (e.g. main).

Other feeds: out/china-official.ics, out/solar-terms.ics, out/traditional-lunar.ics, out/international.ics.

iPhone: Settings - Calendar - Accounts - Other - Add Subscribed Calendar.

## Automation

Workflow: .github/workflows/publish.yml runs generate_ics.py and commits out/*.ics.

## Yearly maintenance

Edit data/holidays.json from gov.cn notices; increase `--end` in the workflow if needed.

## Does JSON update automatically from the State Council?

**No.** Whatever is in `data/holidays.json` is the source of truth. The government publishes **HTML/documents**, not an official JSON API. Auto-scraping gov.cn is fragile (layout changes may produce wrong vacation dates).

What *is* automated:

- **publish.yml** — when you push updates to `data/holidays.json` (or related files), ICS files are rebuilt and committed.
- **holiday-reminder.yml** — each **November** (twice) opens a **GitHub Issue** reminding you to edit `data/holidays.json` for the next calendar year after the official notice appears.

Subscribed calendars pick up changes after a **few minutes** (`raw.githubusercontent.com` cache), not instantly.

## 中文：JSON 会随国务院通知自动变吗？

**不会。** 须在核对 [中国政府网](https://www.gov.cn) 正式通知后更新 `data/holidays.json`（或你自建可信数据源）。官方无开放 JSON；不建议用爬虫自动填法定假，以免版面改版导致日期错误。

已有自动化：**11 月定时提醒 Issue**（`holiday-reminder.yml`），以及你 push 后 **重建 `out/*.ics`**（`publish.yml`）。
