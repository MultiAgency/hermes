# Team Member Onboarding - Hermes Desktop Remote Gateway

## Prerequisites

| Step | What to do |
|------|------------|
| **1** | Install **Hermes Desktop** from hermes-agent.nousresearch.com/desktop |
| **2** | Install **Tailscale** from tailscale.com/download |
| **3** | Ask Jas/James to add you to the team's Tailscale network |
| **4** | Make sure Tailscale is **connected and running** (green checkmark in menu bar / system tray) |

## Connect to the remote backend

1. Open **Hermes Desktop**
2. You'll see a login screen - tap the **Settings** gear icon or the connection field
3. Fill in the fields:

| Field | Value |
|-------|-------|
| **Remote URL** | ws://<tailscale-ip>:9090 |
| **Username** | Ask Jas/James to create your profile and provide credentials |
| **Password** | Ask Jas/James to create your profile and provide credentials |
| **Profile** | The profile name Jas/James gave you (e.g. megha) |

4. Click **Connect** (or **Login**)

## How it works

- Each team member has their **own profile** on the shared server - private sessions, private memory, private skills, private conversation history.
- The profile acts as a **fully independent personal assistant just for you**, running on the team's shared backend.
- No one can see your sessions or memory - they are isolated per profile.
- **(Coming later)** - a shared company-wide knowledge base that all profiles can access.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **Connection refused** | Check Tailscale is running and you've been added to the network |
| **Invalid credentials** | Double-check the username and password Jas/James gave you |
| **Won't connect after server restart** | Just hit **Connect** again - it picks up right away |
