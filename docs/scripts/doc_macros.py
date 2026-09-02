import re

# The versioning file for python
PYTHON_VERSION_FILE = ".python-version"

# The versioning file for node (used by nvm)
NVM_VERSION_FILE = ".nvmrc"

# RegEx string recommended for semver:
# https://semver.org/#is-there-a-suggested-regular-expression-regex-to-check-a-semver-string
SEMVER_REGEX = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)(?:\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?)?$"


# Exception classes
class InvalidVersionException(Exception):
    """A version specified in `PYTHON_VERSION_FILE` or `NVM_VERSION_FILE` are of invalid format."""


class VersionFileNotFoundError(FileNotFoundError):
    """A version file specified in `PYTHON_VERSION_FILE` or `NVM_VERSION_FILE` was not found."""


def define_env(env):
    """
    Where the documentation macros are defined. For more info, see:
    https://zensical.org/docs/setup/extensions/macros/
    """

    # Zensical's macros extension merges the `extra` block into the template
    # variables only after this function has run, so `env.variables` is still
    # empty here - fall back to reading it straight off the config.
    versions = env.variables.get("versions") or env.conf["extra"]["versions"]

    # If python & node versions are left blank in zensical.toml, attempt to
    # automatically populate them. A blank value is read as an empty string.

    if not versions["python"]["version"]:
        versions["python"]["version"] = get_python_version()

    if not versions["node"]["version"]:
        versions["node"]["version"] = get_node_version()

    env.variables["versions"] = versions


def get_python_version() -> str:
    """
    Returns the semantic version of the current Python runtime based off the specified `PYTHON_VERSION_FILE`
    """
    version: str

    try:
        with open(PYTHON_VERSION_FILE) as py_ver:
            version = py_ver.read().strip()

        if not valid_semver(version):
            raise InvalidVersionException(
                f'Unrecognized Python version: "{version.strip()}"!'
            )

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
        with open(NVM_VERSION_FILE) as nvm_ver:
            version = nvm_ver.read().strip()

        # Node version is usually in the format of "vX.X.X"
        if version.startswith("v"):
            version = version[1:]

        # We specify only major version for node so skip this check.
        # if not valid_semver(version):
        #    raise InvalidVersionException(f'Unrecognized Node version: "{version}"!')

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
