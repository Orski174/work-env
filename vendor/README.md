# vendor/

Intentionally vendored (copied/frozen) external code lives here.

Default: contents are **gitignored**. Vendoring is a deliberate act — only copy
code here when you specifically want a frozen snapshot that won't move when the
source repo changes.

Prefer, in order:
1. **Reference** a sibling repo via `$REPOS_ROOT/<repo>` (no copy).
2. **Editable install**: `pip install -e "$REPOS_ROOT/<repo>"`.
3. **Vendor** here only when you need an isolated, frozen copy.

If you vendor something, record where it came from (repo + commit) in this file
or alongside the copied code, and force-add it if it must be committed:

```bash
git add -f vendor/<thing>
```
