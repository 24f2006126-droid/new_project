from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values
import yaml
import os


app = FastAPI()

# Allow browser requests from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()

    # YAML layer
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            data = yaml.safe_load(f) or {}
            for k, v in data.items():
                config[k] = coerce(k, v)

    # .env layer
    env_file = dotenv_values(".env")

    if "NUM_WORKERS" in env_file:
        config["workers"] = coerce("workers", env_file["NUM_WORKERS"])

    if "APP_LOG_LEVEL" in env_file:
        config["log_level"] = env_file["APP_LOG_LEVEL"]

    # OS environment layer
    env_map = {
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
        }

    for env_name, key in env_map.items():
        if env_name in os.environ:
            config[key] = coerce(key, os.environ[env_name])

    # CLI overrides (?set=key=value)
    for item in set:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        config[key] = coerce(key, value)

    # Mask secret
    config["api_key"] = "****"

    return config