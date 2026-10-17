import sys

import ingestion
import matplotlib
import numpy
import pandas
import pyarrow
import sklearn


def test_project_environment_smoke() -> None:
    assert sys.version_info[:2] == (3, 12)
    assert sys.prefix != sys.base_prefix
    assert ingestion.__file__ is not None
    assert matplotlib.__version__
    assert numpy.__version__
    assert pandas.__version__
    assert pyarrow.__version__
    assert sklearn.__version__
