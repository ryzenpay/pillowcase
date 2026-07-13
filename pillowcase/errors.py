class ConfigError(Exception):
    """Configuration / environment / validation error. Always fatal (exit 2)."""


class ProcessingError(Exception):
    """A single image failed to process. Governed by the failure policy."""
