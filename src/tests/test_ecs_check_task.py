import pytest
import datetime
import ecs_fixtures
from ecs_fixtures import context
from ecs_fixtures import check_task
from ecs_fixtures import check_event

def test_check_task_running(check_task, check_event, context):
  result = check_task.handler(check_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'RUNNING'

def test_check_task_completed(check_task, check_event, context):
  check_task.task_mgr.client.describe_tasks.return_value = ecs_fixtures.STOPPED_TASK_RESULT
  result = check_task.handler(check_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'STOPPED'

def test_check_task_timeout(check_task, check_event, context):
  check_event['CreateTimestamp'] = (datetime.datetime.utcnow() - datetime.timedelta(seconds=3600)).isoformat() + 'Z'
  check_event['Timeout'] = 1800
  result = check_task.handler(check_event, context)
  assert check_task.task_mgr.client.describe_tasks.not_called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('The task failed to complete with the specified timeout')

def test_check_task_exited_non_zero(check_task, check_event, context):
  check_task.task_mgr.client.describe_tasks.return_value = ecs_fixtures.FAILED_TASK_RESULT
  result = check_task.handler(check_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('One or more containers failed with a non-zero exit code')

def test_check_task_failure(check_task, check_event, context):
  check_task.task_mgr.client.describe_tasks.return_value['failures'] = ecs_fixtures.TASK_FAILURE
  result = check_task.handler(check_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('A task failure occurred')
  