"""Multi-user basic auth provider — per-user credentials for team members.

Each entry in ``dashboard.multi_user_basic.users`` registers an independent
:class:`BasicAuthProvider <plugins.dashboard_auth.basic.BasicAuthProvider>`
with the username as the provider name, so the login page shows one selectable
entry per team member.

Configuration (config.yaml) — env vars are NOT supported for this provider::

    dashboard:
      multi_user_basic:
        # Optional shared token-signing key, base64 or hex, >= 32 bytes.
        # If omitted, a random per-process key is generated (sessions do not
        # survive restart / span multiple workers).
        secret: "..."

        # Optional session TTL (default 12h).
        session_ttl_seconds: 43200

        # REQUIRED — at least one user.
        users:
          jas:
            # Provide EITHER a precomputed scrypt hash (preferred):
            password_hash: "scrypt$..."
            # ... OR a plaintext password (hashed in-memory at load):
            # password: "mypassword"

            display_name: "Jas"           # optional, shown on login button

          james:
            password_hash: "scrypt$..."
            display_name: "James"

          alex:
            password_hash: "scrypt$..."
            display_name: "Alex"
"""

from __future__ import annotations

import base64
import logging
from typing import Any, Optional

from hermes_cli.dashboard_auth import register_provider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_config_multi_user_section() -> dict:
    """Return ``dashboard.multi_user_basic`` from config.yaml, or ``{}``."""
    try:
        from hermes_cli.config import cfg_get, load_config
        cfg = load_config()
    except Exception as exc:
        logger.debug(
            "multi-user-basic: load_config() raised %s; config unavailable", exc
        )
        return {}
    section = cfg_get(cfg, "dashboard", "multi_user_basic", default=None)
    return section if isinstance(section, dict) else {}


def _resolve_secret(cfg_section: dict) -> bytes:
    """Resolve the token-signing secret, or generate a random one."""
    raw = str(cfg_section.get("secret", "") or "").strip()
    if not raw:
        import secrets
        logger.info(
            "multi-user-basic: no 'secret' configured; generating a "
            "random per-process signing key. Sessions will not survive a "
            "restart or span multiple workers. Set dashboard.multi_user_basic."
            "secret for stable sessions."
        )
        return secrets.token_bytes(32)
    for decoder in (base64.b64decode, bytes.fromhex):
        try:
            decoded = decoder(raw)
            if len(decoded) >= 16:
                return decoded
        except (ValueError, TypeError):
            pass
    return raw.encode("utf-8")


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

LAST_SKIP_REASON: str = ""

_DEFAULT_TTL = 12 * 60 * 60  # 12h


def register(ctx) -> None:
    """Plugin entry — registers one BasicAuthProvider per configured user."""
    global LAST_SKIP_REASON
    LAST_SKIP_REASON = ""

    from plugins.dashboard_auth.basic import BasicAuthProvider

    section = _load_config_multi_user_section()
    users_raw = section.get("users")
    if not users_raw or not isinstance(users_raw, dict):
        LAST_SKIP_REASON = (
            "dashboard.multi_user_basic.users is not configured (missing, "
            "empty, or not a dict). Add a users section to config.yaml under "
            "dashboard.multi_user_basic to enable per-user credentials."
        )
        logger.debug("multi-user-basic: %s", LAST_SKIP_REASON)
        return

    secret = _resolve_secret(section)
    ttl = _DEFAULT_TTL
    if section.get("session_ttl_seconds"):
        try:
            ttl = max(60, int(section["session_ttl_seconds"]))
        except (ValueError, TypeError):
            pass

    registered = 0
    errors: list[str] = []

    for username, user_cfg in users_raw.items():
        if not isinstance(user_cfg, dict):
            errors.append(f"user {username!r}: config is not a dict, skipping")
            continue
        if not username or not username.strip():
            errors.append("empty username key, skipping")
            continue
        username = username.strip()

        # Resolve password_hash (config-only, no env override — env is
        # impractical for multiple users).
        password_hash = str(user_cfg.get("password_hash", "") or "").strip()
        plaintext = str(user_cfg.get("password", "") or "").strip()

        if not password_hash and not plaintext:
            errors.append(
                f"user {username!r}: neither password_hash nor password set, skipping"
            )
            continue

        # If a plaintext password is supplied, hash it in-memory.
        if not password_hash:
            password_hash = _hash_password(plaintext)
            logger.info(
                "multi-user-basic: hashed plaintext password for user %r "
                "in-memory. Precompute password_hash for production use.",
                username,
            )

        display_name = str(user_cfg.get("display_name", "").strip() or username)

        try:
            provider = BasicAuthProvider(
                username=username,
                password_hash=password_hash,
                secret=secret,
                ttl_seconds=ttl,
            )
            # Give each provider a unique name so the login page can
            # distinguish them.
            provider.name = username
            provider.display_name = display_name
        except ValueError as exc:
            errors.append(f"user {username!r}: provider construction failed: {exc}")
            continue

        register_provider(provider)
        registered += 1
        logger.info(
            "multi-user-basic: registered provider %r (display_name=%r)",
            username,
            display_name,
        )

    if registered:
        logger.info(
            "multi-user-basic: registered %d user(s) successfully", registered
        )
    if errors:
        joined = "; ".join(errors)
        LAST_SKIP_REASON = f"registered {registered} user(s) with {len(errors)} error(s): {joined}"
        logger.warning("multi-user-basic: %s", joined)
    elif not registered:
        LAST_SKIP_REASON = (
            "No users were registered — check dashboard.multi_user_basic.users "
            "in config.yaml."
        )
        logger.debug("multi-user-basic: %s", LAST_SKIP_REASON)


# ---------------------------------------------------------------------------
# Inline password hasher (self-contained, no dependency on basic plugin's
# internal helpers that may change).
# ---------------------------------------------------------------------------

_SCRYPT_N = 1 << 14      # 16384 — OWASP recommended for interactive logins
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_SALT_BYTES = 16
_SCRYPT_DKLEN = 32


def hash_password(password: str) -> str:
    """Return a ``scrypt$n$r$p$<salt_b64>$<dk_b64>`` hash string.

    Use this to precompute ``password_hash`` for users so plaintext never
    sits at rest in config.yaml::

        python3 -c "
        from plugins.dashboard_auth.multi_user_basic import hash_password
        print(hash_password('mypassword'))
        "
    """
    import hashlib
    import secrets
    salt = secrets.token_bytes(_SCRYPT_SALT_BYTES)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
        maxmem=0,
    )
    return (
        f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}$"
        f"{base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"
    )


def _hash_password(password: str) -> str:
    """Internal alias; calls the public function above."""
    return hash_password(password)
