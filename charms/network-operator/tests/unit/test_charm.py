# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Learn more about testing at: https://juju.is/docs/sdk/testing

import unittest.mock as mock

import ops.testing
import pytest
from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness

from charm import NetworkOperatorCharm

ops.testing.SIMULATE_CAN_CONNECT = True


@pytest.fixture
def harness():
    harness = Harness(NetworkOperatorCharm)
    try:
        yield harness
    finally:
        harness.cleanup()


def test_update_status(harness: Harness):
    harness.set_leader(is_leader=True)
    harness.begin_with_initial_hooks()
    harness.charm.on.update_status.emit()
    assert harness.charm.unit.status == ActiveStatus("Ready")


def test_install_or_upgrade_apierror(harness: Harness, lk_client, api_error_klass):
    lk_client.apply.side_effect = api_error_klass
    harness.begin_with_initial_hooks()
    charm = harness.charm
    charm.stored.config_hash = "mock_hash"
    mock_event = mock.MagicMock()
    charm._install_or_upgrade(mock_event)
    mock_event.defer.assert_called_once()
    assert isinstance(charm.unit.status, WaitingStatus)


def test_waits_for_config(harness: Harness, lk_client, caplog):
    harness.begin_with_initial_hooks()
    with mock.patch.object(lk_client, "list") as mock_list:
        mock_list.return_value = [mock.Mock(**{"metadata.annotations": {}})]
        caplog.clear()
        harness.update_config(
            {
                "nfd-worker-conf": "sources: None",
            }
        )

        messages = {r.message for r in caplog.records if "manifests" in r.filename}

        assert "Applying Node Feature Discovery ConfigMap Data" in messages
