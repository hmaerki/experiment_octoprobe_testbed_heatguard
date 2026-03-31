from __future__ import annotations

import logging
import pathlib
import typing

import typer
from mpremote.transport_serial import TransportError
from octoprobe.scripts.op import iter_usb_tentacles
from octoprobe.scripts.op_logging import init_logging
from octoprobe.util_baseclasses import OctoprobeAppExitException
from octoprobe.util_pyudev import UdevPoller
from octoprobe.util_tentacle_label import label_renderer

from testbed_heatguard import constants, tentacle_spec
from testbed_heatguard.tentacles_inventory import TENTACLES_INVENTORY

logger = logging.getLogger(__file__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer()


@app.command()
def labels() -> None:
    init_logging()

    filename = constants.DIRECTORY_DOWNLOADS / "testbed_labels.pdf"
    label_renderer.create_report(
        filename=filename,
        layout=label_renderer.RendererLabelBolzoneDuo(),
        labels=TENTACLES_INVENTORY.labels_data,
    )
    print(f"Created: {filename}")


@app.command(help="Copy main.py to DUT.")
def dut_copy_main() -> None:
    with UdevPoller() as udev:
        poweron = True
        for usb_tentacle in iter_usb_tentacles(poweron=poweron, serials=None):
            tentacle = tentacle_spec.TentacleHeatguard.factory_usb_tentacle(
                usb_tentacle=usb_tentacle
            )
            try:
                tentacle.infra.load_base_code_if_needed()
            except (TransportError, OctoprobeAppExitException):
                continue
            tentacle.dut.boot_and_init_mp_remote_dut(tentacle=tentacle, udev=udev)
            src = constants.DIRECTORY_OF_THIS_FILE / "mp_dut_main.py"
            dest = ":main.py"
            tentacle.dut.mp_remote.cp(src=src, dest=dest, multiple=False)
            logger.info(f"{tentacle.dut.label}: Copied {src}")
            # Restart main
            tentacle.dut.mp_remote.exec_raw(
                cmd="import machine; machine.reset()",
                follow=False,
            )


@app.command(help="Flash micropython to DUT.")
def dut_flash() -> None:
    with UdevPoller() as udev:
        poweron = True
        for usb_tentacle in iter_usb_tentacles(poweron=poweron, serials=None):
            tentacle = tentacle_spec.TentacleHeatguard.factory_usb_tentacle(
                usb_tentacle=usb_tentacle
            )
            try:
                tentacle.infra.load_base_code_if_needed()
            except (TransportError, OctoprobeAppExitException):
                continue

            tentacle.flash_dut(
                udev=udev,
                firmware_spec=tentacle.tentacle_state.firmware_spec,
                directory_logs=pathlib.Path("/tmp/heatguard"),
            )


if __name__ == "__main__":
    app()
