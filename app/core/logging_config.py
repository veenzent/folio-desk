from loguru import logger
from fastapi import FastAPI
import sentry_sdk

def init_logging(app: FastAPI):
    logger.add("logs/app.log", rotation="1 MB", retention="10 days", enqueue=True)

    try:
        dsn = app.state.settings.sentry_dsn
    except AttributeError:
        dsn = ""
    
    if (dsn := app.state.settings.sentry_dsn):
        sentry_sdk.init(dsn=dsn, traces_sample_rate=1.0)
