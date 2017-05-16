from dateutil.parser import parse
import datetime
import pytest
import ecs_fixtures
from ecs_fixtures import context
from ecs_fixtures import create_task
from ecs_fixtures import create_event

def test_create_task_created(create_task, create_event, context):
  result = create_task.handler(create_event, context)
  creation = parse(result['CreateTimestamp'])
  assert create_task.task_mgr.client.run_task.called
  assert result['Status'] == 'PENDING'
  assert creation < parse(datetime.datetime.utcnow().isoformat() + 'Z')

def test_create_task_failure(create_task, create_event, context):
  create_task.task_mgr.client.run_task.return_value['failures'] = ecs_fixtures.TASK_FAILURE
  result = create_task.handler(create_event, context)
  assert create_task.task_mgr.client.run_task.called
  assert result['Status'] == 'FAILED'
  assert result['Reason'].startswith('A task failure occurred')
