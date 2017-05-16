import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

import time
import logging
import json
from datetime import datetime
from cfn_lambda_handler import Handler, CfnLambdaExecutionTimeout
from hashlib import md5
from lib import CfnManager
from lib import EcsTaskManager, EcsTaskFailureError, EcsTaskExitCodeError, EcsTaskTimeoutError
from lib import validate_cfn
from lib import cfn_error_handler

# Stack rollback states
ROLLBACK_STATES = ['ROLLBACK_IN_PROGRESS','UPDATE_ROLLBACK_IN_PROGRESS']

# Set handler as the entry point for Lambda
handler = Handler()

# Configure logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)

# AWS services
task_mgr = EcsTaskManager()
cfn_mgr = CfnManager()

# Starts an ECS task
def start(task):
  return task_mgr.start_task(
    cluster=task['Cluster'],
    task_definition=task['TaskDefinition'],
    overrides=task['Overrides'],
    count=task['Count'],
    instances=task['Instances'],
    started_by=task['StartedBy']
  )

# Outputs JSON
def format_json(data):
  return json.dumps(data, default=lambda d: d.isoformat() if isinstance(d, datetime) else str(d))

# Transforms a list of dicts into a keyed dictionary
def to_dict(items, key, value):
  return dict(zip([i[key] for i in items], [i[value] for i in items]))

# Creates a fixed length consist ID based from a given stack ID and resource IC
def get_task_id(stack_id, resource_id):
  m = md5()
  m.update(stack_id + resource_id)
  return m.hexdigest()

# Gets ECS task definition and returns environment variable values for a given set of update criteria
def get_task_definition_values(task_definition_arn, update_criteria):
  task_definition = task_mgr.describe_task_definition(task_definition_arn)
  containers = to_dict(task_definition['containerDefinitions'],'name','environment')
  return [env['value'] for u in update_criteria for env in containers.get(u['Container'],{}) if env['name'] in u['EnvironmentKeys']]

# Updates ECS task status
def describe_tasks(cluster, task_result):
  tasks = task_result['tasks']
  task_arns = [t.get('taskArn') for t in tasks]
  return task_mgr.describe_tasks(cluster=cluster, tasks=task_arns)

# Checks ECS task completion
def check_complete(task_result):
  if task_result.get('failures'):
    raise EcsTaskFailureError(task_result)
  tasks = task_result.get('tasks')
  return all(t.get('lastStatus') == 'STOPPED' for t in tasks)

# Checks ECS task exit codes
def check_exit_codes(task_result):
  tasks = task_result['tasks']
  non_zero = [c.get('taskArn') for t in tasks for c in t.get('containers') if c.get('exitCode') != 0]
  if non_zero:
    raise EcsTaskExitCodeError(tasks, non_zero)

# Polls an ECS task for completion 
def poll(task, remaining_time):
  poll_interval = task['PollInterval'] or 10
  task_result = task['TaskResult']
  while True:
    if task['CreationTime'] + task['Timeout'] < int(time.time()):
      raise EcsTaskTimeoutError(task)
    if remaining_time() < (poll_interval + 5) * 1000:
      task['TaskResult'] = task_result
      raise CfnLambdaExecutionTimeout(task)
    if not check_complete(task_result):
      log.info("Task(s) have not yet completed, checking again in %s seconds..." % poll_interval)
      time.sleep(poll_interval)
      task_result = describe_tasks(task['Cluster'], task_result)
    else:
      check_exit_codes(task_result)
      return task_result

# Start and poll task
def start_and_poll(task, context):
  task['TaskResult'] = start(task)
  log.info("Task created successfully with result: %s" % format_json(task['TaskResult']))
  if task['Timeout'] > 0:
    task['TaskResult'] = poll(task,context.get_remaining_time_in_millis)
    log.info("Task completed successfully with result: %s" % format_json(task['TaskResult']))
  return next(t['taskArn'] for t in task['TaskResult']['tasks'])

# Create task
def create_task(event):
  task = validate_cfn(event['ResourceProperties'])
  task['StartedBy'] = get_task_id(event['StackId'],event['LogicalResourceId'])
  event['Timeout'] = task['Timeout']
  task['CreationTime'] = event['CreationTime']
  log.info('Received task %s' % format_json(task))
  return task

# Event handlers
@handler.poll
@cfn_error_handler
def handle_poll(event, context):
  log.info('Received poll event %s' % str(event))
  task = event.get('EventState')
  task['TaskResult'] = poll(task, event, context)
  log.info("Task completed with result: %s" % task['TaskResult'])
  return {"Status": "SUCCESS", "PhysicalResourceId": task['StartedBy']}

@handler.create
@cfn_error_handler
def handle_create(event, context):
  log.info('Received create event %s' % str(event))
  task = create_task(event)
  if task['Count'] > 0:
    event['PhysicalResourceId'] = start_and_poll(task, context)
  return event

@handler.update
@cfn_error_handler
def handle_update(event, context):
  log.info('Received update event %s' % str(event))
  task = create_task(event)
  update_criteria = task['UpdateCriteria']
  should_run = task['RunOnUpdate'] and task['Count'] > 0
  if should_run:
    old_task = validate_cfn(event.get('OldResourceProperties'))
    if not task['RunOnRollback']:
      stack_status = cfn_mgr.get_stack_status(event['StackId'])
      should_run = stack_status not in ROLLBACK_STATES
    if update_criteria and should_run:
      old_values = get_task_definition_values(old_task['TaskDefinition'],update_criteria)
      new_values = get_task_definition_values(task['TaskDefinition'],update_criteria)
      if old_values != new_values:
        event['PhysicalResourceId'] = start_and_poll(task, context)
    elif should_run:
      event['PhysicalResourceId'] = start_and_poll(task, context)
  return event
  
@handler.delete
@cfn_error_handler
def handle_delete(event, context):
  log.info('Received delete event %s' % str(event))
  task = create_task(event)
  tasks = task_mgr.list_tasks(cluster=task['Cluster'], startedBy=task['StartedBy'])
  for t in tasks:
    service_mgr.stop_task(cluster=task['Cluster'], task=t, reason='Delete requested for %s' % event['StackId'])
  return event