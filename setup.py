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
        str: version tag in PEP 440 format, defaults to '0.0.0' if git describe fails
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags"], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5
        )
        version_tag = result.stdout.decode("utf-8").strip()
        
        if version_tag:
            # Handle git describe format like "v2.0.3-334-g4f69b64"
            # Convert to "2.0.3.post334" for PEP 440 compliance
            match = re.match(r'v?(\d+\.\d+\.\d+)(?:-(\d+)-g[a-f0-9]+)?', version_tag)
            if match:
                base_version = match.group(1)
                commits_since = match.group(2)
                
                if commits_since:
                    # Format: version.post<commits_since>
                    return f"{base_version}.post{commits_since}"
                else:
                    # Exact tag match
                    return base_version
    except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
        pass
    
    # Fallback version for detached HEAD or when git is not available
    # (e.g., Read the Docs builds)
    return "0.0.0"

def validate_version(version: str) -> bool:
    """Validate Version (matches PEP 440 format)

    Args:
        version (str): version string

    Returns:
        bool: if it validates, returns True, else False
    """
    # Matches PEP 440: X.Y.Z with optional .postN, .devN, etc.
    pattern = r'^\d+\.\d+\.\d+([.-]?\w+)?$'
    return bool(re.match(pattern, version))


# get version
simpm_version = get_version()
# version validation - log warning if invalid but still use it
if not validate_version(simpm_version):
    print(f"Warning: Version '{simpm_version}' may not match semantic versioning pattern")
    # Still use the version even if it doesn't validate perfectly

# setup
setup(version=simpm_version)
