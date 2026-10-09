<!--
  ~ Copyright (c) 2026 Arista Networks, Inc.
  ~ Use of this source code is governed by the Apache License 2.0
  ~ that can be found in the LICENSE file.
  -->

# Notes

Notes regarding how to release anta package

## Package requirements

- `bumpver`

Also, [Github CLI](https://cli.github.com/) can be helpful and is recommended

## Bumping version

In a branch specific for this, use the `bumpver` tool.
It is configured to update:

- pyproject.toml
- docs/contribution.md
- docs/requirements-and-installation.md

For instance to bump a patch version:

```bash
bumpver update --patch
```

and for a minor version

```bash
bumpver update --minor
```

Tip: It is possible to check what the changes would be using `--dry`

```bash
bumpver update --minor --dry
```

## Creating release on Github

Create the release on Github with the appropriate tag `vx.x.x`

## Release version `x.x.x`

`x.x.x` is the version to be released

When publishing a version the workflow `release.yml` is run.

The workflow works as follow:

1. First build the wheel and the sdist for the package.
2. Release to test pypi using trusted publisher (it needs to be approved in GitHub UI).
3. Download the wheel from test pypi and run the tests by checking them out (testing on Linux, OSX and Windows).
4. Release to Pypi (it needs to be approved in Github UI).
5. Build and publish the doc.
6. Publish docker containers.
7. Announce the release in the ANTA-Field Google Chat room.

### Google Chat announcement

The release workflow checks for curated highlights before publishing artifacts and posts the ANTA-Field announcement only after PyPI, documentation, and Docker publishing have succeeded.

Set the `ANTA_FIELD_WEBHOOK_URL` GitHub Actions secret to the ANTA-Field incoming webhook URL.

GitHub's generated release-note configuration does not support adding a static placeholder section, so add a `Highlights` section to the GitHub release body before publishing:

```markdown
## Highlights

- Support for expanded results for a few tests
- Nicer markdown report
- Python 3.14 support added
```

If the `Highlights` section is missing or still contains placeholder text such as `TODO` or `TBD`, the release workflow stops before publishing to PyPI.

### Tips

#### Install from test pypi to run local tests between steps 2 and 4

   ```bash
   # In a brand new venv
   pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --no-cache anta[cli]
   ```
