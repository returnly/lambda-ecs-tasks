import time
import logging
import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

from cfn_lambda_handler import Handler, CfnLambdaExecutionTimeout
from hashlib import md5
from lib import EcsTaskManager, EcsTaskFailureError, EcsTaskExitCodeError
from lib import get_validator, validate
from voluptuous import MultipleInvalid, Invalid

# Set handler as the entry point for Lambda
handler = Handler()

# Configure logging
log = logging.getLogger()
log.setLevel(logging.INFO)

# ECS Task Manager
task_mgr = EcsTaskManager()

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
def poll(task, event, context):
  poll_interval = task['PollInterval'] or 10
  poll_count = task['Timeout'] / poll_interval + 1
  counter = 0
  log.info("Checking if task(s) have completed...")
  while counter < poll_count:
    if context.get_remaining_time_in_millis() < (poll_interval + 10) * 1000:
      event['EventState'] = task
      raise CfnLambdaExecutionTimeout()
    complete = check_complete(task['TaskResult'])
    if complete:
      check_exit_codes(task['TaskResult'])
      return task['TaskResult']
    else:
      log.info("Task(s) have not yet completed, checking again in %s seconds..." % poll_interval)
      time.sleep(poll_interval)
      tasks = task['TaskResult']['tasks']
      task_arns = [t.get('taskArn') for t in tasks]
      task['TaskResult'] = task_mgr.describe_tasks(cluster=task['Cluster'], tasks=task_arns)
  raise Exception("The tasks did not complete in the specified timeout of %s seconds", task['Timeout'])

# Starts and ECS task and polls for the task result
def start_and_poll(task, event, context):
  task['TaskResult'] = start(task)
  task['TaskResult'] = poll(task, event, context)
  log.info("Task completed with result: %s" % task['TaskResult'])

# Creates a task object from event data
def create_task(event, context):
  task = validate(event.get('ResourceProperties'))
  event['Timeout'] = event.get('Timeout') or task['Timeout']
  task['StartedBy'] = get_task_id(event.get('StackId'), event.get('LogicalResourceId'))
  log.info('Received task %s' % str(task))
  return task

# Exception handler  
def task_result_handler(func):
  def handle_task_result(event, context):
    try:
      return func(event, context)
    except EcsTaskFailureError as e:
      return {"Status": "FAILED", "Reason": "A task failure occurred: %s" % e.failures}
    except EcsTaskExitCodeError as e:
      return {"Status": "FAILED", "Reason": "One or more containers failed with a non-zero exit code: %s" % e.non_zero}
    except (Invalid, MultipleInvalid) as e:
      return {"Status": "FAILED", "Reason": "One or more invalid properties: %s" % e}
  return handle_task_result

# Event handlers
@handler.poll
@task_result_handler
def handle_poll(event, context):
  log.info('Received poll event %s' % str(event))
  task = event.get('EventState')
  task['TaskResult'] = poll(task, event, context)
  log.info("Task completed with result: %s" % task['TaskResult'])
  return {"Status": "SUCCESS", "PhysicalResourceId": task['StartedBy']}

@handler.create
@task_result_handler
def handle_create(event, context):
  log.info('Received create event %s' % str(event))
  task = create_task(event, context)
  if task['Count'] > 0:
    start_and_poll(task, event, context)
  return {"Status": "SUCCESS", "PhysicalResourceId": task['StartedBy']}

@handler.update
@task_result_handler
def handle_update(event, context):
  log.info('Received update event %s' % str(event))
  task = create_task(event, context)
  update_criteria = task['UpdateCriteria']
  if task['RunOnUpdate'] and task['Count'] > 0:
    old_task = validate(event.get('OldResourceProperties'))
    if update_criteria:
      old_values = get_task_definition_values(old_task['TaskDefinition'],task['UpdateCriteria'])
      new_values = get_task_definition_values(task['TaskDefinition'],task['UpdateCriteria'])
      if old_values != new_values:
        start_and_poll(task, event, context)
    else:
      start_and_poll(task, event, context)
  return {"Status": "SUCCESS", "PhysicalResourceId": task['StartedBy']}
  
@handler.delete
@task_result_handler
def handle_delete(event, context):
  log.info('Received delete event %s' % str(event))
  task = validate(event.get('ResourceProperties'))
  task_id = get_task_id(event.get('StackId'), event.get('LogicalResourceId'))
  tasks = task_mgr.list_tasks(cluster=task['Cluster'], startedBy=task_id)
  for t in tasks:
    service_mgr.stop_task(cluster=task['Cluster'], task=t, reason='Delete requested for %s' % event.get('StackId'))
  return {"Status": "SUCCESS"}