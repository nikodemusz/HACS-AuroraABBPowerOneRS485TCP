# Release checklist

1. Update version in `custom_components/aurora_abb_powerone_tcp/manifest.json`
2. Update `CHANGELOG.md`
3. Verify GitHub Actions pass:
   - HACS
   - Hassfest
4. Create a Git tag like `v0.1.0`
5. Create a GitHub release with changelog notes
6. In HACS, refresh repository information
