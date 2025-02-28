# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing


import ops.testing
import pytest
from ops.testing import Harness

from charm import GPUOperatorCharm

ops.testing.SIMULATE_CAN_CONNECT = True


@pytest.fixture
def harness():
    harness = Harness(GPUOperatorCharm)
    try:
        yield harness
    finally:
        harness.cleanup()


def test_waits_for_config(harness: Harness, lk_client, caplog):
    harness.begin_with_initial_hooks()
    caplog.clear()
    harness.update_config(
        {
            "nfd-worker-conf": "sources: {}",
        }
    )

    messages = {r.message for r in caplog.records if "manifests" in r.filename}
    assert "Applying Node Feature Discovery ConfigMap Data" in messages
