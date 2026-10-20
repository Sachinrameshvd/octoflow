import os
import pytest

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def clean_dry_run_env():
    orig_dry = os.environ.get("OCTOFLOW_DRY_RUN")
    orig_force = os.environ.get("OCTOFLOW_FORCE_LIVE")
    os.environ.pop("OCTOFLOW_DRY_RUN", None)
    os.environ.pop("OCTOFLOW_FORCE_LIVE", None)
    yield
    if orig_dry is not None:
        os.environ["OCTOFLOW_DRY_RUN"] = orig_dry
    else:
        os.environ.pop("OCTOFLOW_DRY_RUN", None)
    if orig_force is not None:
        os.environ["OCTOFLOW_FORCE_LIVE"] = orig_force
    else:
        os.environ.pop("OCTOFLOW_FORCE_LIVE", None)
