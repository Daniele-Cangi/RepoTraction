<div align="center">

# RepoTraction

### Evidence-based growth analytics for GitHub maintainers

Turn repository traffic, stars, clones, activity and community changes into signals you can actually use.

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![GitHub CLI](https://img.shields.io/badge/GitHub_CLI-required-181717?style=flat-square&logo=github)
[![GitHub REST API](https://img.shields.io/badge/GitHub_REST_API-2022--11--28-181717?style=flat-square&logo=github)](https://docs.github.com/en/rest)
[![CI](https://github.com/Daniele-Cangi/RepoTraction/actions/workflows/ci.yml/badge.svg)](https://github.com/Daniele-Cangi/RepoTraction/actions/workflows/ci.yml)
![Zero dependencies](https://img.shields.io/badge/dependencies-zero-b8f33d?style=flat-square&labelColor=11161d)
![Local first](https://img.shields.io/badge/data-local_only-b084ff?style=flat-square&labelColor=11161d)
![MIT License](https://img.shields.io/badge/license-MIT-b084ff?style=flat-square&labelColor=11161d)

</div>

![RepoTraction overview](docs/screenshots/overview.png)

> The screenshots use RepoTraction's built-in synthetic demo profile. They do
> not contain data from a real GitHub account.

RepoTraction is a local-first analytics application built on the
[GitHub REST API](https://docs.github.com/en/rest) for the account currently
active in [GitHub CLI](https://cli.github.com/). It runs on your computer,
reads GitHub through the authenticated <code>gh</code> session and stores
historical data in a local SQLite database.

There is no username to configure and no token to paste into the app.

## What you get

| Area | What it shows |
| --- | --- |
| **Overview** | Page views, clone activity, net star changes, community trends and important signals |
| **Repositories** | Portfolio ranking, page views, clone events, GitHub-native 14-day uniques, referrers and popular pages |
| **Insights** | Prioritized opportunities, Impact Lab, repository comparison, weekly digest and local alerts |
| **Stars** | Timestamped stargazer timeline for repositories you can access |
| **Network** | Followers, following, mutual relationships and changes over time |
| **Activity** | Recent public events and an experimental Achievement Lab |
| **Data** | Daily collection status, CSV exports and a JSON analytics export |

![RepoTraction Impact Lab](docs/screenshots/impact-lab.png)

## Designed for every GitHub account

RepoTraction automatically runs:

~~~powershell
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

~~~powershell
git clone https://github.com/Daniele-Cangi/RepoTraction.git
cd RepoTraction
~~~

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

### Run from source

Verify the active GitHub account:

~~~powershell
gh auth status
~~~

Start the dashboard:

~~~powershell
python app.py
~~~

On Windows you can also double-click <code>start.cmd</code> or run:

~~~powershell
.\start.ps1
~~~

RepoTraction opens at [http://127.0.0.1:8765](http://127.0.0.1:8765). Press
<code>Ctrl+C</code> in the terminal to stop it.

### Headless collection

Collect a complete snapshot without starting or keeping the dashboard open:

~~~powershell
python app.py --collect-only
~~~

This command is suitable for Windows Task Scheduler, cron and other local job
runners. It uses the same authenticated GitHub CLI account and the same SQLite
history as the dashboard, prints a JSON result and exits when collection ends.

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

The frontend is plain HTML, CSS and JavaScript. The backend is a single Python
application with no framework or package-manager dependency.

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
GET  /api/compare?repos=OWNER/REPO&repos=OWNER/OTHER
GET  /api/digest
GET  /api/traffic?repo=OWNER/REPO
POST /api/collect
GET  /api/export?dataset=summary
~~~

## Release status

The current development line is **RepoTraction 3.0.0**. It supersedes the
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
