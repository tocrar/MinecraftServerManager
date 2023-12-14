import urllib.request as requests
import json
from pathlib import Path
import os
import subprocess
import argparse

default_manifest_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
server_command = "java -Xmx1024M -Xms1024M -jar minecraft_server.1.20.4.jar nogui"

java_download_page = "https://adoptium.net/de/temurin/releases/"


def check_and_create_folder(path: Path):
    # Check if the path exists and is a folder
    if path.exists() and path.is_dir():
        return
    else:
        # Create the folder if it doesn't exist
        os.makedirs(path, exist_ok=True)
        return


def run_command(command):
    # Run the command in a new shell
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Get the output and error from the command
    output, error = process.communicate()

    # Decode the output and error to make them readable
    output = output.decode("utf-8")
    error = error.decode("utf-8")

    return output, error


class MinecraftServer:
    def __init__(self, version: str, type: str, meta_url: str):
        self.version = version
        self.type = type
        self.meta_url = meta_url
        self._data = None
        self.server_folder = Path("server_versions")

    def __str__(self):
        return f"MinecraftServer({self.version=}, {self.type=})"

    @property
    def server_file_path(self):
        return self.server_folder / f"minecraft_server.{self.version}.jar"

    @property
    def server_url(self) -> str:
        if self._data is None:
            self._update_data()
        return self._data.get("downloads", {}).get("server", {}).get("url", "")

    @property
    def java_version(self) -> int:
        if self._data is None:
            self._update_data()
        return self._data.get("javaVersion", {}).get("majorVersion", -1)

    @property
    def minimum_launcher_version(self) -> int:
        if self._data is None:
            self._update_data()
        return self._data.get("minimumLauncherVersion", -1)

    def _update_data(self):
        with requests.urlopen(self.meta_url) as request:
            self._data = json.load(request)

    def download_server(self):
        check_and_create_folder(self.server_folder)
        if not self.server_file_path.exists():
            print("Downloading server files please wait ...")
            requests.urlretrieve(self.server_url, self.server_file_path)
        print("Download done")

    def check_java(self):
        print(run_command(["java", "-version"]))


def get_version_manifest(url: str) -> dict:
    with requests.urlopen(url) as request:
        data = json.load(request)
    return data


def manifest_extract_meta(manifest: dict) -> dict:
    results = {}
    for version in manifest.get("versions", []):
        results[version["id"]] = MinecraftServer(
            version["id"], version["type"], version["url"]
        )
    latest = manifest.get("latest", {})
    results["latest_release"] = results.get(latest.get("release", None), None)
    results["latest_snapshot"] = results.get(latest.get("snapshot", None), None)
    return results


def update(**kwargs):
    print("Not implemented yet")


def download(version, **kwargs):
    print("downloading manifest")
    manifest = get_version_manifest(default_manifest_url)
    versions = manifest_extract_meta(manifest)
    if version in versions:
        versions[version].download_server()
    else:
        print(
            f"{version} is not a valid Version. Try 'latest_release' for the newest stable version"
        )


if __name__ == "__main__":
    # Create the top-level parser
    parser = argparse.ArgumentParser(prog="msm")
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")

    # Create the parser for the "update" command
    parser_update = subparsers.add_parser(
        "update", help="download and install the newest server"
    )
    parser_update.set_defaults(func=update)

    # Create the parser for the "download" command
    parser_download = subparsers.add_parser(
        "download", help="download a specific server version"
    )
    parser_download.add_argument("version", type=str, help="Version to download")
    parser_download.set_defaults(func=download)

    args = parser.parse_args()

    # Execute the function associated with the selected sub-command
    if hasattr(args, "func"):
        args.func(**vars(args))
    else:
        # Display help if no sub-command is provided
        parser.print_help()
