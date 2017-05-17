import pytest
import fixtures
from fixtures import context, ecs_tasks, handlers, create_update_handlers, time, now, cfn_mgr
from fixtures import update_event, delete_event
from fixtures import required_property, invalid_property
from cfn_lambda_handler import CfnLambdaExecutionTimeout

# Test running task is stopped on delete
def test_running_task_is_stopped_on_delete(ecs_tasks, delete_event, context, time):
  response = ecs_tasks.handle_delete(delete_event, context)
  assert not ecs_tasks.task_mgr.client.run_task.called
  assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert ecs_tasks.task_mgr.client.list_tasks.called
  assert ecs_tasks.task_mgr.client.stop_task.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID


# Test task is not run on stack rollback when RunOnRollback is false
def test_no_run_when_run_on_rollback_disabled(ecs_tasks, cfn_mgr, update_event, context, time):
  ecs_tasks.cfn_mgr = cfn_mgr
  update_event['ResourceProperties']['RunOnRollback'] = u'False'
  response = ecs_tasks.handle_update(update_event, context)
  assert cfn_mgr.client.describe_stacks.called
  assert not ecs_tasks.task_mgr.client.run_task.called
  assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID

# Test task is run when UpdateCriteria is met
def test_run_when_update_criteria_met(ecs_tasks, cfn_mgr, update_event, context, time):
  ecs_tasks.cfn_mgr = cfn_mgr
  update_event['ResourceProperties']['UpdateCriteria'] = fixtures.UPDATE_CRITERIA
  update_event['ResourceProperties']['TaskDefinition'] = fixtures.NEW_TASK_DEFINITION_ARN
  response = ecs_tasks.handle_update(update_event, context)
  assert ecs_tasks.task_mgr.client.describe_task_definition.called
  assert ecs_tasks.task_mgr.client.run_task.called
  assert ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID

# Test task is not run when UpdateCriteria is not met
def test_no_run_when_update_criteria_not_met(ecs_tasks, cfn_mgr, update_event, context, time):
  ecs_tasks.cfn_mgr = cfn_mgr
  update_event['ResourceProperties']['UpdateCriteria'] = fixtures.UPDATE_CRITERIA
  response = ecs_tasks.handle_update(update_event, context)
  assert ecs_tasks.task_mgr.client.describe_task_definition.called
  assert not ecs_tasks.task_mgr.client.run_task.called
  assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID

# Test task is not run when RunOnUpdate is false
def test_no_run_when_run_on_update_disabled(ecs_tasks, update_event, context, time):
  update_event['ResourceProperties']['RunOnUpdate'] = u'False'
  response = ecs_tasks.handle_update(update_event, context)
  assert not ecs_tasks.task_mgr.client.run_task.called
  assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID

# Run task
def test_run_task(ecs_tasks, create_update_handlers, context, time):
  handler = getattr(ecs_tasks, create_update_handlers[0])
  event = create_update_handlers[1]
  response = handler(event, context)
  assert ecs_tasks.task_mgr.client.run_task.called
  assert ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID

# Run asychronous task (returns immediately without polling)
def test_run_task_zero_timeout(ecs_tasks, create_update_handlers, context, time):
  handler = getattr(ecs_tasks, create_update_handlers[0])
  event = create_update_handlers[1]
  event['ResourceProperties']['Timeout'] = 0
  response = handler(event, context)
  assert ecs_tasks.task_mgr.client.run_task.called
  assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert not time.sleep.called
  assert response['Status'] == 'SUCCESS'
  assert response['PhysicalResourceId'] == fixtures.PHYSICAL_RESOURCE_ID

# Test for ECS task failure
def test_run_task_failure(ecs_tasks, create_update_handlers, context, time):
  ecs_tasks.task_mgr.client.run_task.return_value = fixtures.TASK_FAILURE
  handler = getattr(ecs_tasks, create_update_handlers[0])
  event = create_update_handlers[1]
  response = handler(event, context)
  assert response['Status'] == 'FAILED'
  assert 'A task failure occurred' in response['Reason']

# Test for ECS task with non-zero containers
def test_run_task_non_zero_exit_code(ecs_tasks, create_update_handlers, context, time):
  ecs_tasks.task_mgr.client.describe_tasks.return_value = fixtures.FAILED_TASK_RESULT
  handler = getattr(ecs_tasks, create_update_handlers[0])
  event = create_update_handlers[1]
  response = handler(event, context)
  assert ecs_tasks.task_mgr.client.run_task.called
  assert ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'FAILED'
  assert 'One or more containers failed with a non-zero exit code' in response['Reason']

# Test for ECS task that does not complete within Lambda execution timeout
def test_run_task_execution_timeout(ecs_tasks, create_update_handlers, context, time):
  context.get_remaining_time_in_millis.return_value = 1000
  handler = getattr(ecs_tasks, create_update_handlers[0])
  event = create_update_handlers[1]
  with pytest.raises(CfnLambdaExecutionTimeout) as e:
    response = handler(event, context)
    assert ecs_tasks.task_mgr.client.run_task.called
    assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert e.value.state['TaskResult'] == fixtures.START_TASK_RESULT

# Test for ECS task that does not complete within absolute task timeout
def test_create_new_task_completion_timeout(ecs_tasks, create_update_handlers, context, time, now):
  # Now returns time in the future past the timeout
  now.return_value += 120
  ecs_tasks.task_mgr.client.describe_tasks.return_value = fixtures.RUNNING_TASK_RESULT
  handler = getattr(ecs_tasks, create_update_handlers[0])
  event = create_update_handlers[1]
  event['ResourceProperties']['Timeout'] = 60
  response = handler(event, context)
  assert ecs_tasks.task_mgr.client.run_task.called
  assert not ecs_tasks.task_mgr.client.describe_tasks.called
  assert response['Status'] == 'FAILED'
  assert 'The task failed to complete with the specified timeout of 60 seconds' in response['Reason']

# Test for missing required properties in custom resource 
def test_missing_property(ecs_tasks, handlers, required_property, context, time):
  handler = getattr(ecs_tasks, handlers[0])
  event = handlers[1]
  del event['ResourceProperties'][required_property]
  response = ecs_tasks.handle_create(event,context)
  assert response['Status'] == 'FAILED'
  assert ecs_tasks.task_mgr.client.run_task.was_not_called
  assert ecs_tasks.task_mgr.client.describe_tasks.was_not_called
  assert 'One or more invalid event properties' in response['Reason']

# Test for invalid properties in custom resource 
def test_invalid_property(ecs_tasks, handlers, invalid_property, context, time):
  handler = getattr(ecs_tasks, handlers[0])
  event = handlers[1]
  event['ResourceProperties'][invalid_property[0]] = invalid_property[1]
  response = handler(event,context)
  assert response['Status'] == 'FAILED'
  assert ecs_tasks.task_mgr.client.run_task.was_not_called
  assert ecs_tasks.task_mgr.client.describe_tasks.was_not_called
  assert 'One or more invalid event properties' in response['Reason']
