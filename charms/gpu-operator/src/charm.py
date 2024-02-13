#!/usr/bin/env python3
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
"""Dispatch logic for the nvidia-gpu-operator charm."""

import logging
from typing import cast

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.manifests import Collector, ManifestClientError
from ops.model import ActiveStatus, BlockedStatus, MaintenanceStatus, WaitingStatus

from config import CharmConfig
from manifests import GPUOperatorManifests

log = logging.getLogger(__name__)


class GPUOperatorCharm(CharmBase):
    """Charm the service."""

    DEFAULT_NAMESPACE = "default"

    stored = StoredState()

    def __init__(self, *args):
        super().__init__(*args)

        # Config Validator and datastore
        self.charm_config = CharmConfig(self)
        self.stored.set_default(
            config_hash=None,  # hashed value of the applied config once valid
            deployed=False,  # True if the config has been applied after new hash
            namespace=self._configured_ns,
        )
        self.collector = Collector(
            GPUOperatorManifests(self, self.charm_config),
        )

        self.framework.observe(self.on.update_status, self._update_status)
        self.framework.observe(self.on.install, self._install_or_upgrade)
        self.framework.observe(self.on.upgrade_charm, self._install_or_upgrade)
        self.framework.observe(self.on.config_changed, self._merge_config)
        self.framework.observe(self.on.stop, self._cleanup)

    @property
    def _configured_ns(self) -> str:
        """Currently configured namespace."""
        return self.config["namespace"] or self.DEFAULT_NAMESPACE

    def _update_status(self, _):
        if not cast(bool, self.stored.deployed):
            return
        self.unit.status = MaintenanceStatus("Updating Status")

        unready = self.collector.unready
        current_ns, config_ns = self.stored.namespace, self._configured_ns
        if unready:
            self.unit.status = WaitingStatus(", ".join(unready))
        elif current_ns != config_ns:
            self.unit.status = BlockedStatus(
                f"Namespace '{current_ns}' cannot be configured to '{config_ns}'"
            )
        else:
            self.unit.status = ActiveStatus("Ready")
            self.unit.set_workload_version(self.collector.short_version)
            self.app.status = ActiveStatus(self.collector.long_version)

    def _check_config(self):
        self.unit.status = MaintenanceStatus("Evaluating charm config.")
        evaluation = self.charm_config.evaluate()
        if evaluation:
            self.unit.status = BlockedStatus(evaluation)
            return False
        return True

    def _merge_config(self, event):
        if not self._check_config():
            return

        self.unit.status = MaintenanceStatus("Evaluating Manifests")
        new_hash = 0
        for controller in self.collector.manifests.values():
            evaluation = controller.evaluate()
            if evaluation:
                self.unit.status = BlockedStatus(evaluation)
                return
            new_hash += controller.hash()

        self.stored.deployed = False
        if self._install_or_upgrade(event, config_hash=new_hash):
            self.stored.config_hash = new_hash
            self.stored.deployed = True

    def _install_or_upgrade(self, event, config_hash=None):
        if self.stored.config_hash == config_hash:
            log.info("Skipping until the config is evaluated.")
            return True

        self.unit.status = MaintenanceStatus("Deploying NVIDIA GPU Operator")
        self.unit.set_workload_version("")
        for controller in self.collector.manifests.values():
            try:
                controller.apply_charm_manifests()
            except ManifestClientError as e:
                self.unit.status = WaitingStatus("Waiting for kube-apiserver")
                log.warning(f"Encountered retryable installation error: {e}")
                event.defer()
                return False
        return True

    def _cleanup(self, event):
        if self.stored.config_hash:
            self.unit.status = MaintenanceStatus("Cleaning up NVIDIA GPU Operator")
            for controller in self.collector.manifests.values():
                try:
                    controller.delete_manifests(ignore_unauthorized=True)
                except ManifestClientError:
                    self.unit.status = WaitingStatus("Waiting for kube-apiserver")
                    event.defer()
                    return
        self.unit.status = MaintenanceStatus("Shutting down")


if __name__ == "__main__":
    main(GPUOperatorCharm)
