import boto3
from typing import Optional


# SSMClient is a class to encapsulate the boto3 SSM client functionality.
class SSMClient:
  def __init__(self, region: str):
    self.client = boto3.client('ssm', region_name=region)

  def get_parameter(self, name: str, with_decryption: bool = True) -> Optional[str]:
    """Fetch a parameter from SSM. Returns None only if the parameter does not exist.

    Raises RuntimeError on any other AWS/network error so that inventory
    generation fails loudly rather than silently producing None values that
    propagate into Ansible as empty strings.
    """
    try:
      response = self.client.get_parameter(Name=name, WithDecryption=with_decryption)
      return response['Parameter']['Value']
    except self.client.exceptions.ParameterNotFound:
      return None
    except Exception as e:
      raise RuntimeError(f"Failed to retrieve SSM parameter '{name}': {e}") from e

  def require_parameter(self, name: str, with_decryption: bool = True) -> str:
    """Fetch a parameter from SSM. Raises ValueError if the parameter does not exist.

    Use this for parameters that must be present for the inventory to be valid.
    """
    value = self.get_parameter(name, with_decryption)
    if value is None:
      raise ValueError(
        f"Required SSM parameter not found: {name}\n"
        f"Run: aws ssm put-parameter --name \"{name}\" --value \"<value>\" --type SecureString"
      )
    return value
