import dataclasses
from pathlib import Path
from typing import Dict, Optional

import yaml

from sensors.core.errors import ConfigParseError
from sensors.core.retort import base_retort


@dataclasses.dataclass
class TuyaDataPoint:
    name: str
    multiplier: Optional[float] = None


@dataclasses.dataclass
class TuyaDeviceType:
    data_points: Dict[int, TuyaDataPoint] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class TuyaDevice:
    device_type: str
    device_id: str
    version: Optional[float] = None
    cid: Optional[str] = None
    local_key: Optional[str] = None
    address: Optional[str] = None
    parent: Optional[str] = None


@dataclasses.dataclass
class Config:
    tuya_device_types: Dict[str, TuyaDeviceType] = dataclasses.field(default_factory=dict)
    tuya_devices: Dict[str, TuyaDevice] = dataclasses.field(default_factory=dict)


retort = base_retort


def load_config(config_path: Path) -> Config:
    with open(config_path, "r", encoding="utf-8") as f:
        config = retort.load(yaml.safe_load(f), Config)
    for device_name, device in config.tuya_devices.items():
        if device.device_type != "gateway" and device.device_type not in config.tuya_device_types:
            raise ConfigParseError("Config validation error: device '{}' has unknown type '{}'".format(
                device_name, device.device_type,
            ))
        if device.parent is not None and device.parent not in config.tuya_devices:
            raise ConfigParseError("Config validation error: device '{}' has unknown parent '{}'".format(
                device_name, device.parent,
            ))
    return config
