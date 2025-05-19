import boto3
from typing import Optional

# SSMClient is a class to encapsulate the boto3 SSM client functionality.
class SSMClient:
  def __init__(self, region: str):
    self.client = boto3.client('ssm', region_name=region)

  def get_parameter(self, name: str, with_decryption: bool = True) -> Optional[str]:
    try:
      response = self.client.get_parameter(Name=name, WithDecryption=with_decryption)
      return response['Parameter']['Value']
    except self.client.exceptions.ParameterNotFound:
      print(f"Parameter '{name}' not found.")
      return None
    except Exception as e:
      print(f"Failed to retrieve Parameter '{name}': {e}")
      return None

