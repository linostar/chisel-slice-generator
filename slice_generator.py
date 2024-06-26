#!/usr/bin/env python3

import sys
import argparse
import requests
import yaml
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# allow http[s] retries with increasing delays
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

ARCHS = ["x86_64", "aarch64", "arm", "i386", "powerpc64le", "riscv64", "s390x"]
GNUS = ["linux-gnu", "linux-gnueabihf"]


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False, *args, **kwargs):
        return super().increase_indent(flow, indentless=False, *args, **kwargs)


def map_release_version_to_name(version):
    version_map = {
        "20.04": "focal",
        "22.04": "jammy",
        "22.10": "kinetic",
        "23.04": "lunar",
        "23.10": "mantic",
        "24.04": "noble",
    }
    return version_map.get(version, None)


def represent_empty_string(dumper, data):
    if data == "":
        return dumper.represent_scalar("tag:yaml.org,2002:null", "")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


def get_package_dependencies(version_name, package_name):
    dependencies = []
    try:
        url = f"https://packages.ubuntu.com/{version_name}/{package_name}"
        response = http.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        uldeps = soup.find_all("ul", class_="uldep")
        for i, uldep in enumerate(uldeps):
            if i == 0:
                continue
            list_items = uldep.find_all("li")
            for li in list_items:  # skip the first item which is the title
                dep = li.find("a")
                if dep:
                    dependencies.append(dep.text)
    except requests.exceptions.RequestException as e:
        print(f"Network-related error: {e}", file=sys.stderr)
    except AttributeError as e:
        print(f"Parsing error: {e}", file=sys.stderr)
    finally:
        return sorted(dependencies)


def get_package_contents(version_name, arch, package_name):
    contents = []
    try:
        url = f"https://packages.ubuntu.com/{version_name}/{arch}/{package_name}/filelist"
        response = http.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        filelist = soup.find("div", attrs={"id": "pfilelist"})
        if filelist:
            pre_filelist = filelist.find("pre")
            for file in pre_filelist.text.splitlines():
                contents.append(file)
    except requests.exceptions.RequestException as e:
        print(f"Network-related error: {e}", file=sys.stderr)
    except AttributeError as e:
        print(f"Parsing error: {e}", file=sys.stderr)
    finally:
        return sorted(contents)


def filter_contents(contents):
    filtered = dict()
    license_dict = dict()
    for item in contents:
        if (
            not any(
                ext in item
                for ext in [
                    "/man/",
                    "/usr/share/doc",
                    "changelog",
                    "/usr/share/bug/",
                    "/usr/share/lintian/",
                    "README",
                ]
            )
        ):
            filtered[item] = ""
        if (
            any(
                ext in item
                for ext in [
                    "/copyright",
                    "/COPYRIGHT",
                    "/license_dict",
                    "/LICENSE_dict",
                ]
            )
        ):
            license_dict[item] = ""
    return filtered, license_dict


def simplify_contents(contents):
    # simplify multiple files and replace them by one that has a glob pattern
    for content in list(contents.keys()):
        similar_contents = [x for x in list(contents.keys()) if content in x]
        if len(similar_contents) > 1:
            contents[content + "*"] = ""
            for similar in similar_contents:
                del contents[similar]

    # replace arch and gnu names by correspondant glob patterns
    keys = list(contents.keys())
    for i, _ in enumerate(keys):
        for gnu in GNUS:
            keys[i] = keys[i].replace(gnu, "linux-*")
        for arch in ARCHS:
            keys[i] = keys[i].replace(arch, "*")
    return dict.fromkeys(keys, "")


def generate_yaml(package_name, dependencies, contents, license_dict):
    data = {
        "package": package_name,
        "essential": [f"{package_name}_copyright"],
        "slices": {
            "all": {
                "essential": dependencies,
                "contents": contents,
            },
            "copyright": {
                "contents": license_dict
            },
        },
    }

    if not license_dict:
        del data["essential"]
        del data["slices"]["copyright"]

    if not dependencies:
        del data["slices"]["all"]["essential"]

    Dumper.add_representer(str, represent_empty_string)

    return yaml.dump(
        data, default_flow_style=False, sort_keys=False, Dumper=Dumper
    )


def main():
    parser = argparse.ArgumentParser(
        description="Fetch package dependencies and contents for a given Ubuntu release."
    )

    parser.add_argument(
        "release_version",
        help="Ubuntu release version, e.g., 22.04, 22.10, 23.04, 23.10, 24.04",
    )
    parser.add_argument("arch", help="Architecture, e.g., amd64, arm64, s390x")
    parser.add_argument(
        "package_name",
        help="Debian package name, e.g., curl, libssl3, python3.12-minimal",
    )
    args = parser.parse_args()

    version_name = map_release_version_to_name(args.release_version)
    if not version_name:
        print(f"Invalid release version: {args.release_version}")
        return

    dependencies = get_package_dependencies(version_name, args.package_name)
    contents = get_package_contents(version_name, args.arch, args.package_name)
    filtered_contents, license_dict = filter_contents(contents)
    yaml_output = generate_yaml(
        args.package_name,
        dependencies,
        simplify_contents(filtered_contents),
        license_dict
    )

    print(yaml_output)


if __name__ == "__main__":
    main()
