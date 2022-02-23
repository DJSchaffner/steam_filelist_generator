import sys
import pathlib
import re
import time
import os

from getopt import getopt

from utils import *
from logic import *

def print_usage():
  print("Usage: main.py [OPTIONS]\n" +
        "OPTIONS:\n" +
        "    -d VERSION Download manifests from latest version\n" + 
        "    -a Added files\n" +
        "    -m Modified files\n" +
        "    -r Removed files")

if __name__ == '__main__':
  # Extract options from parameters
  opt_values, args = getopt(sys.argv[1:], "d:amr")

  # After removing the options nothing should be left
  if len(args) != 0:
    print_usage()
    sys.exit()

  #date = time.mktime(time.strptime(args[0], "%d %B %Y – %H:%M:%S %Z"))
  download_option = list(filter(lambda x: x[0] == "-d", opt_values))
  download_path = base_path() / "download"

  if len(download_option) > 0:
    opt_values.remove(download_option[0])
    version = download_option[0][1].strip()
    destination_path = (download_path / version).absolute()

    if download_manifests(destination_path):
      # Remove depot downloader cache file
      remove_file_or_dir(destination_path / ".DepotDownloader")

      # Rename manifest files for later
      for filename in os.listdir(destination_path):
        depot = re.match(r'manifest_(\d+)_\d+\.txt', filename).groups()[0]
        (destination_path / filename).rename(f"{destination_path}/{depot}.txt")

  if len(opt_values) > 0:
    current_version = 59165
    previous_version = 58850

    current_files = os.listdir(download_path / str(current_version))
    previous_files = os.listdir(download_path / str(previous_version))

    out_folder = base_path() / "out"
    json_file = out_folder / f"{current_version}.json"

    # Clear out folder
    remove_file_or_dir(out_folder)

    # Prepare json content
    json_content = {  "version": int(current_version),
                      "date": 0,
                      "changed_depots": [] }

    # Iterate all depots that were present in previous version (Might be an issue if future version removes a depot)
    for depot in previous_files:
      removed = []
      added = []
      modified = []

      current_path = download_path / str(current_version) / depot
      previous_path = download_path / str(previous_version) / depot

      # Read manifest files
      current_manifest = read_manifest(current_path)
      previous_manifest = read_manifest(previous_path)

      # Initialize file sets
      current_set = set(current_manifest.files)
      previous_set = set(previous_manifest.files)

      # Find all removed files (Result contains removed files and files with different hash)
      diff_removed = list(previous_set.difference(current_set))
      diff_removed_names = set([x[0] for x in diff_removed])

      # Find all added files (Result contains added files and files with different hash)
      diff_added = list(current_set.difference(previous_set))
      diff_added_names = set([x[0] for x in diff_added])
      
      # Find all removed files (Remove files with same name but different hash)
      removed = set.difference(diff_removed_names, diff_added_names)

      # Find all added files (Remove files with same name but different hash)
      added = set.difference(diff_added_names, diff_removed_names)

      # Find all modified files (Retain files with same name but different hash)
      modified = set.intersection(diff_removed_names, diff_added_names)

      changes = []

      for opt, _ in opt_values:
        if opt == "-a":
          changes += added

        if opt == "-r":
          changes += removed

        if opt == "-m":
          changes += modified

      if len(changes) > 0:
        write_file(out_folder / depot, "\n".join(changes))
        json_content["changed_depots"].append({"depot_id": int(previous_manifest.depot), "manifest_id": int(previous_manifest.id)})

    # Write json files
      write_json(json_file, json_content)