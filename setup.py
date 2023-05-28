"""
Followed from: https://github.com/cfengine/cf-remote
More: https://youtu.be/U-aIPTS580s
"""
import re
import subprocess
from setuptools import setup

def get_version() -> str:
    """get the last version tag from git

    Returns:
        str: version tag
    """
    return subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE,check=False).stdout.decode("utf-8").strip()

def validate_version(version: str) -> bool:
    """Validate Version (example: 1.0.1)

    Args:
        version (str): version

    Returns:
        bool: if it validates, returns True, else False
    """
    pattern = r'\d+\.\d+\.\d+'
    return bool(re.match(pattern, version))


# get version
simpm_version = get_version()
# version validation
assert validate_version(simpm_version)
# setup
setup(version=simpm_version)
