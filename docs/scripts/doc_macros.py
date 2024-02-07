import re

# The versioning file for python
PYTHON_VERSION_FILE = ".python-version"

# The versioning file for node (used by nvm)
NVM_VERSION_FILE = ".nvmrc"

# RegEx string recommended for semver:
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
SEMVER_REGEX = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"


# Exception classes
class InvalidVersionException(Exception):
    """A version specified in `PYTHON_VERSION_FILE` or `NVM_VERSION_FILE` are of invalid format."""


class VersionFileNotFoundError(FileNotFoundError):
    """A version file specified in `PYTHON_VERSION_FILE` or `NVM_VERSION_FILE` was not found."""


def define_env(env):
    """
    Where mkdocs-macros are defined. For more info, see:
    https://mkdocs-macros-plugin.readthedocs.io/en/latest/macros/
    """

    # If python & node versions are left blank in mkdocs.yml, attempt to automatically populate them

    if env.variables.versions["python"]["version"] is None:
        py_ver = get_python_version()
        # Remove the patch number from the docs versioning
        env.variables.versions["python"]["version"] = ".".join(py_ver.split(".")[:-1])

        if env.variables.versions["python"]["packages"]["macos"] is None:
            env.variables.versions["python"]["packages"][
                "macos"
            ] = f"python@{'.'.join(py_ver.split('.')[:-1])}"

    if env.variables.versions["node"]["version"] is None:
        node_ver = get_node_version()

        # Remove the patch number from the docs versioning
        env.variables.versions["node"]["version"] = ".".join(node_ver.split(".")[:-1])


def get_python_version() -> str:
    """
    Returns the semantic version of the current Python runtime based off the specified `PYTHON_VERSION_FILE`
    """
    version: str

    try:
        with open(PYTHON_VERSION_FILE, "r") as py_ver:
            version = py_ver.read()

        if not valid_semver(version):
            raise InvalidVersionException(f'Unrecognized Python version: "{version}"!')

        return version
    except FileNotFoundError as err:
        raise VersionFileNotFoundError(
            f'Failed to find Python version file at "{PYTHON_VERSION_FILE}"'
        ) from err


def get_node_version() -> str:
    """
    Returns the semantic version of the current Node runtime based off the specified `NVM_VERSION_FILE`
    """
    version: str

    try:
        with open(NVM_VERSION_FILE, "r") as nvm_ver:
            version = nvm_ver.read()

        # Node version is usually in the format of "vX.X.X"
        if version.startswith("v"):
            version = version[1:]

        if not valid_semver(version):
            raise InvalidVersionException(f'Unrecognized Node version: "{version}"!')

        return version
    except FileNotFoundError as err:
        raise VersionFileNotFoundError(
            f'Failed to find Node version file at "{NVM_VERSION_FILE}"'
        ) from err


def valid_semver(version: str) -> bool:
    """
    Uses the suggested semver regex pattern to validate that the given version string is valid.
    """
    regex_match = re.match(SEMVER_REGEX, version)

    if regex_match is None:
        return False

    return True
