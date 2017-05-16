import logging
import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

from datetime import datetime
from lib import EcsTaskManager, EcsTaskFailureError
from lib import validate_ecs
from lib import ecs_error_handler

# Configure logging
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
log = logging.getLogger()

# ECS Task Manager
task_mgr = EcsTaskManager()

@ecs_error_handler
def handler(event, context):
  log.info('Received event %s' % str(event))
  # Validate event
  event = validate_ecs(event)
  event['CreateTimestamp'] = datetime.utcnow().isoformat() + 'Z'
  # Start task
  result = task_mgr.start_task(
    cluster=event['Cluster'],
    task_definition=event['TaskDefinition'],
    overrides=event['Overrides'],
    count=event['Count'],
    instances=event['Instances'],
    started_by=event['StartedBy']
  )
  event['Tasks'] = result['tasks']
  event['Failures'] = result['failures']
  if event['Failures']:
    raise EcsTaskFailureError(result)
  event['Status'] = task_mgr.check_status(event['Tasks'])
  return event