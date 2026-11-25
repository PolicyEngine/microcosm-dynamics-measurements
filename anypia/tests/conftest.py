"""Keep all pytest/Hypothesis artifacts inside the assigned anypia directory."""

from pathlib import Path
import os


ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("HYPOTHESIS_STORAGE_DIRECTORY", str(ROOT / "work/hypothesis"))

from hypothesis import settings
from hypothesis.database import DirectoryBasedExampleDatabase

settings.register_profile("anypia", database=DirectoryBasedExampleDatabase(ROOT / "work/hypothesis/examples"))
settings.load_profile("anypia")


def pytest_configure(config):
    if config.option.basetemp is None:
        config.option.basetemp = str(ROOT / "work/pytest-temp")
