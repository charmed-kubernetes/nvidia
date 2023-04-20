# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
"""Config Management for the nvidia-network-operator charm."""

import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

log = logging.getLogger(__file__)


class CustomResources(BaseModel):
    """Representation of the custom-resources config."""

    cr_yaml: str = Field(alias="custom-resources")


class CustomResourcesError(Exception):
    """Raised for any issue gathering custom-resources."""

    pass


class CharmConfig:
    """Representation of the charm configuration."""

    def __init__(self, charm):
        """Creates a CharmConfig object from the configuration data."""
        self.config = charm.config

    @property
    def custom_resources(self) -> CustomResources:
        """Get the custom-resources from config."""
        bad_cr_msg = "invalid custom-resources config."
        try:
            return CustomResources(**self.config)
        except ValidationError as e:
            raise CustomResourcesError(bad_cr_msg) from e

    @property
    def available_data(self):
        """Parse valid charm config into a dict, drop keys if unset."""
        data = {}
        for key, value in self.config.items():
            data[key] = value

        for key, value in dict(**data).items():
            if value == "" or value is None:
                del data[key]

        return data

    def evaluate(self) -> Optional[str]:
        """Determine if configuration is valid."""
        try:
            self.custom_resources
        except CustomResourcesError as e:
            return str(e)
        return None
