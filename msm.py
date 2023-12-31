"""
This module provides the MinecraftServer class, 
designed to manage different aspects of a Minecraft server.

The MinecraftServer class allows users to interact with specific versions of Minecraft servers. 
It includes functionality for downloading server files. 
This module is intended for those who need to programmatically control 
and manage different Minecraft server instances, 
especially for different versions and build types (like release or snapshot).
"""

import os
import sys
import json
from pathlib import Path
import urllib.request as requests
import subprocess
import argparse

DEFAULT_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
SERVER_START_COMMAND = "java -Xmx1024M -Xms1024M -jar minecraft_server.1.20.4.jar nogui"
JAVA_DOWNLOAD_URL_PAGE = "https://adoptium.net/de/temurin/releases/"
DEFAULT_SERVER_FOLDER = Path("server_versions")


def check_and_create_folder(path: Path):
    """Check if a folder exist and if not create it

    Args:
        path (Path): path of the folder
    """
    if not (path.exists() and path.is_dir()):
        os.makedirs(path, exist_ok=True)


def bytes_with_unit(value, base=10):
    """Convert bits to a readable format with a unit"""
    bytes_ = value

    if base == 10:
        # Decimal units
        units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
        divisor = 1000
    else:
        # Binary units
        units = ["Bytes", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]
        divisor = 1024

    for unit in units:
        if bytes_ < divisor:
            return f"{bytes_:.2f} {unit}"
        bytes_ /= divisor
    return f"{bytes_:.2f} {units[-1]}"


def run_command(command):
    """Runs a shell command and returns the output

    Args:
        command (str, seq(str)): A string, or a sequence of program arguments
    """
    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    ) as process:
        output, error = process.communicate()
        output = output.decode("utf-8")
        error = error.decode("utf-8")
    return output, error


def download_progress(block_num, block_size, total_size):
    """
    Callback function that prints the download progress.
    """
    downloaded = block_num * block_size
    progress = 100 * downloaded / total_size
    sys.stdout.write(f"\rDownloading: {progress:.2f}%")
    sys.stdout.flush()


class MinecraftServer:
    """Represents a Minecraft server file with functionality to manage it"""

    def __init__(self, version: str, release_type: str, meta_url: str, path=None):
        self.version = version
        self.type = release_type
        self.meta_url = meta_url
        self._data = None
        self.server_folder = Path(path) or Path("server_versions")

    def __str__(self):
        return f"MinecraftServer({self.version=}, {self.type=})"

    @property
    def server_file_path(self):
        """The file path of the server jar file."""
        return self.server_folder / f"minecraft_server.{self.version}.jar"

    @property
    def server_url(self) -> str:
        """The URL from which the server jar file can be downloaded"""
        if self._data is None:
            self._update_data()
        return self._data.get("downloads", {}).get("server", {}).get("url", "")

    @property
    def server_file_size(self) -> int:
        """Returns the server file size in bits"""
        if self._data is None:
            self._update_data()
        return self._data.get("downloads", {}).get("server", {}).get("size", "")

    @property
    def client_file_size(self) -> int:
        """Returns the client file size in bits"""
        if self._data is None:
            self._update_data()
        return self._data.get("downloads", {}).get("client", {}).get("size", "")

    @property
    def java_version(self) -> int:
        """The required Java version for the server"""
        if self._data is None:
            self._update_data()
        return self._data.get("javaVersion", {}).get("majorVersion", -1)

    @property
    def minimum_launcher_version(self) -> int:
        """The minimum launcher version required by the client"""
        if self._data is None:
            self._update_data()
        return self._data.get("minimumLauncherVersion", -1)

    def _update_data(self):
        """Private method to update the server metadata by fetching it from the meta_url"""
        with requests.urlopen(self.meta_url) as request:
            self._data = json.load(request)

    def download_server(self):
        """Downloads the server jar file to the specified server_folder"""
        check_and_create_folder(self.server_folder)
        if not self.server_file_path.exists():
            print(f"Downloading minecraft_server.{self.version}.jar file...")
            requests.urlretrieve(
                self.server_url, self.server_file_path, download_progress
            )
        print("\nDownload done")

    def check_java(self):
        """Check if the system has the required java version"""
        print(run_command(["java", "--version"]))
        raise NotImplementedError()

    def print_info(self):
        """Prints verbose information about the version"""
        msg = (
            f"\tminecraft\n"
            f"\tversion: {self.version}\n"
            f"\ttype: {self.type}\n"
            f"\tjava_version: {self.java_version}\n"
            f"\tminimum_launcher_version: {self.minimum_launcher_version}\n"
            f"\tserver_url: {self.server_url}\n"
            f"\tserver_file_size: {bytes_with_unit(self.server_file_size)}\n"
            f"\tclient_file_size: {bytes_with_unit(self.client_file_size)}\n"
            f"\tmeta_url: {self.meta_url}"
        )
        print(msg)


def get_version_manifest(url: str) -> dict:
    """
    Download the minecraft manifest with the client and server versions
    """
    with requests.urlopen(url) as request:
        data = json.load(request)
    return data


def manifest_extract_meta(manifest: dict, server_folder) -> dict:
    """Parse the manifest"""
    results = {}
    for version in manifest.get("versions", []):
        results[version["id"]] = MinecraftServer(
            version=version["id"],
            release_type=version["type"],
            meta_url=version["url"],
            path=server_folder,
        )
    latest = manifest.get("latest", {})
    results["latest_release"] = results.get(latest.get("release", None), None)
    results["latest_snapshot"] = results.get(latest.get("snapshot", None), None)
    return results


def cmd_update(**kwargs):
    """Get the newest release or snapshot version based on running server"""
    print(f"{kwargs=}")
    raise NotImplementedError()


def cmd_download(version, **kwargs):
    """Command to download a specific server jar"""
    print("Downloading manifest")
    manifest = get_version_manifest(DEFAULT_MANIFEST_URL)
    versions = manifest_extract_meta(manifest, kwargs["folder"])
    if version in versions:
        versions[version].download_server()
    else:
        print(
            f"{version} is not a valid Version. Try 'latest_release' for the newest stable version"
        )


def cmd_info(version, **kwargs):
    """Command get information about a version"""
    print("Downloading manifest")
    manifest = get_version_manifest(DEFAULT_MANIFEST_URL)
    versions = manifest_extract_meta(manifest, kwargs["folder"])
    if version in versions:
        versions[version].print_info()
    else:
        print(
            f"{version} is not a valid Version. Try 'latest_release' for the newest stable version"
        )


if __name__ == "__main__":
    # Create the top-level parser
    parser = argparse.ArgumentParser(prog="msm")
    parser.add_argument(
        "--folder",
        type=str,
        default=DEFAULT_SERVER_FOLDER,
        help="Path to the server version folder",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Create the parser for the "update" command
    parser_update = subparsers.add_parser(
        "update", help="download and install the newest server"
    )
    parser_update.set_defaults(func=cmd_update)

    # Create the parser for the "download" command
    parser_download = subparsers.add_parser(
        "download", help="download a specific server version"
    )
    parser_download.add_argument("version", type=str, help="Version to download")
    parser_download.set_defaults(func=cmd_download)

    # Create the parser for the "info" command
    parser_info = subparsers.add_parser(
        "info", help="info for a specific server version"
    )
    parser_info.add_argument("version", type=str, help="Version to get infos on")
    parser_info.set_defaults(func=cmd_info)

    args = parser.parse_args()

    # Execute the function associated with the selected sub-command
    if hasattr(args, "func"):
        args.func(**vars(args))
    else:
        # Display help if no sub-command is provided
        parser.print_help()
