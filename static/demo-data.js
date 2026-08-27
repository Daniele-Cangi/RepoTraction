const generatedAt = "2026-08-23T10:30:00+02:00";
const account = "octoforge-demo";
const accountUrl = "https://example.com/octoforge-demo";
const avatarUrl = "/demo-avatar.svg";
const snapshotPeriod = {
  from: "2026-08-16T10:30:00+02:00",
  to: generatedAt,
  days_observed: 7,
  is_full_window: true,
  has_baseline: true,
  label: "last 7 days",
};
const trafficPeriod = {
  from: "2026-08-17",
  to: "2026-08-23",
  days_available: 7,
  is_complete: true,
  label: "7d ending Aug 23 UTC",
};

function repositorySignal(
  name,
  language,
  views,
  previousViews,
  clones,
  stars,
  netStars,
  score,
  uniqueVisitors,
  uniqueCloners,
) {
  return {
    repo: account + "/" + name,
    name,
    language,
    private: false,
    archived: false,
    views_7d: views,
    previous_views: previousViews,
    visitor_days_7d: Math.round(views * 0.72),
    clones_7d: clones,
    previous_clones: Math.max(0, clones - 7),
    cloner_days_7d: Math.round(clones * 0.78),
    views_14d: views + previousViews,
    clones_14d: clones + Math.max(0, clones - 7),
    unique_visitors_14d: uniqueVisitors,
    unique_cloners_14d: uniqueCloners,
    native_views_14d: views + previousViews,
    native_clones_14d: clones + Math.max(0, clones - 7),
    stars,
    net_stars: netStars,
    forks: Math.round(stars * 0.18),
    net_forks: Math.max(0, Math.round(netStars / 3)),
    watchers: Math.max(2, Math.round(stars * 0.08)),
    open_issues: Math.max(1, Math.round(stars * 0.025)),
    clone_view_ratio: Math.round((clones / views) * 1000) / 10,
    snapshot_period: snapshotPeriod,
    traffic_period: trafficPeriod,
    traffic_comparison_ready: true,
    traffic_collected_at: generatedAt,
    signal_score: score,
  };
}

const repositorySignals = [
  repositorySignal("nebula-notes", "TypeScript", 318, 248, 46, 128, 6, 96, 241, 38),
  repositorySignal("atlas-api", "Python", 274, 205, 38, 212, 4, 92, 198, 31),
  repositorySignal("orbit-ui", "TypeScript", 221, 190, 29, 164, 3, 88, 172, 24),
  repositorySignal("signal-lab", "Rust", 187, 121, 31, 96, 2, 85, 139, 25),
  repositorySignal("streamforge", "Go", 146, 119, 22, 73, 2, 81, 108, 18),
  repositorySignal("tiny-search", "JavaScript", 92, 84, 11, 41, 1, 70, 69, 9),
];

const repositories = repositorySignals.map((row) => ({
  full_name: row.repo,
  name: row.name,
  private: row.private,
  archived: row.archived,
  fork: false,
  stars: row.stars,
  forks: row.forks,
  watchers: row.watchers,
  open_issues: row.open_issues,
  language: row.language,
  html_url: "https://example.com/" + row.repo,
  description: "Synthetic demo repository for GitHub Pulse.",
  homepage: "https://example.com/" + row.name,
  topics: ["demo", "open-source", "developer-tools"],
  license: "MIT",
  pushed_at: "2026-08-22T17:10:00+02:00",
}));

function demoUser(login) {
  return {
    login,
    avatar_url: avatarUrl,
    html_url: "https://example.com/users/" + login,
  };
}

const mutuals = [
  demoUser("pixel-craft"),
  demoUser("api-gardener"),
  demoUser("cloud-sketch"),
  demoUser("syntax-studio"),
];
const followers = mutuals.concat([
  demoUser("studio-spark"),
  demoUser("northstar-dev"),
  demoUser("open-builders"),
]);
const following = mutuals.concat([
  demoUser("data-orbit"),
  demoUser("ship-small"),
]);

const collection = {
  running: false,
  started_at: "2026-08-23T10:27:00+02:00",
  completed_at: generatedAt,
  current_repo: null,
  repos_total: repositories.length,
  repos_completed: repositories.length,
  errors: [],
};

const totals = repositorySignals.reduce(
  (result, row) => {
    result.views_7d += row.views_7d;
    result.clones_7d += row.clones_7d;
    result.stars += row.stars;
    result.net_stars += row.net_stars;
    result.forks += row.forks;
    result.net_forks += row.net_forks;
    return result;
  },
  {
    views_7d: 0,
    clones_7d: 0,
    stars: 0,
    net_stars: 0,
    forks: 0,
    net_forks: 0,
  },
);

const notifications = [
  {
    type: "traffic_spike",
    tone: "positive",
    title: "Traffic spike on nebula-notes",
    detail: "318 page views · +28.2%",
    occurred_at: generatedAt,
    url: "https://example.com/octoforge-demo/nebula-notes",
  },
  {
    type: "net_star_growth",
    tone: "positive",
    title: "Net star growth on atlas-api",
    detail: "+4 · last 7 days",
    occurred_at: "2026-08-23T09:45:00+02:00",
    url: "https://example.com/octoforge-demo/atlas-api",
  },
  {
    type: "new_follower",
    tone: "positive",
    title: "New follower",
    detail: "@studio-spark",
    occurred_at: "2026-08-22T18:15:00+02:00",
    url: "https://example.com/users/studio-spark",
  },
  {
    type: "traffic_spike",
    tone: "positive",
    title: "Traffic spike on signal-lab",
    detail: "187 page views · +54.5%",
    occurred_at: "2026-08-22T16:20:00+02:00",
    url: "https://example.com/octoforge-demo/signal-lab",
  },
];

const dashboard = {
  generated_at: generatedAt,
  collected_at: generatedAt,
  profile: {
    login: account,
    name: "OctoForge Labs",
    bio: "Synthetic open-source studio",
    avatar_url: avatarUrl,
    html_url: accountUrl,
  },
  repositories,
  counts: {
    followers: 482,
    following: 138,
    mutual: 87,
    not_following_back: 51,
    followers_not_followed: 395,
  },
  relationships: {
    mutual: mutuals,
    not_following_back: [demoUser("data-orbit"), demoUser("ship-small")],
    followers_not_followed: [
      demoUser("studio-spark"),
      demoUser("northstar-dev"),
      demoUser("open-builders"),
    ],
    followers,
    following,
    all: followers.concat(following.slice(4)),
  },
  relationship_movements: [
    {
      event_type: "new_follower",
      login: "studio-spark",
      avatar_url: avatarUrl,
      html_url: "https://example.com/users/studio-spark",
      collected_at: "2026-08-22T18:15:00+02:00",
    },
    {
      event_type: "started_following",
      login: "data-orbit",
      avatar_url: avatarUrl,
      html_url: "https://example.com/users/data-orbit",
      collected_at: "2026-08-21T11:10:00+02:00",
    },
  ],
};

const signals = {
  generated_at: generatedAt,
  cards: [
    {
      key: "reach",
      label: "Page views",
      value: totals.views_7d,
      unit: `repository views · ${trafficPeriod.label}`,
      delta: 24.1,
      delta_available: true,
    },
    {
      key: "clone_activity",
      label: "Clone activity",
      value: totals.clones_7d,
      unit: `full clone events · ${trafficPeriod.label}`,
      delta: 14.8,
      delta_available: true,
    },
    {
      key: "stars",
      label: "Stars",
      value: totals.stars,
      unit: "total · net change",
      delta_absolute: totals.net_stars,
    },
    {
      key: "community",
      label: "Community",
      value: 482,
      unit: "followers · last 7 days",
      delta_absolute: 14,
    },
  ],
  totals,
  traffic_period: trafficPeriod,
  traffic_comparison_ready: true,
  repository_ranking: repositorySignals,
  notifications,
  important_signals: notifications.length,
  tracked_repositories: repositorySignals.length,
  relationship_counts: dashboard.counts,
  relationship_delta: {
    followers: 14,
    following: 3,
    mutual: 5,
    not_following_back: -2,
    followers_not_followed: 9,
  },
  relationship_period: snapshotPeriod,
  collection,
};

const opportunities = [
  {
    kind: "discoverability",
    priority: "high",
    repo: account + "/nebula-notes",
    title: "Strengthen nebula-notes' first impression",
    detail: "318 page views make this the portfolio's busiest landing page.",
    action: "Put the live demo and three-step quick start above the fold.",
    metric: "318 views · +28.2%",
    score: 98,
    url: "https://example.com/octoforge-demo/nebula-notes",
  },
  {
    kind: "developer_experience",
    priority: "medium",
    repo: account + "/atlas-api",
    title: "Shorten atlas-api's setup path",
    detail: "38 full clone events were recorded this week.",
    action: "Add a copy-ready local setup and expected response example.",
    metric: "38 clones · 13.9% clone/view",
    score: 84,
    url: "https://example.com/octoforge-demo/atlas-api",
  },
  {
    kind: "momentum",
    priority: "medium",
    repo: account + "/signal-lab",
    title: "Capture signal-lab's momentum",
    detail: "+54.5% page-view growth creates a useful release window.",
    action: "Publish the benchmark update while attention is elevated.",
    metric: "187 views · +54.5%",
    score: 79,
    url: "https://example.com/octoforge-demo/signal-lab",
  },
  {
    kind: "foundation",
    priority: "low",
    repo: account + "/tiny-search",
    title: "Polish tiny-search's metadata",
    detail: "The repository would benefit from one more discovery topic.",
    action: "Add a search-related topic and a compact social preview.",
    metric: "Health 82/100",
    score: 64,
    url: "https://example.com/octoforge-demo/tiny-search",
  },
];

const health = repositorySignals.map((row, index) => ({
  repo: row.repo,
  name: row.name,
  score: [96, 94, 91, 88, 86, 82][index],
  gaps: index === 5 ? ["topics"] : [],
  url: "https://example.com/" + row.repo,
}));

const opportunityCenter = {
  generated_at: generatedAt,
  summary: {
    total: opportunities.length,
    high: 1,
    medium: 2,
    health_average: 90,
    repositories_analyzed: repositorySignals.length,
  },
  opportunities,
  health,
  repositories: repositorySignals.map((row) => ({
    repo: row.repo,
    name: row.name,
  })),
};

const digest = {
  generated_at: generatedAt,
  period: {
    from: "2026-08-17",
    to: "2026-08-23",
    label: trafficPeriod.label,
  },
  totals,
  relationship_delta: signals.relationship_delta,
  relationship_period: snapshotPeriod,
  top_repositories: repositorySignals.slice(0, 5),
  opportunities: opportunities.slice(0, 3),
  alerts: notifications.slice(0, 2),
  markdown: "# GitHub Pulse Weekly Digest\n\nSynthetic demo data.",
};

const trafficHistory = [
  [10, 58, 34], [11, 63, 37], [12, 54, 31], [13, 71, 42],
  [14, 69, 40], [15, 82, 49], [16, 77, 45], [17, 91, 53],
  [18, 88, 51], [19, 96, 57], [20, 104, 61], [21, 98, 59],
  [22, 112, 66], [23, 118, 70],
].map(([day, views, uniqueViews]) => ({
  day: "2026-08-" + String(day).padStart(2, "0"),
  views,
  unique_views: uniqueViews,
  clones: Math.round(views * 0.14),
  unique_clones: Math.round(uniqueViews * 0.12),
}));

const traffic = {
  repo: account + "/nebula-notes",
  collected_at: generatedAt,
  views: { count: 1201, uniques: 241, available: true },
  clones: { count: 163, uniques: 38, available: true },
  history: trafficHistory,
  referrers: [
    { referrer: "github.com", count: 382, uniques: 164 },
    { referrer: "google.com", count: 241, uniques: 131 },
    { referrer: "dev.to", count: 96, uniques: 72 },
  ],
  paths: [
    { path: "/", title: "nebula-notes", count: 618, uniques: 211 },
    { path: "/blob/main/README.md", title: "Quick start", count: 207, uniques: 128 },
    { path: "/releases", title: "Releases", count: 83, uniques: 61 },
  ],
  partial_errors: [],
};

const stars = {
  repo: account + "/nebula-notes",
  count: 128,
  stars: [
    {
      login: "pixel-craft",
      avatar_url: avatarUrl,
      html_url: "https://example.com/users/pixel-craft",
      starred_at: "2026-08-23T08:20:00+02:00",
    },
    {
      login: "studio-spark",
      avatar_url: avatarUrl,
      html_url: "https://example.com/users/studio-spark",
      starred_at: "2026-08-22T16:45:00+02:00",
    },
  ],
};

const activity = {
  generated_at: generatedAt,
  counts: {
    PushEvent: 18,
    PullRequestEvent: 6,
    IssuesEvent: 4,
    ReleaseEvent: 2,
  },
  events: [
    {
      type: "ReleaseEvent",
      title: "Released nebula-notes v1.8",
      detail: "A faster search index and refreshed documentation.",
      created_at: "2026-08-22T15:20:00+02:00",
      url: "https://example.com/octoforge-demo/nebula-notes/releases",
    },
    {
      type: "PushEvent",
      title: "Updated atlas-api",
      detail: "Improved request tracing and examples.",
      created_at: "2026-08-21T12:05:00+02:00",
      url: "https://example.com/octoforge-demo/atlas-api",
    },
  ],
  achievements: [
    {
      name: "Pull Shark",
      confidence: "high",
      progress: 7,
      target: 8,
      detail: "One more merged pull request estimate to the next threshold.",
      status: "candidate",
    },
    {
      name: "Starstruck",
      confidence: "medium",
      progress: 12,
      target: 16,
      detail: "Repository stars are trending toward the estimated threshold.",
      status: "tracking",
    },
  ],
  achievement_note: "Achievement progress is an estimate based on public activity.",
};

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

export function getDemoResponse(path) {
  const url = new URL(path, "http://github-pulse.demo");
  if (url.pathname === "/api/dashboard") return clone(dashboard);
  if (url.pathname === "/api/signals") return clone(signals);
  if (url.pathname === "/api/opportunities") return clone(opportunityCenter);
  if (url.pathname === "/api/digest") return clone(digest);
  if (url.pathname === "/api/activity") return clone(activity);
  if (url.pathname === "/api/collection") return clone(collection);
  if (url.pathname === "/api/traffic") return clone(traffic);
  if (url.pathname === "/api/stars") return clone(stars);
  if (url.pathname === "/api/collect") {
    return { started: false, collection: clone(collection) };
  }
  if (url.pathname === "/api/compare") {
    const requested = url.searchParams.getAll("repos");
    const selected = requested.length ? requested : repositorySignals.slice(0, 2).map((row) => row.repo);
    return {
      generated_at: generatedAt,
      repositories: selected
        .map((repo) => repositorySignals.find((row) => row.repo === repo))
        .filter(Boolean)
        .map((row) => ({
          ...row,
          view_change: Math.round(((row.views_7d - row.previous_views) / row.previous_views) * 1000) / 10,
          history: trafficHistory,
        })),
    };
  }
  throw new Error("Demo data is unavailable for " + url.pathname + ".");
}
