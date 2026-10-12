#!/usr/bin/env python3

import dspy
import logging
import os
import time
from dotenv import load_dotenv
from dspy.utils.callback import BaseCallback

load_dotenv()

API_BASE = "https://llm.ai.e-infra.cz/v1/"
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL", "mini")

logger = logging.getLogger("dspy.calls")
logger.setLevel(logging.INFO)
logger.propagate = False

file_handler = logging.FileHandler("dspy_calls.log", encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(message)s")
)
logger.addHandler(file_handler)


class FileLoggingCallback(BaseCallback):
    def __init__(self):
        self.started_at = {}

    def on_lm_start(self, call_id, instance, inputs):
        self.started_at[call_id] = time.monotonic()
        logger.info("LM call %s started: model=%s", call_id, instance.model)

    def on_lm_end(self, call_id, outputs, exception=None):
        started_at = self.started_at.pop(call_id, None)
        duration = time.monotonic() - started_at if started_at is not None else 0

        if exception is not None:
            logger.error(
                "LM call %s failed after %.2f s: %s",
                call_id,
                duration,
                exception,
            )
            return

        logger.info("LM call %s finished after %.2f s", call_id, duration)


if not API_KEY:
    raise RuntimeError("Missing API_KEY in .env")

lm = dspy.LM(
    f"openai/{MODEL}",
    api_base=API_BASE,
    api_key=API_KEY,
    callbacks=[FileLoggingCallback()],
)

dspy.configure(lm=lm)

messages = [
    {
        "role": "system",
        "content": "You are a helpful assistant"
    },
    {
        "role": "user",
        "content": "What is the capital of France?"
    }
]

print(lm(messages = messages))