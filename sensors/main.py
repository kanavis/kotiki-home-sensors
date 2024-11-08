import asyncio
import logging
import sys
from pathlib import Path

import click

from sensors.api.api import SensorAPI
from sensors.core.config import load_config
from sensors.core.errors import ArgumentError, ResponseParseError
from sensors.core.log import setup_logging
from sensors.tuya.devices import get_device_measurements as tuya_get_device_measurements

log = logging.getLogger(__name__)


@click.group()
def main(*_, **__):
    pass


@main.command()
@click.option("--config-file", type=Path, default=Path("./config.yml"))
@click.option("--debug", is_flag=True, default=False)
@click.option("--no-unit", is_flag=True, default=False)
@click.argument("device")
def get_tuya(config_file: Path, debug: bool, device: str, no_unit: bool):
    setup_logging(debug)
    config = load_config(config_file)
    try:
        measurements = tuya_get_device_measurements(config, device, no_unit=no_unit)
    except ArgumentError as err:
        log.error("Argument error: {}".format(err))
        sys.exit(1)
    except ResponseParseError as err:
        log.error("Response parse error: {}".format(err))
        sys.exit(1)
    else:
        log.info("Device '{}' measurements:".format(device))
        for name, value in measurements.items():
            log.info("  {}: {}".format(name, value))


@main.command()
@click.option("--config-file", type=Path, default=Path("./config.yml"))
@click.option("--debug", is_flag=True, default=False)
@click.option("--host", default="127.0.0.1")
@click.option("--port", type=int, default=8080)
def api(config_file: Path, debug: bool, host: str, port: int):
    setup_logging(debug)
    config = load_config(config_file)
    sensor_api = SensorAPI(config)
    asyncio.run(sensor_api.start(host=host, port=port))
