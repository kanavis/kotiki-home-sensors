import logging
from typing import Dict, Union, Optional

import tinytuya

from sensors.core.config import Config
from sensors.core.errors import ArgumentError, ResponseParseError

log = logging.getLogger(__name__)


def create_device(config: Config, device_name: str) -> tinytuya.Device:
    device_config = config.tuya_devices[device_name]
    kwargs = {}
    if device_config.parent is not None:
        kwargs["parent"] = create_device(config, device_config.parent)
    kwargs["dev_id"] = device_config.device_id
    if device_config.cid is not None:
        kwargs["cid"] = device_config.cid
    if device_config.address is not None:
        kwargs["address"] = device_config.address
    if device_config.local_key is not None:
        kwargs["local_key"] = device_config.local_key
    if device_config.version is not None:
        kwargs["version"] = device_config.version

    return tinytuya.Device(**kwargs)


def get_device_measurements(config: Config, device_name: str, no_unit=False) -> Dict[str, Union[str, int, float]]:
    if device_name not in config.tuya_devices:
        raise ArgumentError("Tuya device '{}' doesn't exist".format(device_name))
    device_config = config.tuya_devices[device_name]
    type_config = config.tuya_device_types[device_config.device_type]
    device = create_device(config, device_name)
    if not type_config.data_points:
        return {}
    log.debug("Getting device {} status".format(device_name))
    status = device.status()
    log.debug("Got device {} status {}".format(device_name, status))
    if status is None:
        raise ResponseParseError("Empty status from device")
    if "dps" not in status:
        raise ResponseParseError("No 'dps' field in status: {}".format(status))
    dps = status["dps"]

    result = {}
    for dp, dp_config in type_config.data_points.items():
        dp_key = str(dp)
        if dp_key not in dps:
            raise ResponseParseError("No dps[{}] field in data points: {}".format(dp_key, dps))
        value = dps[dp_key]
        if dp_config.multiplier is not None:
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except ValueError:
                    raise ResponseParseError("Value '{}' is not numeric, cannot apply multiplier".format(value))
            value = float(value) * dp_config.multiplier
        if dp_config.float_signs is not None and isinstance(value, float):
            value = "{{:.{}f}}".format(dp_config.float_signs).format(value)
        if not no_unit and dp_config.unit is not None:
            value = "{}{}".format(value, dp_config.unit)
        result[dp_config.name] = value

    return result


def query_gateway(config: Config, device_name: str) -> Optional[dict]:
    if device_name not in config.tuya_devices:
        raise ArgumentError("Tuya device '{}' doesn't exist".format(device_name))
    device = create_device(config, device_name)
    return device.subdev_query()


def query_unknown(config: Config, device_name: str) -> Optional[dict]:
    if device_name not in config.tuya_devices:
        raise ArgumentError("Tuya device '{}' doesn't exist".format(device_name))
    device = create_device(config, device_name)
    return device.status()
