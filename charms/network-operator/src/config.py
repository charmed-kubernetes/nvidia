# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Config Management for the nvidia-network-operator charm."""

import logging
from typing import Optional

import jsonschema
import yaml

log = logging.getLogger(__name__)


class CharmConfig:
    """Representation of the charm configuration."""

    NFD_SCHEMA = dict(
        type="object",
        properties={
            "sources": dict(type="object"),
        },
        required=["sources"],
    )
    POLICY_SCHEMA = dict(
        type="object",
        properties={
            "kind": dict(const="NicClusterPolicy"),
        },
        required=["kind"],
    )

    def __init__(self, charm):
        """Creates a CharmConfig object from the configuration data."""
        self.charm = charm

    @property
    def nfd_worker_conf(self) -> str:
        """Raw nfd-worker-conf config string, return empty string if falsy."""
        return self.charm.config.get("nfd-worker-conf") or ""

    @property
    def nic_cluster_policy(self) -> str:
        """Raw nic-cluster-policy config string, return empty string if falsy."""
        return self.charm.config.get("nic-cluster-policy") or ""

    @property
    def safe_nfd_worker_conf(self) -> Optional[dict]:
        """YAML representation of nfd-worker-conf."""
        return self._safe_yaml(self.nfd_worker_conf)

    @property
    def safe_nic_cluster_policy(self) -> Optional[dict]:
        """YAML representation of nic-cluster-policy."""
        return self._safe_yaml(self.nic_cluster_policy)

    def _safe_yaml(self, conf: str) -> Optional[dict]:
        """Parse yaml config string into a dict, return None on failure."""
        try:
            return yaml.safe_load(conf)
        except yaml.YAMLError:
            return None

    def evaluate(self) -> Optional[str]:
        """Determine if configuration is valid."""
        nfd_conf = self.safe_nfd_worker_conf
        if nfd_conf:
            try:
                jsonschema.validate(nfd_conf, self.NFD_SCHEMA)
            except jsonschema.ValidationError:
                return "nfd-worker-conf is invalid"
        else:
            return "nfd-worker-conf is not valid YAML"

        nic_policy = self.safe_nic_cluster_policy
        if nic_policy:
            try:
                jsonschema.validate(nic_policy, self.POLICY_SCHEMA)
            except jsonschema.ValidationError:
                return "nic-cluster-policy is invalid"
        else:
            return "nic-cluster-policy is not valid YAML"

        return None

    @property
    def available_data(self):
        """Parse valid charm config into a dict, drop keys if unset."""
        data = {}
        for key, value in self.charm.config.items():
            if key == "nfd-worker-conf":
                value = self.safe_nfd_worker_conf
            elif key == "nic-cluster-policy":
                value = self.safe_nic_cluster_policy
            data[key] = value

        for key, value in dict(**data).items():
            if value == "" or value is None:
                del data[key]

        return data
