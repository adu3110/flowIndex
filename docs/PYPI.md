# Publishing to PyPI

FlowIndex uses [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) via GitHub Actions.

## One-time setup

1. Create an account at [pypi.org](https://pypi.org/account/register/) if needed.
2. On PyPI → **Your projects** → **Add new project** → name: `flowindex`
3. PyPI → **Account settings** → **Publishing** → **Add a new pending publisher**:
   - PyPI project name: `flowindex`
   - Owner: `adu3110`
   - Repository: `flowIndex`
   - Workflow: `publish.yml`
   - Environment: `pypi` (optional but recommended)
4. On GitHub → repo **Settings** → **Environments** → create `pypi` (no secrets required for trusted publishing).

## Publish a release

```bash
git tag v0.1.0
git push origin v0.1.0
gh release create v0.1.0 --title "v0.1.0" --notes "Initial public release."
```

The `Publish to PyPI` workflow runs on release publish.

Verify:

```bash
pip install flowindex
flowindex --help
```
