import os
import sys

from .config import load_settings, load_profiles
from .errors import ConfigError
from .runner import run


def main(argv=None) -> int:
    try:
        settings = load_settings(os.environ)
        profiles = load_profiles(settings.config_path)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    return run(settings, profiles)


if __name__ == "__main__":
    sys.exit(main())
