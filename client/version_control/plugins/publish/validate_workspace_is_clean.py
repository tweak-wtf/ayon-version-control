import os

import pyblish.api
from qtpy import QtWidgets

from ayon_core.tools.utils import ErrorMessageBox
from ayon_core.pipeline.publish import (
    ValidateContentsOrder,
    RepairAction,
    PublishValidationError,
)

from version_control.rest.perforce.rest_stub import PerforceRestStub

class ValidateWorkspaceIsClean(pyblish.api.InstancePlugin):
    """Validates if local workspace has no uncomitted changes."""

    order = ValidateContentsOrder + 0.01
    label = "Validate P4 workspace is clean"
    families = ["changelist_metadata"]
    targets = ["local"]
    actions = [RepairAction]

    def process(self, instance):
        uncommitted_changes = PerforceRestStub.get_uncommitted_changes()
        if uncommitted_changes:
            for change in uncommitted_changes:
                self.log.error(f"Uncommitted change: {change}")
            instance.data["uncommitted_changes"] = uncommitted_changes
            raise PublishValidationError("Workspace has uncommitted changes! Please commit or revert before publish.")
        # # TODO: check for stream updates

    @classmethod
    def repair(cls, instance):
        UncommittedChangesRepairer(instance.data["uncommitted_changes"]).exec_()


class UncommittedChangesRepairer(ErrorMessageBox):

    mb_submit_message: QtWidgets.QMessageBox = None
    lw_uncommitted_changes: QtWidgets.QListWidget = None

    def __init__(self, uncommitted_changes: list):
        self.title = "Pending Files in Changelist"
        self.parent = QtWidgets.QApplication.activeWindow()
        self.uncommitted_changes = uncommitted_changes
        super().__init__(self.title, self.parent)

    def _create_content(self, content_layout) -> None:
        label = QtWidgets.QLabel(
            "You have pending files in your changelist.\nPlease revert, shelve or submit them before launching Unreal Engine again."
        )
        content_layout.addWidget(label)

        self.lw_uncommitted_changes = QtWidgets.QListWidget()
        for change in self.uncommitted_changes:
            self.lw_uncommitted_changes.addItem(f"[{change['action'].upper()}]\t{change['clientFile']}")

        # allow multiple selection
        self.lw_uncommitted_changes.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )
        content_layout.addWidget(self.lw_uncommitted_changes)

        self.mb_submit_message = QtWidgets.QPlainTextEdit()
        self.mb_submit_message.setPlaceholderText("Enter a message for the submit")

        content_layout.addWidget(self.mb_submit_message)
        btn_revert_selected = QtWidgets.QPushButton("Revert Selected")
        btn_revert = QtWidgets.QPushButton("Revert All")
        btn_submit = QtWidgets.QPushButton("Submit")
        btn_revert.clicked.connect(self.on_revert)
        btn_revert_selected.clicked.connect(self.on_revert_selected)
        btn_submit.clicked.connect(self.on_submit)
        content_layout.addWidget(btn_revert_selected)
        content_layout.addWidget(btn_revert)
        content_layout.addWidget(btn_submit)

    def on_revert_selected(self):
        if self.lw_uncommitted_changes.selectedItems():
            for item in self.lw_uncommitted_changes.selectedItems():
                self.revert(item.text())
                # remove item from list
                self.lw_uncommitted_changes.takeItem(self.lw_uncommitted_changes.row(item))

        if self.lw_uncommitted_changes.count() == 0:
            self.accept()

    def on_revert(self):
        self.revert("//...")
        self.lw_uncommitted_changes.clear()
        self.accept()

    def revert(self, file):
        # TODO: implement
        pass

    def on_submit(self):
        if self.mb_submit_message.toPlainText() == "":
            errorbox = GenericErrorBox(
                "Submit Error", "Please enter a message for the submit"
            )
            errorbox.exec_()
            return

        # TODO: implement default changelist submission
        self.accept()
