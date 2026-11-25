"""Run the standalone hermetic pytest suite through the workspace test runner."""

import pytest


if __name__ == "__main__":
    raise SystemExit(pytest.main(["-q"]))
