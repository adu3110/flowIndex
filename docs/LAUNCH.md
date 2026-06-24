# FlowIndex Launch Checklist

Goal: maximize GitHub Trending visibility and developer adoption — not a guaranteed "#1 repo of the day," but a structured launch.

## Before launch day

### Product polish
- [ ] `pip install flowindex` works from PyPI (not just editable install)
- [ ] README demo GIF: `init --here` → `scan` → `context`
- [ ] Cursor MCP config snippet copy-pasteable in README
- [ ] GitHub repo description + topics: `ai`, `agents`, `mcp`, `developer-tools`, `code-analysis`
- [ ] Pin repo on https://github.com/adu3110
- [ ] CI badge green on main

### Narrative
- [ ] One-line pitch: "Behavior-first repo indexing for AI coding agents"
- [ ] Show HN title drafted: "Show HN: FlowIndex – index how code behaves, not just files"
- [ ] 60-second demo video or terminal recording
- [ ] Blog post or site link from aditichatterji.com/research

### Distribution list
- [ ] Hacker News (Show HN)
- [ ] X/Twitter thread with demo GIF
- [ ] r/LocalLLaMA, r/programming
- [ ] Cursor / MCP Discord servers
- [ ] LinkedIn post (research-builder angle, not hype)

## Launch day (Tuesday–Thursday, 9–11am PT)

1. Publish PyPI if not already live
2. Post Show HN within 5 minutes of tweet
3. Link from personal site `/research#lab-notebooks`
4. Ask 5–10 peers to engage organically on HN (comments, not bot stars)
5. Monitor issues — respond within 1 hour

## Week 1 follow-through
- [ ] `v0.1.1` patch release (bug fixes from early users)
- [ ] Add ledger.py to context ranking (known gap)
- [ ] One example post: "FlowIndex on a FastAPI payments app"
- [ ] Thank-you comment on HN with roadmap

## What drives Trending

GitHub Trending ranks repos by **stars in a ~24h window** relative to project size. You need:

| Factor | Action |
|--------|--------|
| Spike traffic | HN front page or viral tweet |
| Clear value in 10s | GIF + comparison table in README |
| Easy install | PyPI one-liner |
| Shareability | MCP + Cursor angle |
| Credibility | Tests, CI, serious docs |

Realistic targets:
- **50–200 stars** — good launch with your network
- **500–2k stars** — HN front page or influencer RT
- **#1 global Trending** — rare; competes with major org releases

## Do not

- Buy stars or use star-for-star rings (GitHub detects abuse)
- Force-push over contributors
- Launch on Friday evening US time
- Over-promise "production-ready" — say "dev tool, alpha, local-first"
