import sys
import pathlib
import re
import time
import os

from getopt import getopt

from utils import *
from logic import *

# DLC Depots
DEPOT_BLACKLIST = [228987, 228988, 228990, 1389240, 1557210, 1869820, 2141580]

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

  #date = time.mktime(time.strptime(args[0], "%d %B %Y – %H:%M:%S %Z"))
  download_option = list(filter(lambda x: x[0] == "-d", opt_values))
  download_path = base_path() / "download"
  patches_json_path = base_path() / "remote" / "patches.json"

  # Make sure download path is empty and create it if necessary
  remove_file_or_dir(download_path)
  download_path.mkdir(parents=True)

  # After download option has no addition parameter, other options require two
  if len(download_option) == 0 and len(args) != 2:
    print_usage()
    sys.exit()

  # Load patches json
  with open(patches_json_path, "r") as f:
    patches_json = json.load(f)

  # Download option was chosen
  if len(download_option) > 0:
    opt_values.remove(download_option[0])
    version = download_option[0][1].strip()
    depots = []

    if download_current_manifests(download_path):
      # Rename manifest files for later
      for filename in os.listdir(download_path):
        # Extract depot and manifest id from downloaded file name
        depot_id, manifest_id = map(int, re.match(r'manifest_(\d+)_(\d+)\.txt', filename).groups()[:2])

        # Rename the file
        (download_path / filename).rename(f"{download_path}/{depot_id}.txt")

        # Ignore DLC Depots
        if not depot_id in DEPOT_BLACKLIST:
          # Add current depot to depot list
          depots.append({"depot_id": depot_id, "manifest_id": manifest_id})

    # Add new patch to json file and write it
    patches_json["patches"].append({"version": int(version), "date": 0, "depots": depots})
    write_json(patches_json_path, patches_json)

  # List option was chosen
  if len(opt_values) > 0:
    current_version = int(args[0])
    target_version = int(args[1])

    filtered_patches = list(filter(lambda x: x["version"] == current_version or x["version"] == target_version, patches_json["patches"]))

    if len(filtered_patches) != 2:
      print("At least one patch is not documented or ambigous!")
      sys.exit()

    current_patch = list(filter(lambda x: x["version"] == current_version, filtered_patches))[0]
    target_patch = list(filter(lambda x: x["version"] == target_version, filtered_patches))[0]

    out_path = base_path() / "out"
    json_file = out_path / f"{current_version}.json"

    # Clear out folder
    remove_file_or_dir(out_path)

    # Prepare json content
    json_content = {  "version": int(current_version),
                      "date": 0,
                      "changed_depots": [] }

    # Iterate all depots that were present in target version (Might be an issue if future version removes a depot)
    for current_depot, target_depot in zip(current_patch["depots"], target_patch["depots"]):
      depot_id = current_depot["depot_id"]
      current_manifest_id = current_depot["manifest_id"]
      target_manifest_id = target_depot["manifest_id"]

      # Only need to check for changes if manifest changed
      if current_manifest_id != target_manifest_id:
        removed = []
        added = []
        modified = []

        # Download manifests
        download_manifest(current_manifest_id, depot_id, download_path)
        download_manifest(target_manifest_id, depot_id, download_path)

        # Read manifest files
        current_manifest = read_manifest(download_path / f"manifest_{depot_id}_{current_manifest_id}.txt")
        target_manifest = read_manifest(download_path / f"manifest_{depot_id}_{target_manifest_id}.txt")

        # Initialize file sets
        current_set = set(current_manifest.files)
        target_set = set(target_manifest.files)

        # Find all removed files (Result contains removed files and files with different hash)
        diff_removed = list(target_set.difference(current_set))
        diff_removed_names = set([x[0] for x in diff_removed])

        # Find all added files (Result contains added files and files with different hash)
        diff_added = list(current_set.difference(target_set))
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
          write_file(out_path / f"{depot_id}.txt", "\n".join(changes))

          # Add depot to json list
          json_content["changed_depots"].append({"depot_id": int(target_manifest.depot), "manifest_id": int(target_manifest.id)})

    # Write json files
    write_json(json_file, json_content)