# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Config Management for the nvidia-network-operator charm."""

import logging
from typing import Optional

import yaml

log = logging.getLogger(__name__)


class CharmConfig:
    """Representation of the charm configuration."""

    def __init__(self, charm):
        """Creates a CharmConfig object from the configuration data."""
        self.charm = charm

    @property
    def nfd_worker_conf(self) -> str:
        """Raw nfd-worker-conf config string, return empty string if falsy."""
        return self.charm.config.get("nfd-worker-conf") or ""

    @property
    def safe_nfd_worker_conf(self) -> Optional[dict]:
        """Parse nfd-worker-conf config into a dict, return None on failure."""
        try:
            return yaml.safe_load(self.nfd_worker_conf)
        except yaml.YAMLError:
            return None

    def evaluate(self) -> Optional[str]:
        """Determine if configuration is valid."""
        try:
            yaml.safe_load(self.nfd_worker_conf)
        except yaml.YAMLError:
            return "Config nfd-worker-conf is invalid."
        return None

    @property
    def available_data(self):
        """Parse valid charm config into a dict, drop keys if unset."""
        data = {}
        for key, value in self.charm.config.items():
            if key == "nfd-worker-conf":
                value = self.safe_nfd_worker_conf
            data[key] = value

        for key, value in dict(**data).items():
            if value == "" or value is None:
                del data[key]

        return data
