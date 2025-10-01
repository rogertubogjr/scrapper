"""Helpers for invoking agent runners within the property module."""

import json
import re
from typing import Any

from agents import Runner


async def run_agent_action(input_data: Any, agent: Any, session=None, return_final_output: bool = False):
  result = await Runner.run(
    agent,
    input_data,
    session=session,
  )
  if return_final_output:
    return result.final_output
  try:
    action = re.sub(r"```(?:json)?|```", "", result.final_output).strip()
    return json.loads(action)
  except Exception as exc:
    print("Invalid JSON:", action, exc)
    raise ValueError("Error occur on running agent")
