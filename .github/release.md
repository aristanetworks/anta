# Notes

Notes regarding how to release anta package

## Package requirements

- `bumpver`
- `build`
- `twine`

Also, [Github CLI](https://cli.github.com/) can be helpful and is recommended

## Bumping version

In a branch specific for this, use the `bumpver` tool.
It is configured to update:
* pyproject.toml
* docs/contribution.md
* docs/requirements-and-installation.md

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

> [!IMPORTANT]
> TODO - make this a github workflow

`x.x.x` is the version to be released

This is to be executed at the top of the repo

1. Checkout the latest version of `main` with the correct tag for the release
2. Create a new branch for release

   ```bash
   git switch -c rel/vx.x.x
   ```
3. [Optional] Clean dist if required
4. Build the package locally

   ```bash
   python -m build
   ```
5. Check the package with `twine` (replace with your vesion)

    ```bash
    twine check dist/*
    ```
6. Upload the package to test.pypi

    ```bash
    twine upload -r testpypi dist/anta-x.x.x.*
    ```
7. Verify the package by installing it in a local venv and checking it installs
   and run correctly (run the tests)

   ```bash
   # In a brand new venv
   pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --no-cache anta
   ```
8. Push to anta repository and create a Pull Request

    ```bash
    git push origin HEAD
    gh pr create --title 'bump: ANTA vx.x.x'
    ```
9. Merge PR after review and wait for [workflow](https://github.com/arista-netdevops-community/anta/actions/workflows/release.yml) to be executed.

   ```bash
   gh pr merge --squash
   ```

10. Like 7 but for normal pypi

    ```bash
    # In a brand new venv
    pip install anta
    ```

11. Test installed version

    ```bash
    anta --version
    ```