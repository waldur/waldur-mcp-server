# Releasing Waldur MCP Server

## Releasing a New Version via GitLab CI

To deploy a new release:

1. Create and push a new tag:
    ```bash
    git tag 0.1.0
    git push origin 0.1.0
    ```

2. The CI pipeline will automatically build and publish the package to PyPI.

## Building and Publishing manually

To prepare the package for distribution:

1. Sync dependencies and update lockfile:
    ```bash
    uv sync
    ```

2. Build package distributions:
    ```bash
    uv build
    ```

    This will create source and wheel distributions in the `dist/` directory.

3. Publish to PyPI:
    ```bash
    uv publish
    ```

Note: You'll need to set PyPI credentials via environment variables or command flags:
- Token: `--token` or `UV_PUBLISH_TOKEN`
- Or username/password: `--username`/`UV_PUBLISH_USERNAME` and `--password`/`UV_PUBLISH_PASSWORD`
