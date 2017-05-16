import pytest
import datetime
import fixtures
from fixtures import context
from fixtures import check_task
from fixtures import check_task_event
from fixtures import create_task
from fixtures import create_task_event
from dateutil.parser import parse

def test_create_task_created(create_task, create_task_event, context):
  result = create_task.handler(create_task_event, context)
  creation = parse(result['CreateTimestamp'])
  assert create_task.task_mgr.client.run_task.called
  assert result['Status'] == 'PENDING'
  assert creation < parse(datetime.datetime.utcnow().isoformat() + 'Z')

def test_create_task_failure(create_task, create_task_event, context):
  create_task.task_mgr.client.run_task.return_value['failures'] = fixtures.TASK_FAILURE
  result = create_task.handler(create_task_event, context)
  assert create_task.task_mgr.client.run_task.called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('A task failure occurred')

def test_check_task_running(check_task, check_task_event, context):
  result = check_task.handler(check_task_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'RUNNING'

def test_check_task_completed(check_task, check_task_event, context):
  check_task.task_mgr.client.describe_tasks.return_value = fixtures.STOPPED_TASK_RESULT
  result = check_task.handler(check_task_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'STOPPED'

def test_check_task_timeout(check_task, check_task_event, context):
  check_task_event['CreateTimestamp'] = (datetime.datetime.utcnow() - datetime.timedelta(seconds=3600)).isoformat() + 'Z'
  check_task_event['Timeout'] = 1800
  result = check_task.handler(check_task_event, context)
  assert check_task.task_mgr.client.describe_tasks.not_called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('The task failed to complete with the specified timeout')

def test_check_task_exited_non_zero(check_task, check_task_event, context):
  check_task.task_mgr.client.describe_tasks.return_value = fixtures.FAILED_TASK_RESULT
  result = check_task.handler(check_task_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('One or more containers failed with a non-zero exit code')

def test_check_task_failure(check_task, check_task_event, context):
  check_task.task_mgr.client.describe_tasks.return_value['failures'] = fixtures.TASK_FAILURE
  result = check_task.handler(check_task_event, context)
  assert check_task.task_mgr.client.describe_tasks.called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('A task failure occurred')
  