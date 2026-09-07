# MultiAgency.ai — Hermes Ops

> **Mission:** A durable, reproducible Hermes deployment for the org. If Hetzner goes down, we don't lose our setup, config, or history. This repo is the source of truth for how our Hermes backend is built, configured, and operated — so it can be rebuilt anywhere, anytime.

## Why this repo exists

We run a **single shared Hermes backend** on Hetzner (via Tailscale) that serves **multiple team members** through the Hermes desktop app. Each team member gets:

- 🔐 **Their own username/password** (per-user auth)
- 🧊 **A private, isolated profile** (own sessions, own memory, own skills)
- 🏢 **A shared company-wide context** (roadmap)

This repo captures everything needed to **recreate that setup from scratch**: the auth plugin, the server config (sanitized), onboarding docs, and the operational playbook. If the server dies, we don't start from zero.

## Current status

**Phase 1 - Working today:**
- [x] Hermes serve running on Hetzner behind Tailscale (:9090)
- [x] Per-user auth via the multi_user_basic plugin (see plugins/)
- [x] Private profiles: default (admin), megha, james, bizdev, onboarding
- [x] Profile-access enforcement (users can't read/switch into others' profiles)
- [x] Team onboarding docs (see docs/ONBOARDING.md)

**Phase 2 - Company-wide brain (next):**
- [ ] Shared knowledge base / memory accessible to all profiles
- [ ] Shared context about the org, clients, and pipeline
- [ ] Consistent model/config rollout across profiles

**Phase 3 - Durability and disaster recovery:**
- [ ] Automated config backup (this repo is the start)
- [ ] Scripted rebuild: one command, fresh Hetzner box, same setup
- [ ] Session/history backup strategy (SQLite dumps, object storage)
- [ ] Secret management (.env never in this repo, documented instead)

## Repo layout

```
.
├── README.md                        this file
├── config.sanitized.yaml            server config, secrets redacted
├── plugins/
│   └── dashboard_auth/
│       └── multi_user_basic/        per-user auth plugin
│           ├── plugin.yaml
│           └── __init__.py
├── docs/
│   ├── ONBOARDING.md                what a new team member needs
│   └── OPS.md                       how to add a user, restart, etc. (WIP)
└── .gitignore
