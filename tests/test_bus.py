from unittest.mock import Mock

import pytest

from codex_harness.adapters.bus import RedisBus


@pytest.mark.parametrize("retain", [-1, 1.0, "1", None, True, False, [], float("inf")])
def test_compact_rejects_invalid_retention_before_accessing_redis(retain):
    bus = RedisBus("redis://localhost:6379")
    bus.client = Mock()
    with pytest.raises(ValueError, match="nonnegative integer"):
        bus.compact("worker", retain)
    assert bus.client.mock_calls == []
