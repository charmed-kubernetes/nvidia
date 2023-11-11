# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Implementation of nvidia-gpu-operator kubernetes manifests."""

import logging
import pickle
from hashlib import md5
from typing import Dict, Optional

import yaml
from lightkube.codecs import AnyResource, from_dict
from ops.manifests import ConfigRegistry, ManifestLabel, Manifests, Patch
from ops.manifests.manipulations import HashableResource

log = logging.getLogger(__file__)


class ApplyNFDConfigMap(Patch):
    """Update the NFD ConfigMap as a patch since the manifests include a default."""

    def __call__(self, obj):
        """Update the ConfigMap object in the deployment."""
        if not (
            obj.kind == "ConfigMap"
            and obj.metadata.name == "nvidia-charm-node-feature-discovery-worker-conf"
        ):
            return
        config = self.manifests.config.get("nfd-worker-conf")
        if not isinstance(config, dict):
            log.error(f"nfd-worker-conf was an unexpected type: {type(config)}")
            return
        log.info("Applying Node Feature Discovery ConfigMap Data")
        obj.data["nfd-worker.conf"] = yaml.safe_dump(config)


class GPUOperatorManifests(Manifests):
    """Deployment details for nvidia-gpu-operator."""

    def __init__(self, charm, charm_config):
        super().__init__(
            "gpu-operator",
            charm.model,
            "upstream/gpu-operator",
            [
                ManifestLabel(self),
                ConfigRegistry(self),
                ApplyNFDConfigMap(self),
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
        """Determine if config can be applied to manifests."""
        return None

    def apply_charm_manifests(self):
        """Apply manifests from disk as well as those from charm config."""
        self.apply_manifests()
