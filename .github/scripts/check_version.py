import toml

def get_version():
    # Load the pyproject.toml file
    pyproject = toml.load("pyproject.toml")
    return pyproject["tool"]["poetry"]["version"]

def is_minor_version_change(old_version, new_version):
    old_major, old_minor, old_patch = map(int, old_version.split('.'))
    new_major, new_minor, new_patch = map(int, new_version.split('.'))
    return (new_major == old_major and new_minor > old_minor)

# Example usage
old_version = get_version()  # Get the current version
new_version = "1.1.0"  # This should be dynamically determined based on your versioning strategy

if is_minor_version_change(old_version, new_version):
    print("Minor version changes are not allowed to be pushed to PyPI.")
    exit(1)  # Exit with an error code to prevent the publish step