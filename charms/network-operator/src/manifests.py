# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Implementation of nvidia-network-operator kubernetes manifests."""

import logging
import pickle
from hashlib import md5
from typing import Dict, Optional

from ops.manifests import ConfigRegistry, ManifestLabel, Manifests

log = logging.getLogger(__file__)


class NetworkOperatorManifests(Manifests):
    """Deployment details for nvidia-network-operator."""

    def __init__(self, charm, charm_config):
        super().__init__(
            "network-operator",
            charm.model,
            "upstream/network-operator",
            [
                ManifestLabel(self),
                ConfigRegistry(self),
            ],
        )
        self.charm_config = charm_config

    @property
    def config(self) -> Dict:
        """Returns config mapped from charm config and joined relations."""
        config: Dict = {}
        config.update(**self.charm_config.available_data)

        for key, value in dict(**config).items():
            if value == "" or value is None:
                del config[key]

        return config

    def hash(self) -> int:
        """Calculate a hash of the current configuration."""
        return int(md5(pickle.dumps(self.config)).hexdigest(), 16)

    def evaluate(self) -> Optional[str]:
        """Determine if manifest_config can be applied to manifests."""
        # Placeholder for future config that affects our manifests
        return None
