import datetime
import os
from pathlib import Path

import grid2op
from grid2op.Action import BaseAction, PowerlineSetAction
from grid2op.Environment import Environment
from grid2op.Opponent import BaseActionBudget, RandomLineOpponent
from lightsim2grid import LightSimBackend

import config
from curriculumagent.baseline.baseline import CurriculumAgent
from utils.global_utils import resolve_config_path


_REPORTED_GRID2OP_DATA: set[str] = set()


def _get_grid2op_data_paths() -> list[Path]:
    data_paths = []
    for env_var in ("GRID2OP_DATA_PATH", "GRID2OP_DATA"):
        env_value = os.environ.get(env_var)
        if env_value:
            data_paths.append(Path(env_value).expanduser())

    data_paths.extend(
        [
            Path("~/data_grid2op").expanduser(),
            Path("~/.grid2op/data").expanduser(),
        ]
    )

    return data_paths


def _report_grid2op_data_status(env_name: str) -> None:
    if env_name in _REPORTED_GRID2OP_DATA:
        return

    _REPORTED_GRID2OP_DATA.add(env_name)
    data_paths = _get_grid2op_data_paths()
    env_paths = [data_path / env_name for data_path in data_paths]

    for env_path in env_paths:
        if env_path.exists():
            print(f"Grid2Op data found for {env_name}; using existing local data.")
            return

    searched_paths = ", ".join(str(path) for path in env_paths)
    print(f"Grid2Op data for {env_name} was not found locally; Grid2Op may download it now.")
    print(f"Checked Grid2Op data paths: {searched_paths}")


# NOTE: When creating with another agent/forecasting model
# this function needs to be changed so that the right initialization
# is done
def create_environment(
    env_seed: int,
    lines_attacked: list[str],
) -> tuple[Environment, CurriculumAgent]:
    """
    Creates and configures a Grid2Op simulation environment with agent and prediction model

    Args:
        env_seed: Integer random seed for reproducible simulations
        lines_attacked: list of power line names for opponent attacks

    Returns:
        Tuple of (Grid2Op environment, CurriculumAgent, HBGB prediciton model)
    """

    print(f"Initializing Grid2Op environment: {config.ENV_NAME} with seed {env_seed}")
    _report_grid2op_data_status(config.ENV_NAME)

    if not lines_attacked:
        env = grid2op.make(
            config.ENV_NAME,
            backend=LightSimBackend(),
        )
    else:
        print(f"Lines attacked: {lines_attacked}")
        env = grid2op.make(
            config.ENV_NAME,
            opponent_attack_cooldown=config.OPPONENT_ATTACK_COOLDOWN,
            opponent_attack_duration=config.OPPONENT_ATTACK_DURATION,
            opponent_budget_per_ts=config.OPPONENT_BUDGET_PER_TS,
            opponent_init_budget=config.OPPONENT_INIT_BUDGET,
            opponent_action_class=PowerlineSetAction,
            opponent_class=RandomLineOpponent,
            opponent_budget_class=BaseActionBudget,
            kwargs_opponent={"lines_attacked": lines_attacked},
            backend=LightSimBackend(),
        )
    env.seed(env_seed)

    agent = CurriculumAgent(
        action_space=env.action_space,
        observation_space=env.observation_space,
        name=config.AGENT_NAME,
    )
    agent.load(resolve_config_path(config.MODEL_PATH))

    return env, agent


def is_action_empty(action: BaseAction, env: Environment) -> bool:
    """
    Checks if an agent action represents a "do nothing" operation

    Args:
        action: Grid2Op action object from agent.act()
        env: Grid2Op environment object

    Returns:
        Boolean indicating if action is equivalent to doing nothing
    """
    empty_action = env.action_space({})
    if action == empty_action:
        return True
    return False


def get_warmup_cutoff_time(
    start_time: datetime.datetime,
    warmup_steps: int,
) -> datetime.datetime:
    """
    Calculates the cutoff time after which calibration data collection begins

    Args:
        start_time: Simulation start time as string or datetime object
        warmup_steps: Optional number of 5-minute timesteps to skip

    Returns:
        Datetime object marking the end of warmup period
    """
    return start_time + datetime.timedelta(minutes=warmup_steps * 5)


def needs_new_forecast(
    current_datetime: datetime.datetime,
    last_forecast_time: datetime.datetime | None,
    expected_forecast_times: set[datetime.datetime],
) -> bool:
    """
    Determines if a new forecast trajectory should be generated

    Args:
        current_datetime: Current simulation timestamp (datetime)
        last_forecast_time: Timestamp (datetime) when last forecast was generated, or None
        expected_forecast_times: Set of timestamps for which forecasts exist

    Returns:
        Boolean indicating if a new forecast is needed
    """
    return (
        last_forecast_time is None
        or current_datetime == last_forecast_time
        or len(expected_forecast_times) == 0
    )
