# This file serves as an anchor to the frontend directory for easier imports in tests.

import inspect
from pathlib import Path


class FrontendAnchor:

    @staticmethod
    def get_location():
        return Path(inspect.getfile(FrontendAnchor)).parent.resolve()
