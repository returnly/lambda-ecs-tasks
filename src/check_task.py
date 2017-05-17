import datetime
import logging
import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

from dateutil.parser import parse
from lib import EcsTaskManager, EcsTaskFailureError, EcsTaskExitCodeError, EcsTaskTimeoutError
from lib import validate_ecs
from lib import ecs_error_handler

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ECS Task Manager
task_mgr = EcsTaskManager()

# Checks if timeout has exceeded
def check_timeout(event):
  now = parse(datetime.datetime.utcnow().isoformat() + 'Z')
  creation = parse(event['CreateTimestamp'])
  if now > creation + datetime.timedelta(seconds=event['Timeout']):
    raise EcsTaskTimeoutError(event)

# Checks ECS task exit codes
def check_exit_codes(tasks):
  non_zero = [c.get('taskArn') for t in tasks for c in t.get('containers') if c.get('exitCode') != 0]
  if non_zero:
    raise EcsTaskExitCodeError(tasks, non_zero)

@ecs_error_handler
def handler(event, context):
  log.info('Received event %s' % str(event))
  # Validate event and create task
  event = validate_ecs(event)
  check_timeout(event)
  # Query task status
  task_arns = [t.get('taskArn') for t in event['Tasks']]
  result = task_mgr.describe_tasks(cluster=event['Cluster'], tasks=task_arns)
  event['Tasks'] = result['tasks']
  event['Failures'] = result['failures']
  if event['Failures']:
    raise EcsTaskFailureError(result)
  # Check if task is complete
  event['Status'] = task_mgr.check_status(event['Tasks'])
  if event['Status'] == 'STOPPED':
    check_exit_codes(event['Tasks'])
  return event