# License: MIT
# Copyright © 2024 Frequenz Energy-as-a-Service GmbH

"""Timeseries basic types."""

from datetime import datetime, timezone
from typing import Final

UNIX_EPOCH: Final[datetime] = datetime.fromtimestamp(0.0, tz=timezone.utc)
"""The UNIX epoch (in UTC)."""
