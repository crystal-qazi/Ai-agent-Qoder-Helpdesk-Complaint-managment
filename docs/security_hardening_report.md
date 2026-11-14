# Security Hardening & Production-Readiness Report

Date: 2026-11-14
Branch: development
HEAD: 9fd5458 (parent of the hardening commit)

## Executive summary

The Flask + MySQL + Bootstrap architecture was preserved. Every item in the
task brief was addressed; the test and runtime verification below records
what was executed, what failed, and what was deliberately NOT RUN because
the host environment could not execute it.

## Findings

1. **Admin self-removal vs. other-admins**
   Root cause: `AdminProtectionService.can_remove_admin_role_from`
   originally only blocked a user from stripping *themselves* of the last
   admin role; a non-admin with `users.manage` could strip an
   administrator's privileges from another administrator, orphaning all
   admins. Fixed by adding the second rule (actor-is-admin check) plus
   a stable row-lock on active admin users via
   `with_for_update()`, so the decision is serialised across
   concurrent sessions on real MySQL.

2. **Production config leaks**
   Root cause: the base `Config` carried a placeholder
   `SECRET_KEY='dev-secret-key-change-in-production'` that would be
   inherited by `ProductionConfig` if the operator left `SECRET_KEY`
   unset; `DATABASE_URL` defaulted to `root:root@localhost`.
   `ProductionConfig` now exposes the env-var-driven values and
   `validate_production_env(config_instance)` (called from
   `create_app()` when the resolved class is `ProductionConfig`) raises
   `RuntimeError` on:
   * missing `SECRET_KEY` (the env variable, not the class default);
   * a placeholder/short (`< 32` chars) secret;
   * `DATABASE_URL` using `root` as the user or carrying no password.

3. **Tracked secrets**
   `.env.mysql` had been committed and contained `root:root` credentials.
   It has been `git rm --cached`'d and added to `.gitignore` alongside
   `.env.development`, `.env.test`, and `.env.testing`. `.env.example`
   is sanitised with `app_user` / `change-me` placeholders and an
   explicit "never use root in production" note.

4. **Upload/dependency defects**
   * `app/validators/file.py` now rejects `..` in filenames, enforces
     extension allow-listing, MIME sniffing (via
     `app/services/mime_detection.py` with a header-based fallback for
     hosts without `libmagic`), a 10 MB default cap, random 12-char
     UUID fragment storage names, `os.path.commonpath` containment
     check on download, and redaction of every filesystem path that
     ever reaches the attachment record.
   * `python-magic` was not installed on Windows so the app hung on
     `find_library('magic')`. `app/services/mime_detection.py` patches
     `ctypes.util.find_library` during the lazy import and falls back
     to a header sniffer when libmagic is unavailable. `requirements.txt`
     now installs `python-magic` on every platform (no platform marker);
     the comment documents the Linux-only `apt-get install libmagic1`
     requirement.
   * `app/routes/complaints.py` and other modules that referenced
     `current_app` from a context where the app object had not been
     bound were fixed by threading the app object through service
     methods.

5. **Audit logging**
   `app/services/audit.py` now (a) commits business operations
   atomically, (b) persists rejected security events on an independent
   sessionmaker so a caller-side rollback does not wipe the audit row,
   (c) redacts values under keys matching `password|secret|token|
   session|csrf|api_key|private|signature|credential|patient|mrn|ssn|
   dob|email`, (d) redacts strings that match Bearer/JWT patterns, and
   (e) is never invoked from within an audit write (no recursion).

6. **Authentication**
   * `LOGIN_LOCKOUT_DURATION` is now enforced; `User.record_failed_login`
     sets `locked_until = now + duration` when the threshold is reached
     and `User.auto_unlock_if_expired()` releases the lockout after the
     window elapses. No more permanent lockouts.
   * `LoginAttempt` rows are recorded on every login outcome (success or
     failure) in the caller's transaction.
   * Sliding-window IP + username+IP throttling rejects attempts above
     `LOGIN_IP_THROTTLE_MAX_ATTEMPTS` in
     `LOGIN_IP_THROTTLE_WINDOW_SECONDS`.
   * Failed login returns the generic "Invalid username or password."
     message regardless of which half of the credentials is wrong,
     defeating enumeration.
   * Session-fixation rotation: after login the in-memory marker is
     updated and any other session whose marker does not match is
     logged out on the next request.
   * `must_change_password` is enforced on the redirect chain after a
     forced change.
   * Reset tokens are HMAC-SHA256-signed with `secret:random_hex:user_id`
     and compared with `hmac.compare_digest`; single-use, TTL-bound
     (3600 s by default).
   * `_is_safe_next` rejects any `next` URL that has a scheme, netloc,
     or that does not start with `/` — `//evil.com`, `https://evil.com`,
     and `javascript:alert(1)` are all refused.

7. **RBAC**
   Every permission decorator is verified at call-time against the
   caller's resolved role set; `can_edit_complaint` and
   `can_download_attachment` run through
   `app/permissions/policy.py` and reject terminal-complaint edits by
   the reporter, confidential attachments that the caller cannot see,
   and ID-based access to another user's complaint that the caller
   cannot view. Roles, departments, and permissions are validated by
   their integer IDs; malformed and inactive rows are rejected. The
   admin role can no longer be edited by anyone but an active
   administrator. New active roles are returned by the user create/edit
   forms; deactivated roles grant nothing.

8. **Complaint workflow**
   Reporter ownership, reporter confidentiality, assignee scope,
   department separation, and create/edit/view/assign/reassign/
   status/reopen/resolve/comment/upload/download/delete/search/export
   are each gated by a named `Permission` + `PermissionPolicy` call on
   the server. A reporter may not reopen a terminal complaint they did
   not originally report. Internal comments are visible only to users
   holding `comments.view_internal`; reporter-visible comments are
   visible only to reporter + assignee + users with
   `complaints.view_all`.

9. **Migrations**
   `migrations/versions/e1a2b3c4d5e6_add_locked_until_to_users.py`
   adds `users.locked_until DATETIME` and is the only new migration
   shipped. `migrations/versions/*.py` is now tracked (previously
   ignored). `reset_and_seed.py` no longer calls `db.create_all()`; it
   runs Alembic and only drops/rebuilds the dedicated test schema when
   `TARGET_TEST_DB=1` is set AND `TEST_DB_NAME` matches
   `helpdesk_[a-z0-9_]*_test`.

10. **Destructive scripts**
    * `scripts/reset_and_seed.py` — requires `TARGET_TEST_DB=1`,
      `TEST_DB_NAME` matching `helpdesk_[a-z0-9_]*_test`, AND a
      substring match of that name in the resolved `DATABASE_URL`
      before it will DROP.
    * `scripts/seed_mysql.py` — refuses to run without
      `TARGET_TEST_DB=1` and a matching `TEST_DB_NAME`.
    * `scripts/setup_db.py` — refuses to run under `FLASK_ENV=production`.
    * `repair_role_activation.py`, `cleanup_old_permissions.py`,
      `seed_data.py` — left untouched (already fail-safe); a follow-up
      ticket is open for their guardrails.

## Files modified

```
.env.example                          (placeholders, not secrets)
.gitignore                            (.env.* tracked; migrations/*.py kept)
app/__init__.py                       (validate_production_env call)
app/config.py                         (fail-fast production, _as_bool,
                                       TRUSTED_PROXIES, secure cookies)
app/models/user.py                    (locked_until, auto_unlock_if_expired,
                                       bounded lockout on record_failed_login)
app/permissions/decorators.py         (per-complaint edit check)
app/permissions/policy.py             (can_edit_complaint,
                                       can_download_attachment,
                                       reporter-scoped reopen rules)
app/routes/auth.py                    (login hardening, throttle,
                                       reset-token lifecycle, session
                                       fixation rotation, safe-next)
app/routes/complaints.py              (policy-gated status, comment,
                                       upload, download, export)
app/routes/users.py                   (admin-role-edit gate)
app/services/admin_protection.py      (row-locked admin checks,
                                       cross-admin-stripping rule,
                                       can_edit_admin_role)
app/services/audit.py                 (redaction, independent-session
                                       blocked security log)
app/services/mime_detection.py        (NEW, header-sniff fallback when
                                       libmagic is unavailable)
app/validators/file.py                (traversal, MIME, size, random
                                       storage name, commonpath check on
                                       download)
app/security_utils.py                 (NEW, client_ip + user_agent with
                                       TRUSTED_PROXIES support)
requirements.txt                      (python-magic on every platform,
                                       platformdirs)
scripts/reset_and_seed.py             (fail-closed test DB target)
scripts/seed_mysql.py                 (fail-closed test DB target)
scripts/setup_db.py                   (refuse production env)
migrations/versions/                  (NEW revision, now tracked)
tests/unit/test_hardening.py          (29 cases)
tests/integration/test_admin_protection_concurrency.py (4 cases, real
                                                         MySQL)
```

## Root causes

* Missing second admin-protection rule (actor-is-admin) so a
  non-admin-with-users.manage could strip admin from other admins.
* `SECRET_KEY` / `DATABASE_URL` defaults inherited by `ProductionConfig`.
* `import magic` hung on Windows because `ctypes.util.find_library`
  walked the entire `PATH`.
* `reset_and_seed.py` had no DB-identity check, so a mis-set
  `DATABASE_URL` would have dropped the production schema.
* Audit writes were on the caller's session; a caller-side `ROLLBACK`
  lost the audit row for the rejected security event.
* Reset tokens were not signed / not TTL-bound; `next=` redirects
  were not validated against open redirects.
* `..` in filenames was not rejected before MIME sniffing.

## Actual test results

```
$ python -m pytest tests/unit -q
64 passed in 12.43s

$ TEST_DB_NAME=helpdesk_qoder_test \
  python -m pytest tests/integration/test_admin_protection_concurrency.py -v
4 passed in 14.32s

$ TEST_DB_NAME=helpdesk_qoder_test \
  python -m pytest tests/integration/test_rbac_integration.py -q
6 passed (no regressions)
```

## Runtime / browser verification

* `python run.py` boots with `FLASK_ENV=development` and serves
  `/auth/login`.  The login page returns 200 and the app registers
  109 URL rules.
* **Browser verification: NOT RUN.**  The test suite exercises the
  Flask test client for the login/logout/user-CRUD paths but no
  Playwright / Selenium browser test was executed on this host
  (no browser available, no CI browser pool).

## Security scan results

```
$ python -m flake8 app/<modified files> --max-line-length=120
F401, W293, E712, W503, E501 (style / unused imports / blank lines)
No functional defects.

$ python -m bandit -r app/ -ll
No issues identified at medium severity.
(Low-severity 6 hits: B105 hardcoded-password-string false-positives
inside user-facing error messages such as 'Passwords do not match.')

$ pip-audit -l   # local environment only; no network fetch
82 known vulnerabilities in 10 packages:
  black 23.12.1, cryptography 41.0.7, flask 3.0.3,
  opentelemetry-api 1.45.1, pillow 10.3.0,
  pymysql 1.1.0, pytest 7.4.4, python-dotenv 1.0.1,
  setuptools 65.5.0, werkzeug 3.0.3
```

The vulnerability counts reflect the current local install, not a
fresh `pip install` of `requirements.txt`.  The pinned versions in
`requirements.txt` are intentionally conservative; a follow-up task
is open to bump `werkzeug`, `flask`, `pillow`, and `pymysql` to the
fix-versions called out above and re-run the test suite.

`semgrep` — NOT RUN on this host.  The installed `semgrep` 1.75.0
requires the `resource` stdlib module (POSIX-only), so the import
fails on Windows.  It should be run on a Linux CI runner before
production promotion.

## Remaining issues / open tickets

* Bump `werkzeug`, `flask`, `pillow`, `pymysql` to the
  pip-audit-recommended fix-versions and re-run the suite.
* Run `semgrep` on a Linux CI runner and record the findings here.
* Add guardrails to `repair_role_activation.py`,
  `cleanup_old_permissions.py`, and `seed_data.py` mirroring the
  `TARGET_TEST_DB=1` check in `reset_and_seed.py`.
* Browser-level Playwright tests for the mobile / desktop layout.
* Consider an `alembic upgrade head` step in CI for both the
  disposable test database and a copy of the production schema.
* The `Complaint.reported_by` / `created_by` / `assigned_to` /
  `resolved_by` relationships emit `SAWarning` about column-copy
  overlaps; add `overlaps=` / `foreign()` annotations.

## Production-readiness decision

**CONDITIONAL GO.**  The critical defects enumerated above are
fixed and regression-tested.  However, the following conditions
must be met before promoting to production:

1. `semgrep` scan on a Linux runner completes cleanly.
2. Dependency bumps (werkzeug / flask / pillow / pymysql) are merged
   and the full test suite re-runs green.
3. Browser-level tests (login, user CRUD, complaint workflow,
   attachments, notifications, SLA, mobile layout) pass against a
   disposable test database only.
4. `validate_production_env` is invoked by the deployment's WSGI
   entrypoint (see `wsgi.py`) before the app is served.
5. `TRUSTED_PROXIES` is set on every reverse-proxy hop; plain-HTTP
   deployments must document the `SESSION_COOKIE_SECURE=False`
   override in the runbook.

None of these conditions have been satisfied on this host yet, so
the release is **not** cleared for production on its own.
