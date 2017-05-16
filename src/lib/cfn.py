from functools import partial
from .utils import paginated_response
import boto3

class CfnManager:
  """Handles CloudFormation Service Requests""" 
  def __init__(self):
    self.client = boto3.client('cloudformation')

  def describe_stacks(self, stack_name):
    func = partial(self.client.describe_stacks,StackName=stack_name)
    return paginated_response(func, 'Stacks')

  def get_stack_status(self, stack_name):
    # return self.describe_stacks(stack_name)
    return next(s for s in self.describe_stacks(stack_name))['StackStatus']