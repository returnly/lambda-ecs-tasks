import logging
import json
from ecs import EcsTaskFailureError, EcsTaskExitCodeError, EcsTaskTimeoutError
from voluptuous import MultipleInvalid, Invalid
from cfn_lambda_handler import CfnLambdaExecutionTimeout
from botocore.exceptions import ClientError

log = logging.getLogger()

def ecs_error_handler(func):
  def handle_task_result(event, context):
    try:
      event = func(event, context)
    except ClientError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "A boto3 client error occurred: %s" % e
    except (Invalid, MultipleInvalid) as e:
      event['Status'] = "FAILED"
      event['Reason'] = "One or more invalid event properties: %s" % e
    except EcsTaskFailureError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "A task failure occurred: %s" % e.failures
    except EcsTaskExitCodeError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "One or more containers failed with a non-zero exit code: %s" % e.non_zero
    except EcsTaskTimeoutError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "The task failed to complete with the specified timeout of %s seconds" % e.timeout
    except Exception as e:
      event['Status'] = "FAILED"
      event['Reason'] = "An error occurred: %s" % e
    finally:
      if event['Status'] == "FAILED":
        log.error(event['Reason'])
      return json.loads(json.dumps(event, default=lambda d: d.isoformat() if isinstance(d, datetime) else str(d)))
  return handle_task_result

def cfn_error_handler(func):
  def handle_task_result(event, context):
    try:
      event = func(event, context)
    except EcsTaskFailureError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "A task failure occurred: %s" % e.failures
      event['PhysicalResourceId'] = e.taskArn or event['PhysicalResourceId']
    except EcsTaskExitCodeError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "One or more containers failed with a non-zero exit code: %s" % e.non_zero
      event['PhysicalResourceId'] = e.taskArn or event['PhysicalResourceId']
    except EcsTaskTimeoutError as e:
      event['Status'] = "FAILED"
      event['Reason'] = "The task failed to complete with the specified timeout of %s seconds" % e.timeout
      event['PhysicalResourceId'] = e.taskArn or event['PhysicalResourceId']
    except CfnLambdaExecutionTimeout:
      raise
    except (Invalid, MultipleInvalid) as e:
      event['Status'] = "FAILED"
      event['Reason'] = "One or more invalid event properties: %s" % e  
    if event.get('Status') == "FAILED":
      log.error(event['Reason'])
    return event
  return handle_task_result