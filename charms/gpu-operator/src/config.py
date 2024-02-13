# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
"""Config Management for the nvidia-gpu-operator charm."""

import logging
from typing import Optional

import jsonschema
import yaml

log = logging.getLogger(__name__)

NFD_SCHEMA = {
    "type": "object",
    "properties": {
        "sources": {"type": "object"},
    },
    "required": ["sources"],
}


class CharmConfig:
    """Representation of the charm configuration."""

    def __init__(self, charm):
        self.charm = charm

    @property
    def nfd_worker_conf(self) -> str:
        """Raw nfd-worker-conf config string."""
        return self.charm.config.get("nfd-worker-conf", "")

    def _safe_yaml(self, conf: str) -> Optional[dict]:
        """Parse yaml config string into a dict, return None on failure."""
        try:
            return yaml.safe_load(conf)
        except yaml.YAMLError:
            return None

    def _is_valid(self, yaml: dict, schema: dict) -> bool:
        """Determine if given yaml is valid against the given schema."""
        try:
            jsonschema.validate(yaml, schema)
        except jsonschema.ValidationError:
            return False
        return True

    def evaluate(self) -> Optional[str]:
        """Determine if configuration is valid."""
        nfd_yaml = self._safe_yaml(self.nfd_worker_conf)
        if not (nfd_yaml and self._is_valid(nfd_yaml, NFD_SCHEMA)):
            return "nfd-worker-conf is invalid"

        return None

    @property
    def available_data(self):
        """Parse valid charm config into a dict, drop keys if unset."""
        data = {"namespace": self.charm.stored.namespace}
        safe_data = {
            "nfd-worker-conf": self._safe_yaml(self.nfd_worker_conf),
        }
        for key, value in self.charm.config.items():
            # use the safe value if we have one for this key
            data[key] = safe_data.get(key, value)

        for key, value in dict(**data).items():
            if value == "" or value is None:
                del data[key]

        return data
