import json
import pathlib
import sys
import shutil

def resource_path(relative_path: str):
  """Construct the resource patch for a resource.

  Args:
      relative_path (str): The path relative to the resource path

  Returns:
      pathlib.Path: The path to the given resource
  """
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = pathlib.Path(pathlib.sys._MEIPASS)
  else:
    base_path = pathlib.Path()

  return base_path / "res" / relative_path

def base_path():
  """Construct the base path to the exe / project.

  Returns:
      pathlib.Path: The base path of the exectuable or project
  """ 
  # Get absolute path to resource, works for dev and for PyInstaller
  if getattr(sys, 'frozen', False):
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    return pathlib.Path(pathlib.sys.executable).parent
  else:
    return pathlib.Path()

def write_file(file_name: pathlib.Path, content: str):
  if file_name.exists():
    file_name.unlink()

  # Create parent directory if it doesnt exist
  file_name.parent.mkdir(parents=True, exist_ok=True)

  with file_name.open("x", buffering=16384) as file:
    file.write(content)

def write_json(file_name: pathlib.Path, content: dict):
  # Remove file if it exists
  if file_name.exists():
    file_name.unlink()

  # Create parent directory if it doesnt exist
  file_name.parent.mkdir(parents=True, exist_ok=True)

  with file_name.open("x") as file:
    json.dump(content, file, indent=2)

def remove_file_or_dir(path: pathlib.Path):
  """Removes a file or directory recursively. Does not throw an error if file does not exist.

  Args:
      path (pathlib.Path): The path to be removed
  """
  if path.is_dir():
    shutil.rmtree(path.absolute(), ignore_errors=True)
  else:
    path.unlink(missing_ok=True)