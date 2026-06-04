#!/bin/bash
set -e

cd "$(dirname "$0")"

rm -rf build dist src/*.egg-info

python -m build

if [ -z "$PYPI_URL" ] || [ -z "$PYPI_USERNAME" ] || [ -z "$PYPI_PASSWORD" ]; then
    echo "请设置 PYPI_URL, PYPI_USERNAME, PYPI_PASSWORD 环境变量"
    exit 1
fi

python -m twine upload --repository-url "$PYPI_URL" \
    -u "$PYPI_USERNAME" -p "$PYPI_PASSWORD" dist/*

VERSION=$(grep -oP 'version\s*=\s*"\K[^"]+' pyproject.toml)
echo "发布完成: sdd-cli $VERSION"
