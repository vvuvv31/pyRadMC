"""Forward lanes must load their module before any concurrent launch."""

from __future__ import annotations

import pytest

wp = pytest.importorskip("warp")

from pyradmc.backends.warp import kernels  # noqa: E402
from pyradmc.backends.warp.engine import WarpEngine  # noqa: E402

pytestmark = pytest.mark.warp


def test_forward_lanes_preload_transport_before_using_lane_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class LoadedBeforeWorkersError(Exception):
        pass

    def load(module: object, *, device: str) -> None:
        assert module is kernels
        assert device == "cuda:0"
        raise LoadedBeforeWorkersError

    monkeypatch.setattr(wp, "load_module", load)
    engine = object.__new__(WarpEngine)
    # No lane state is supplied: module loading must precede lane setup and
    # worker creation. A real cold CUDA compile is covered by integration tests.
    with pytest.raises(LoadedBeforeWorkersError):
        engine._run_forward_batch_lanes([], None, 2, 1, 1, device="cuda:0")
