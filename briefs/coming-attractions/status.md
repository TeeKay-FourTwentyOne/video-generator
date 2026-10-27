# Coming Attractions — status page

The collaboration status page for this film is built from [status.json](status.json)
with the shared `production-status` skill:

```sh
python3 tools/production/status-page.py coming-attractions
```

The generated page lives in the ignored workspace (`status/index.html`) and is
published privately for the director's comments; the published URL is kept in the
workspace, not here. Scene and beat IDs in `status.json` are stable so that comments
and links keep their meaning. Statuses on the page are authored from decisions and
reviewed results, never inferred from files; no prices appear on it.
