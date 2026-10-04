import warnings
from importlib import metadata

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

warnings.warn(
    "`langchain-experimental` is being sunset and is no longer actively "
    "maintained. See "
    "https://github.com/langchain-ai/langchain-experimental/issues/87 for "
    "details.",
    DeprecationWarning,
    stacklevel=2,
)
