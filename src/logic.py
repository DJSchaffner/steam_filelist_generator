import time
import shutil
from dataclasses import dataclass
import re

import pexpect
import pexpect.popen_spawn

from utils import *

@dataclass
class Manifest():
  depot: int
  id: int
  date: int
  num_files: int
  num_chunks: int
  size_disk: int
  size_compressed: int
  files: list

def download_manifests(destination_path: pathlib.Path):
  depot_downloader_path = str(resource_path("DepotDownloader/DepotDownloader.dll").absolute())
  args = ["dotnet", str(depot_downloader_path), 
          "-app", "813780",
          "-username", "hellgameroriginal", 
          "-password", "reinda8426", 
          "-remember-password",
          "-dir", str(destination_path),
          "-manifest-only"]

  # Make sure destination folder is empty
  if destination_path.exists():
    try:
      shutil.rmtree(destination_path)
    except BaseException:
      print("Error removing previous download directory")
      
  destination_path.mkdir(parents=True)

  # Spawn process and store in queue
  p = pexpect.popen_spawn.PopenSpawn(" ".join(args), encoding="utf-8")
  p.logfile_read = sys.stdout

  try:
    responses = [
      "result: OK",
      "Please enter .*: ",
      pexpect.EOF
    ]

    # Default timeout in seconds
    timeout = 15
    response = p.expect(responses, timeout=timeout)

    # Success
    if response == 0:
      success = True

    # Code required
    elif response == 1:       
      p.sendline(input())

       # Invalid code
      if p.expect(responses, timeout=timeout) == 1:
        raise ConnectionError("Invalid authentication code") 
      else:
        success = True

    # Error
    elif response == 2:
      raise ConnectionError("Error logging into account")

    # Wait for program to finish
    p.expect(pexpect.EOF, timeout=None)
  except pexpect.exceptions.TIMEOUT as e:
    print("Error waiting for DepotDownloader to start")
  except ConnectionError as e:
    print(e)

  return success

def read_manifest(file: pathlib.Path):
  result = None

  with open(file, "r") as f:
    depot = 0
    id = 0
    date = 0
    num_files = 0
    num_chunks = 0
    size_disk = 0
    size_compressed = 0
    files = []

    line = f.readline() # First line contains depot id
    depot = re.match(r".* (\d+)", line).groups()[0]

    # Second lines is empty
    # Third contains manifest id and date
    line = f.readline()
    line = f.readline()
    groups = re.match(r".* : (\d+) \/ (.+)", line).groups()
    id = groups[0]
    date = time.mktime(time.strptime(groups[1], "%d.%m.%Y %H:%M:%S"))

    # Fourth line contains number of files
    line = f.readline()
    groups = re.match(r".* : (\d+)", line).groups()
    num_files = groups[0]

    # Fifth line contains number of chunks
    line = f.readline()
    groups = re.match(r".* : (\d+)", line).groups()
    num_chunks = groups[0]

    # Sixth line contains size on disk
    line = f.readline()
    groups = re.match(r".* : (\d+)", line).groups()
    size_disk = groups[0]

    # Seventh line contains size compressed
    line = f.readline()
    groups = re.match(r".* : (\d+)", line).groups()
    size_compressed = groups[0]

    # Eighth line is empty
    # Nineth line contains headers
    # Tenth line until EOF contains one file per line
    line = f.readline()
    line = f.readline()
    while line := f.readline():
      groups = re.match(r"\s+\d+\s+\d+\s+(.{40})\s+\d+\s+(.+)", line)
      files.append((groups[2], groups[1]))

    result = Manifest(depot, id, date, num_files, num_chunks, size_disk, size_compressed, files)

  return result