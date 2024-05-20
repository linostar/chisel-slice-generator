#!/usr/bin/env python3

import sys
import requests
import argparse
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


class Dumper(yaml.Dumper):
    def increase_indent(self, flow=False, *args, **kwargs):
        return super().increase_indent(flow=flow, indentless=False)


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
        for i in range(len(uldeps)):
            if i == 0:
                continue
            uldep = uldeps[i]
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
                ]
            )
            or "copyright" in item
            or "license" in item
        ):
            filtered[item] = ""
    return filtered


def generate_yaml(package_name, dependencies, contents):
    data = {
        "package": package_name,
        "slices": {"all": {"essentials": dependencies, "contents": contents}},
    }
    yaml.add_representer(str, represent_empty_string)
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
    filtered_contents = filter_contents(contents)
    yaml_output = generate_yaml(
        args.package_name, dependencies, filtered_contents
    )

    print(yaml_output)


if __name__ == "__main__":
    main()
