"""
Smoke-test configuration.

This keeps the real environment, agent, forecaster, cache, CSV export, and
plotting pipeline, but reduces the run size so failures are visible quickly.
"""

from config_full import *  # noqa: F403


CALIB_EPISODES = 3
TEST_EPISODES = 2

# The full config adds WARMUP_STEPS to STEPS_TO_RUN and caps at 8064.
WARMUP_STEPS = 48
STEPS_TO_RUN = min(192 + WARMUP_STEPS, 8064)

OUTPUT_DIR = "RESULTS/SMOKE_TEST"

KNN_NEIGHBORS_OVERRIDE = 1
MIN_DATAPOINTS_FOR_AGGREGATION = 10

MAX_WORKERS_CALIBRATION = 1
MAX_WORKERS_MODELS = 1
MAX_WORKERS_TESTING = 1

