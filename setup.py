"""
Followed from: https://github.com/cfengine/cf-remote
More: https://youtu.be/U-aIPTS580s
"""
from setuptools import setup
import subprocess

# Get the last tag from git
pmpy_version = (
    subprocess.run(["git", "describe", "--tags"], stdout=subprocess.PIPE)
    .stdout.decode("utf-8")
    .strip()
)

# Check version validation
assert "." in pmpy_version

setup(
    version=pmpy_version
)
