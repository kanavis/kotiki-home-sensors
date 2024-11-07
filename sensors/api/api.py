import asyncio
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from fastapi import FastAPI, HTTPException

from sensors.core.config import Config
from sensors.tuya.devices import get_device_measurements as tuya_get_device_measurements


class SensorAPI:
    def __init__(self, config: Config):
        self.config = config
        self.app = FastAPI()
        self.app.get("/sensors/{name}")(self.api_sensors)
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def start(self, host: str, port: int):
        server = uvicorn.Server(uvicorn.config.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
        ))
        await server.serve()

    async def api_sensors(self, name: str):
        if name not in self.config.tuya_devices:
            raise HTTPException(status_code=404, detail="Sensor not found")
        loop = asyncio.get_running_loop()
        return {"measurements": loop.run_in_executor(self.executor, tuya_get_device_measurements, self.config, name)}
