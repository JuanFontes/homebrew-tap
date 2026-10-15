#!/usr/bin/env python3
"""Update the tap only after verifying every supported release archive."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path

REPOSITORY = "JuanFontes/curlimp"
API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
PLATFORMS = ("macos-arm64", "linux-amd64", "linux-arm64")
VERSION = r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
HEX = r"[0-9a-f]{64}"


def formula_version(text):
    matches = re.findall(r'^  version "(' + VERSION + r')"$', text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError("Expected one explicit stable formula version")
    return matches[0]


def request(url, limit, *, api=False):
    headers = {"User-Agent": "curlimp-homebrew-updater"}
    if api and os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    if api:
        headers["Accept"] = "application/vnd.github+json"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers=headers), timeout=60
    ) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Response exceeds the permitted size")
    return data


def verify_asset(asset, url, limit):
    if asset.get("browser_download_url") != url:
        raise ValueError("Asset URL does not match the expected repository, tag, and filename")
    size = asset.get("size")
    digest = asset.get("digest", "")
    if type(size) is not int or not 0 < size <= limit:
        raise ValueError("Invalid release asset size")
    if not isinstance(digest, str) or not re.fullmatch("sha256:" + HEX, digest):
        raise ValueError("Missing SHA-256 asset digest")
    data = request(url, size)
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest[7:]:
        raise ValueError("Release asset size or SHA-256 digest mismatch")
    return data


def render(before, current, version, hashes):
    after = before.replace(f'  version "{current}"', f'  version "{version}"', 1)
    for platform, checksum in hashes.items():
        old_url = (
            f"https://github.com/{REPOSITORY}/releases/download/v{current}/"
            f"curlimp-{current}-{platform}.tar.gz"
        )
        new_url = (
            f"https://github.com/{REPOSITORY}/releases/download/v{version}/"
            f"curlimp-{version}-{platform}.tar.gz"
        )
        pattern = r'(?m)^( +)url "' + re.escape(old_url) + r'"\n\1sha256 "' + HEX + r'"$'
        after, count = re.subn(
            pattern,
            lambda m, url=new_url, sha=checksum: f'{m[1]}url "{url}"\n{m[1]}sha256 "{sha}"',
            after,
        )
        if count != 1:
            raise ValueError(f"Unrecognized formula layout for {platform}")
    return after


def update(formula, *, verify_current=False):
    before = formula.read_text()
    current = formula_version(before)
    release = json.loads(request(API, 1024 * 1024, api=True))
    tag = release.get("tag_name", "")
    if (
        release.get("draft") is not False
        or release.get("prerelease") is not False
        or not isinstance(tag, str)
        or not re.fullmatch("v" + VERSION, tag)
    ):
        raise ValueError("Expected a published stable release with a vMAJOR.MINOR.PATCH tag")
    version = tag[1:]
    current_parts = tuple(map(int, current.split(".")))
    version_parts = tuple(map(int, version.split(".")))
    if version_parts < current_parts or (version == current and not verify_current):
        return False

    assets = {}
    for asset in release.get("assets", []):
        name = asset.get("name")
        if not isinstance(name, str) or name in assets:
            raise ValueError("Invalid or duplicate release asset name")
        assets[name] = asset
    names = [f"curlimp-{version}-{platform}.tar.gz" for platform in PLATFORMS]
    if not all(name in assets for name in [*names, "SHA256SUMS"]):
        raise ValueError("Release is missing a supported archive or SHA256SUMS")
    base = f"https://github.com/{REPOSITORY}/releases/download/{tag}/"
    manifest = verify_asset(assets["SHA256SUMS"], base + "SHA256SUMS", 65536)
    checksums = {}
    for line in manifest.decode("ascii").splitlines():
        match = re.fullmatch("(" + HEX + r")  ([A-Za-z0-9._-]+)", line)
        if not match or match[2] in checksums:
            raise ValueError("Malformed or duplicate checksum entry")
        checksums[match[2]] = match[1]

    hashes = {}
    for platform, name in zip(PLATFORMS, names, strict=True):
        checksum = checksums.get(name)
        if not checksum or assets[name].get("digest") != "sha256:" + checksum:
            raise ValueError("SHA256SUMS and GitHub asset digests disagree")
        verify_asset(assets[name], base + name, 256 * 1024 * 1024)
        hashes[platform] = checksum
    after = render(before, current, version, hashes)
    if version == current and after != before:
        raise ValueError("Published checksums changed for the installed formula version")
    if after == before:
        return False

    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=formula.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(after)
        temporary.chmod(formula.stat().st_mode & 0o777)
        os.replace(temporary, formula)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formula", type=Path, default=Path("Formula/curlimp.rb"))
    parser.add_argument(
        "--verify-current",
        action="store_true",
        help="Also download and verify assets when the version is unchanged",
    )
    args = parser.parse_args()
    changed = update(args.formula, verify_current=args.verify_current)
    version = formula_version(args.formula.read_text())
    summary = f"changed={str(changed).lower()}\nversion={version}\n"
    print(summary, end="")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(summary)


if __name__ == "__main__":
    main()
