import os

import pyblish.api
from ayon_core.pipeline.publish import ValidateContentsOrder
from ayon_core.pipeline import PublishXmlValidationError

from version_control.rest.perforce.rest_stub import PerforceRestStub


class ValidateWorkspaceIsClean(pyblish.api.InstancePlugin):
    """Validates if local workspace has no uncomitted changes."""

    order = ValidateContentsOrder + 0.01
    label = "Validate P4 workspace is clean"
    families = ["changelist_metadata"]
    targets = ["local"]

    def process(self, instance):
        uncommitted_changes = PerforceRestStub.get_uncommitted_changes()
        if uncommitted_changes:
            raise Exception("Workspace has uncommitted changes! Please commit or revert before publish.")
        # # TODO: check for stream updates
