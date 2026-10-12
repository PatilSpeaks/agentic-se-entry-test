
import json
import sys
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen


def get_pypi_data(url):
    """Fetch JSON data from PyPI."""
    try:
        with urlopen(url, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return None
        raise


def check_requirements(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    dependencies_checked = len(lines)
    packages_not_found = 0
    versions_not_found = 0
    oldest_release = None
    oldest_date = None

    for line in lines:
        requirement = line.strip()

        if not requirement or requirement.startswith("#"):
            continue

        if "==" not in requirement:
            print(f"Skipping unpinned requirement: {requirement}")
            continue

        name, version = requirement.split("==", 1)
        name = name.strip()
        version = version.strip()

        if not name or not version:
            print(f"Skipping invalid requirement: {requirement}")
            continue

        package_url = (
            f"https://pypi.org/pypi/{quote(name, safe='')}/json"
        )

        package_data = get_pypi_data(package_url)

        if package_data is None:
            packages_not_found += 1
            continue

        version_url = (
            f"https://pypi.org/pypi/"
            f"{quote(name, safe='')}/"
            f"{quote(version, safe='')}/json"
        )

        version_data = get_pypi_data(version_url)

        if version_data is None:
            versions_not_found += 1
            continue

        for uploaded_file in version_data.get("urls", []):
            upload_time = uploaded_file.get("upload_time")

            if not upload_time:
                continue

            date = datetime.fromisoformat(upload_time)

            if oldest_date is None or date < oldest_date:
                oldest_date = date
                oldest_release = f"{name}=={version}"

    print(f"Dependencies checked: {dependencies_checked}")
    print(f"Packages not on PyPI: {packages_not_found}")
    print(f"Versions not on PyPI: {versions_not_found}")

    if oldest_release is not None:
        print(
            f"Oldest pinned release: "
            f"{oldest_release} ({oldest_date.year})"
        )
    else:
        print("Oldest pinned release: None")


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "requirements.txt"

    try:
        check_requirements(filename)
    except FileNotFoundError:
        print(f"File not found: {filename}")
        sys.exit(1)
    except (HTTPError, URLError, TimeoutError) as error:
        print(f"PyPI request failed: {error}")
        sys.exit(1)
