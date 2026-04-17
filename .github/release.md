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

```
bumpver update --patch
```

and for a minor version

```
bumpver update --minor
```

Tip: It is possible to check what the changes would be using `--dry`

```
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

### Tips

#### Install from test pypi to run local tests between steps 2 and 4

   ```bash
   # In a brand new venv
   pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --no-cache anta[cli]
