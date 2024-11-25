import asyncio
import logging
import sys
from pathlib import Path

import click

from sensors.api.api import SensorAPI
from sensors.core.config import load_config
from sensors.core.errors import ArgumentError, ResponseParseError
from sensors.core.log import setup_logging
from sensors.prometheus.exporter import run_prometheus_exporter
from sensors.tuya.devices import get_device_measurements as tuya_get_device_measurements
from sensors.tuya.devices import query_gateway as tuya_query_gateway
from sensors.tuya.devices import query_unknown as tuya_query_unknown

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
    if device not in config.tuya_devices:
        raise ArgumentError("Tuya device '{}' doesn't exist".format(device))
    device_config = config.tuya_devices[device]
    try:
        if device_config.device_type == "gateway":
            print(tuya_query_gateway(config, device))
        elif device_config.device_type == "unknown":
            print(tuya_query_unknown(config, device))
        else:
            measurements = tuya_get_device_measurements(
                config, device, no_unit=no_unit,
            )
            log.info("Device '{}' measurements:".format(device))
            for name, value in measurements.items():
                log.info("  {}: {}".format(name, value))
    except ArgumentError as err:
        log.error("Argument error: {}".format(err))
        sys.exit(1)
    except ResponseParseError as err:
        log.error("Response parse error: {}".format(err))
        sys.exit(1)


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


@main.command()
@click.option("--config-file", type=Path, default=Path("./config.yml"))
@click.option("--debug", is_flag=True, default=False)
@click.option("--host", default="127.0.0.1")
@click.option("--port", type=int, default=8092)
def prometheus_exporter(config_file: Path, debug: bool, host: str, port: int):
    setup_logging(debug)
    config = load_config(config_file)
    if config.prometheus_exporter is None:
        raise RuntimeError("No prometheus exporter configured")
    run_prometheus_exporter(host, port, config)
