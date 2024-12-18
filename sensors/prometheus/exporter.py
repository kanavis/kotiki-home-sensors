import dataclasses
import logging
import time
from typing import List

from prometheus_client import start_http_server, Gauge

from sensors.core.config import Config
from sensors.tuya.devices import get_device_measurements as tuya_get_device_measurements

log = logging.getLogger(__name__)


@dataclasses.dataclass
class DeviceMetrics:
    tuya_device_name: str
    metric_targets: dict[str, Gauge]


def collect_metrics(config: Config, metric: DeviceMetrics) -> List[str]:
    measurements = tuya_get_device_measurements(config, device_name=metric.tuya_device_name, no_unit=True)
    collected = []
    for metric_name, gauge in metric.metric_targets.items():
        value = float(measurements[metric_name])
        gauge.set(value)
        collected.append("{} -> {}: {}".format(metric_name, gauge, value))

    return collected


def run_prometheus_exporter(host: str, port: int, config: Config):
    log.info("Starting prometheus")
    start_http_server(addr=host, port=port)
    log.info("Prometheus server is listening on {}:{}".format(host, port))

    devices = []
    for device_name, device_config in config.prometheus_exporter.tuya_devices.items():
        metric_targets = {}
        for metric_name in device_config.measurements:
            gauge_name = "{}_{}".format(device_name, metric_name)
            metric_targets[metric_name] = Gauge(gauge_name, "Device '{}' metric '{}'".format(device_name, metric_name))
        devices.append(DeviceMetrics(
            tuya_device_name=device_name,
            metric_targets=metric_targets,
        ))

    last_exception = None
    while True:
        start_collecting = time.monotonic()
        try:
            for device_metric in devices:
                log.info("Collecting metrics from {}".format(device_metric.tuya_device_name))
                collected = collect_metrics(config, device_metric)
                log.info("Collected {} metrics {} from {}".format(
                    len(collected), collected, device_metric.tuya_device_name),
                )
                last_exception = None
        except Exception as e:
            log.exception(e)
            if last_exception:
                log.error("Two exceptions in a row. Throttling to 1 min")
                time.sleep(60)
            else:
                log.error("Exception happened, sleeping for 5 seconds")
                time.sleep(5)
            last_exception = e
        else:
            passed = time.monotonic() - start_collecting
            left = config.prometheus_exporter.request_every_sec - passed
            if left > 0:
                log.info("Sleeping for {:.2f} seconds".format(left))
                time.sleep(left)
            else:
                log.info("No time to sleep, going forward")
