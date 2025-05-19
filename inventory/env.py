import os
from typing import Callable, Optional

# read_env_var reads an environment variable, defaults to a specified value if
# not found, validates the value, and casts it to the required type.
def read_env_var(name: str, default_value: Optional[str] = None, required: bool = False, value_type: Callable = str) -> Optional[str]:
  value = os.environ.get(name, default_value)

  # Check if the required env var is missing.
  if required and value is None:
      raise ValueError(f"Environment variable '{name}' is required but not set.")

  # If the value exists, try casting it to the specific type.
  if value is not None:
      try:
        return value_type(value)
      except ValueError:
        raise ValueError(f"Environment variable '{name}' must be of type {value_type.__name__}.")

  return value

