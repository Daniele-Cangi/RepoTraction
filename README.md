<div align="center">

# RepoTraction

### Evidence-based analytics and capability discovery for GitHub maintainers

Understand your repository signals and discover problems your existing code could solve.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![GitHub CLI](https://img.shields.io/badge/GitHub_CLI-required-181717?style=flat-square&logo=github)
[![GitHub REST API](https://img.shields.io/badge/GitHub_REST_API-2022--11--28-181717?style=flat-square&logo=github)](https://docs.github.com/en/rest)
[![CI](https://github.com/Daniele-Cangi/RepoTraction/actions/workflows/ci.yml/badge.svg)](https://github.com/Daniele-Cangi/RepoTraction/actions/workflows/ci.yml)
![Zero dependencies](https://img.shields.io/badge/dependencies-zero-b8f33d?style=flat-square&labelColor=11161d)
![Local first](https://img.shields.io/badge/data-local_only-b084ff?style=flat-square&labelColor=11161d)
![MIT License](https://img.shields.io/badge/license-MIT-b084ff?style=flat-square&labelColor=11161d)

</div>

RepoTraction is a local-first analytics application built on the
[GitHub REST API](https://docs.github.com/en/rest) for the account currently
active in [GitHub CLI](https://cli.github.com/). It runs on your computer,
reads GitHub through the authenticated <code>gh</code> session and stores
historical data in a local SQLite database.

There is no username to configure and no token to paste into the app.

## What RepoTraction actually does

RepoTraction collects repository traffic, repository metadata and snapshot
changes, public activity, and follower/following relationships for the active
GitHub CLI account. It stores that history locally, then turns observed data
into comparisons, portfolio summaries and clearly labeled recommendations.

GitHub exposes repository views and clone data for only its latest rolling
14-day window. RepoTraction saves each observed daily snapshot in local SQLite,
so your traffic history can continue beyond GitHub's window. Collection builds
that history from the first successful run; it cannot restore days that had
already expired. Missing or unverified data stays unavailable instead of being
presented as zero.

It does **not** measure visits to a personal GitHub profile, identify people
who clone repositories, or prove that a repository change caused a traffic
change. Its scores and recommendations are local heuristics, not official
GitHub ratings.

### Dashboard areas

| Area | What it shows |
| --- | --- |
| **Overview** | Page views, clone activity, net star changes, community trends and important signals |
| **Repositories** | Portfolio ranking, page views, clone events, GitHub-native 14-day uniques, referrers and popular pages |
| **Insights** | Prioritized opportunities, Impact Lab, repository comparison, weekly digest and local alerts |
| **Missing Link** | Public requests matched to pinned code capabilities, hard constraints, adoption obstacles and inspectable technical bridges; independent of traffic/popularity |
| **Stars** | Timestamped stargazer timeline for repositories you can access |
| **Network** | Followers, following, mutual and one-sided relationships, and changes between saved snapshots; not profile visits |
| **Activity** | Recent public events and an experimental Achievement Lab |
| **Data** | Daily collection status, CSV exports and a JSON analytics export |

### Missing Link: problem → capability → technical bridge

Select a public repository, review its source-backed capabilities, then evaluate
a public GitHub issue or start bounded discovery. Missing Link separates the
desired outcome from the candidate solution, checks mandatory constraints, and
prepares a command/example/adapter proposal with pinned source evidence.
Internal mechanisms can be considered independently of the complete product.

This first working version supports Python AST analysis and a partial JS/TS
declaration scan; its actual source coverage is visible. No AI provider is required
for existing analytics. Without a provider, Missing Link collects sources and
retrieval candidates **but leaves compatibility as investigation**. For deeper
interpretation, configure an optional provider or export the source context to
your coding agent and import its grounded analysis.

Results are source-supported hypotheses, **not executed third-party integration
proofs**. Download JSON/ZIP handoffs containing requirements, revision, provenance,
bridge files, license information and explicit obstacles. No acquired/generated
code is executed on host Python. An explicitly approved optional WASI runner can
test small pure-Python examples without Docker; separate receipts never claim
target integration. No comments or third-party pull requests are published.

Discovery qualification checks bounded public target manifests and cited files
for prior package references. Reusable existing behavior is counted separately
from compatible scope constraints such as leaving an API unchanged. Neither a
missing reference nor a source citation proves novelty or successful integration.

See [usage, provider configuration and limits](docs/missing-link.md),
[three inspected real cases](docs/missing-link-cases.md), and
[reviewed example analyses](examples/missing-link/README.md). The
[real API verification](docs/missing-link-api-verification.md) is separate from
those manually reviewed analyses and fictional protocol tests. The
[second held-out cohort](docs/missing-link-second-heldout-discovery.md) found no
qualified external leads; [the resulting corrections](docs/missing-link-context-attribution.md)
describe the fixes and what still needs fresh testing.

The [1 October live Luna evaluation](docs/missing-link-live-discovery-2026-10-01.md)
retested the current contract on eight fresh repository-only inputs: 52 real model
calls, 24 selected issues and 34 comparisons, with no qualified external lead.
It records useful partial mechanisms and sound rejections, four quotation failures,
source-selection bias and a missed ANSI-cleanup contribution. Discovery quality
remains experimental; successful API calls and passing software tests are not
evidence of new actionable connections.

## Development plan

For planned architectural work and deferred language coverage, see the
[development plan](docs/development-plan.md).

## Alternatives and trade-offs

| Option | What it is good at | Choose it when |
| --- | --- | --- |
| [GitHub's built-in Traffic](https://docs.github.com/en/repositories/viewing-activity-and-data-for-your-repository/viewing-traffic-to-a-repository) | Native per-repository views, clones, referrers and popular paths for the latest 14 days. | You only need a quick, zero-setup look at recent traffic. |
| [RepoHistory](https://github.com/marketplace/repohistory) | A third-party hosted dashboard for longer-term repository traffic and star history. | You prefer a managed service focused on repository analytics. Review its separate privacy policy before connecting an account. |
| **RepoTraction** | Local portfolio history plus repository signals, relationship snapshots, activity and change-impact comparisons. | You want a local-first view across your GitHub account, and are comfortable running it with GitHub CLI. |

Long-term traffic collection is not unique to RepoTraction: other tools also
preserve it. Its distinction is combining that local history with account-wide
repository, community and impact views. [GitHub's API](https://docs.github.com/en/rest/metrics/traffic)
returns traffic in a rolling 14-day window; RepoTraction can only keep data it
collects while it is available.

## Screenshots

The images below use RepoTraction's built-in synthetic demo profile; they do
not contain data from a real GitHub account.

### Overview

Account signals, repository highlights and the recent activity pulse in one
place.

![RepoTraction overview](docs/screenshots/overview.png)

### Impact Lab

Compare observed traffic before and after releases, README work or repository
metadata changes. The comparison is observational, not proof of causality.

![RepoTraction Impact Lab](docs/screenshots/impact-lab.png)

### Network

Compare followers with the accounts you follow, find mutuals or accounts that
do not follow back, and review changes between saved snapshots. GitHub does
not expose profile visitors.

![RepoTraction Network](docs/screenshots/network.png)

### Missing Link

Start with public code, review its capabilities, and compare them with a public
request's requirements. Results distinguish existing functionality, proposed
bridge work and unknowns; optional isolated examples are not target integration.
The synthetic demo explains the workflow but deliberately does not invent
successful matches or proofs. See the [real API verification](docs/missing-link-api-verification.md)
for the separately recorded investigation and execution evidence.

![RepoTraction Missing Link synthetic demo](docs/screenshots/missing-link.png)

## Designed for every GitHub account

RepoTraction automatically runs:

~~~sh
gh api user
~~~

to identify the active account. Each account gets an isolated database:

~~~text
data/repotraction-<github-login>.sqlite3
~~~

If you use more than one GitHub account, switch the active <code>gh</code>
account and restart RepoTraction. Existing histories remain separate. Existing
`github-pulse-<login>.sqlite3` histories are migrated automatically on first run.

## Requirements

- Python 3.10 or newer;
- [GitHub CLI](https://cli.github.com/) installed and authenticated;
- write access to repositories whose traffic metrics you want to inspect.

No Python packages need to be installed. The application uses only the standard
library, GitHub CLI and SQLite.

## Quick start

Clone the repository and enter the project directory:

~~~sh
git clone https://github.com/Daniele-Cangi/RepoTraction.git
cd RepoTraction
~~~

Verify that GitHub CLI is installed and authenticated:

~~~sh
gh auth status
~~~

### Run from source

The source app uses Python's standard library and works on Windows, macOS and
Linux. Use the Python launcher available on your system:

~~~sh
# macOS / Linux
python3 app.py
~~~

~~~powershell
# Windows
python app.py
~~~

The local dashboard opens at [http://127.0.0.1:8765](http://127.0.0.1:8765).
Press <code>Ctrl+C</code> in the terminal to stop it. On Windows, you can also
double-click <code>start.cmd</code> or run <code>start.ps1</code>.

### Windows installer

Install RepoTraction for the current Windows user:

~~~powershell
.\install.ps1
~~~

You can also double-click <code>install.cmd</code>.

The installer creates a Start menu shortcut and copies the application to
<code>%LOCALAPPDATA%\RepoTraction</code>. Re-running it updates the application
without overwriting the local SQLite history.

To remove the application while keeping your history:

~~~powershell
& "$env:LOCALAPPDATA\RepoTraction\uninstall.ps1"
~~~

Pass <code>-RemoveData</code> only if you also want to delete the collected
history.

## Commands, exports and notifications

### Command-line options

| Option | What it does |
| --- | --- |
| `--help` | Show all command-line options. |
| `--host HOST` | Bind to a loopback address only; defaults to `127.0.0.1`. Network/LAN binding is rejected. |
| `--port PORT` | Choose the local server port; defaults to `8765`. |
| `--no-open` | Start the server without opening a browser tab. |
| `--collect-only` | Collect one snapshot and exit without starting the dashboard. Exit status is `0` for complete, `2` for partial, and `1` for failed collection. |

Example: use a different port and keep the browser closed.

~~~powershell
python app.py --port 8766 --no-open
~~~

On macOS or Linux, use `python3` instead of `python`.

To run a one-off collection for Task Scheduler, cron or another local scheduler:

~~~powershell
python app.py --collect-only
~~~

Use `python app.py --help` (or `python3 app.py --help`) for the current option
summary.

### Export datasets

Download exports from **Data & privacy**; the weekly Markdown digest is in
**Insights → Digest & alerts**. The available `dataset` values are:

| Dataset | Format | Contents |
| --- | --- | --- |
| `traffic` | CSV | Daily per-repository views and clones, native unique counts, availability/provenance status and collection time. |
| `movements` | CSV | Follower/following relationship changes with event time and profile URL. |
| `summary` | JSON | Account signals, repository events, relationship history and collected traffic. This is an analytics export, not a restorable SQLite backup. |
| `digest` | Markdown | The weekly portfolio digest. |

For example: `/api/export?dataset=traffic` downloads the traffic CSV.

### Desktop notifications

Open **Insights → Digest & alerts**, select **Enable desktop alerts**, and grant
the browser's notification permission. Alerts are off by default and are kept
in that browser; while the dashboard is open, it can notify you about detected
traffic spikes, net star growth and new followers.

### Synthetic demo

To explore or capture the interface without displaying the authenticated
account, open:

~~~text
http://127.0.0.1:8765/?demo=1#overview
~~~

Demo mode uses a deterministic fictional profile, repositories and metrics. It
does not call the account data endpoints, and collection and exports are
disabled in the interface.

## How collection works

GitHub exposes repository views and clones for a rolling 14-day window. RepoTraction stores both the native 14-day totals and every available daily value in
SQLite, building an event history that can extend beyond GitHub's window.

Rolling 7-day metrics end on the latest UTC day actually returned by GitHub,
not on the computer's current date. Views and clones track availability
separately: an unavailable endpoint or legacy value is shown as unavailable,
not as zero. Growth and spike comparisons are enabled only when the relevant
metric has all seven daily observations in both adjacent windows. Every label
includes the effective data-through date.

Repositories are tracked by GitHub's immutable numeric repository ID. If a
repository is renamed, its old records are merged into the current name instead
of appearing as a second project. If a deleted repository name is later reused,
the former repository's history is kept separately under an archive label.
Deleted or no-longer-owned repositories remain available in exports but are
excluded from current totals and rankings. Before the first registry snapshot,
historical data remains visible; an initialized but empty registry correctly
means there are no current repositories.
The special profile README repository (`owner/owner`) remains available in the
repository explorer but is excluded from activity totals, Activity Score
rankings, comparisons, digests and recommendations. Its current stars still
count toward the account's overall star total, while its expected lack of star
growth is never presented as a project problem.

The dashboard keeps the meanings separate:

- **Page views** and **clone events** are additive and can be compared across
  repositories.
- **Unique visitors · GitHub 14d** and **unique cloners · GitHub 14d** are the
  native per-repository aggregates returned by GitHub.
- Sums of daily unique values are stored as **visitor-days** and
  **cloner-days** for historical analysis; they are never presented as unique
  people.
- **Cloning breadth** compares GitHub's native unique cloners with full clone
  events from the same 14-day snapshot. **Repeat factor** reports clone events
  per unique cloner. Neither metric identifies people, bots or intent.
- **Net stars** and **net forks** are differences between repository snapshots,
  not counts of newly acquired stars or forks. Their actual observation window
  is shown next to the value. A single snapshot is reported as **no comparison
  yet**, never as stable activity.
- License metadata distinguishes **recognized**, **present but unrecognized**
  (`NOASSERTION`) and **missing**. A custom or proprietary license is not treated
  as absent.

If one GitHub traffic endpoint fails, RepoTraction preserves the last valid
values for that channel instead of replacing them with zero. Existing daily
rows from older versions are marked as availability-unknown until recollected;
the migration does not assume that historical zeroes were measured zeroes.

While the server is running, a complete collection starts when the previous one
is more than 20 hours old, or sooner if the current traffic window still has
availability-unknown values after a database migration. You can also start it
manually with **Collect now** or run `python app.py --collect-only` from a local
scheduler. Non-archived repositories are processed sequentially to keep API
usage predictable.

Follower and following lists do not include timestamps. RepoTraction therefore
creates a baseline on first run and records additions or removals from subsequent
snapshots.

The **Opportunity Center** combines page views, clone events, snapshot changes
and repository readiness checks. Recommendations are heuristics: they highlight
likely next actions without claiming a visitor-to-star or clone conversion.
Each recommendation includes a confidence level. Clone-based recommendations
are deliberately low-confidence because GitHub cannot distinguish people from
bots, CI jobs or other automation.

The **Impact Ledger** records releases, README commits and observed changes to
repository descriptions, topics, homepages and licenses. **Impact Lab** compares
up to seven available days before and after each event, then subtracts the median
movement across other repositories in the same portfolio. This Portfolio
Baseline helps separate repository-specific movement from account-wide noise,
but it remains observational evidence rather than proof of causality.

The **Activity Score** ranks repositories with this capped local heuristic:

~~~text
min(100,
  7 × ln(1 + page views)
  + 9 × ln(1 + clone events)
  + 10 × positive net stars
  + 12 × positive net forks
)
~~~

It does not use summed unique counts or inferred conversion rates and it is not
an official GitHub quality or health score. **Project Readiness** is a separate,
local checklist based on description, topics, license presence, homepage and
recent activity. Activity Score is withheld where daily views or clone data is
unavailable rather than treating an unknown channel as zero.

The **Weekly Digest** can be copied or downloaded as Markdown. Desktop alerts
use the browser's local notification permission and are disabled by default.

## Privacy and security

- The HTTP server binds only to <code>localhost</code> or a loopback IP address;
  requests with a non-local Host or cross-origin Origin are rejected.
- Tokens never enter the browser or the SQLite database.
- RepoTraction does not store credentials; GitHub CLI manages authentication
  through its configured credential store or environment.
- The active GitHub CLI account is checked during requests. If it changes while
  RepoTraction is open, data requests stop until the account is switched back or
  the server is restarted, keeping account histories separate.
- Collected databases are ignored by Git and stay on the local machine.
- CSV, JSON analytics and Markdown exports are generated only when requested.
  The JSON export is not a restorable database backup; keep a separate copy of
  the local SQLite file if you need a full backup.

## GitHub API limits

GitHub does not expose:

- unique visitors to a personal profile;
- the identity of people who clone a repository;
- a direct visitor-to-clone conversion path;
- an official API for every achievement already displayed on a profile.

GitHub's native unique totals apply to one repository and one rolling 14-day
window. They cannot be added across repositories or days to produce
account-level unique reach. Page-view and clone populations are never divided
to claim an individual conversion. Achievement cards are eligibility estimates
and not an authoritative badge record.

RepoTraction caps concurrent GitHub API requests at four. If GitHub explicitly
reports a rate limit, the current collection stops and records the error rather
than continuing to send requests; failed or partial collections are retried by
the local scheduler on its next hourly check.

REST requests pin API version `2022-11-28`; update the pinned version only after
reviewing GitHub's breaking-change notes and running the full test suite.

## Architecture

~~~text
Browser
   │
   ▼
Python local server ─── SQLite history
   │
   ▼
GitHub CLI / credential store
   │
   ▼
GitHub REST API
~~~

The frontend is plain HTML, CSS and JavaScript. The Python server has no framework
or package-manager dependency. Traffic analytics remain in `app.py`; Missing Link
has separate acquisition/analysis, provider, persistence/job and packaging modules
in `missing_link/`. Its optional AI service does not become an analytics dependency.

## Development

Run the test suite:

~~~powershell
python -m unittest discover -s tests -v
~~~

Useful local endpoints:

~~~text
GET  /api/health
GET  /api/dashboard
GET  /api/signals
GET  /api/activity
GET  /api/opportunities
GET  /api/impact
GET  /api/missing-link
POST /api/missing-link/jobs
GET  /api/missing-link/context?job_id=ID
POST /api/missing-link/analysis
GET  /api/compare?repos=OWNER/REPO&repos=OWNER/OTHER
GET  /api/digest
GET  /api/traffic?repo=OWNER/REPO
POST /api/collect
GET  /api/export?dataset=summary
~~~

## Release status

The current development line is **RepoTraction 3.1.0** (Missing Link). It extends
3.0's analytics without claiming universal discovery or executed proof support.
It supersedes the
[v2.0.0 baseline](https://github.com/Daniele-Cangi/RepoTraction/releases/tag/v2.0.0)
with the Insights and Impact Lab expansion plus stricter traffic-availability,
collection-status, account-isolation, repository-identity and local-server
safety handling.

## Support

For RepoTraction support, bug reports that should not be public, or other
project questions, contact **daniele.tl.project@gmail.com**. Public bugs and
feature requests can also be opened through GitHub Issues.

See [SUPPORT.md](SUPPORT.md) for the support policy.

## License

RepoTraction is open-source software released under the
[MIT License](LICENSE). You can use, modify and distribute it, including in
commercial projects, while retaining the copyright and license notice.

---

<div align="center">
Built to make GitHub activity readable, not merely countable.
</div>
