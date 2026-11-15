# POLISH — production status

The collaboration page is built from [status.json](status.json):

```sh
python3 tools/production/status-page.py polish
python3 tools/production/status-page.py polish --check
```

The generated page is `status/index.html` in the project's ignored workspace.
The local review address is recorded there. Director comments are incorporated
into the stable beat IDs and dated log before the page is rebuilt.

The [current treatment](brief.md) describes the published exchange, held-phone
framing and sound. The [original pitch](pitch-v1.md) is preserved unchanged.
[Publication and recovery](closeout.md) records the release and retained sources.
