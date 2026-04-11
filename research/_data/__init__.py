"""Data fetchers used by individual studies.

Each fetcher is responsible for one public source. They cache their output
to kuant-research/data_cache/ so subsequent runs are fast and offline.

Nothing in this subpackage touches WRDS or any licensed vendor — if a study
needs CRSP/Compustat, its own folder ships a `build_data.py` that reads
WRDS creds from the environment.
"""

from research._data.fetch_ff import fetch_ff5, fetch_ff_industries, fetch_ff_momentum_deciles
from research._data.fetch_cn import fetch_cn_indices

__all__ = [
    "fetch_ff5",
    "fetch_ff_industries",
    "fetch_ff_momentum_deciles",
    "fetch_cn_indices",
]
