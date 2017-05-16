import pytest
import mock
import time
import copy
from datetime import datetime
from uuid import uuid4
from lib import EcsTaskManager

AWS_ACCOUNT_ID = 123456789012
AWS_REGION = 'us-west-2'
REQUEST_ID = str(uuid4())
FUNCTION_NAME = 'ecsTasks'
FUNCTION_ARN = 'arn:aws:lambda:%s:%s:function:%s' % (AWS_REGION, AWS_ACCOUNT_ID, FUNCTION_NAME)
CLUSTER_NAME = 'my-stack-ApplicationCluster-1OGPYPX0NHOMI'
TASK_DEFINITION_ARN = 'arn:aws:ecs:%s:%s:task-definition/my-stack-AdhocTaskDefinition-1JA1NYYDAXINC:1' % (AWS_REGION, AWS_ACCOUNT_ID)
MEMORY_LIMIT = '128'
UTC = datetime.utcnow()
NOW = round(time.time(),3)
START_TASK_RESULT = {
  u'tasks': [{
    u'taskArn': 'arn:aws:ecs:%s:%s:task/96052dc0-a646-4068-86d5-4c947b9a88b5' % (AWS_REGION, AWS_ACCOUNT_ID),
    u'group': 'family:my-stack-ApplicationTaskDefinition-4HW2MC4Z0DWO',
    u'overrides': {u'containerOverrides': [{u'name': 'app'}]},
    u'lastStatus': 'PENDING',
    u'containerInstanceArn': 'arn:aws:ecs:%s:%s:container-instance/7de72b16-8e6d-4a22-9317-8c74f15d3382' % (AWS_REGION, AWS_ACCOUNT_ID),
    u'createdAt': NOW,
    u'version': 1,
    u'clusterArn': 'arn:aws:ecs:%s:%s:cluster/%s' % (AWS_REGION, AWS_ACCOUNT_ID, CLUSTER_NAME),
    u'desiredStatus': 'RUNNING',
    u'taskDefinitionArn': TASK_DEFINITION_ARN,
    u'containers': [
      {
        u'containerArn': 'arn:aws:ecs:%s:%s:container/93e604ca-7291-4573-beaa-59a4b439fdc3' % (AWS_REGION, AWS_ACCOUNT_ID),
        u'taskArn': 'arn:aws:ecs:%s:%s:task/96052dc0-a646-4068-86d5-4c947b9a88b5' % (AWS_REGION, AWS_ACCOUNT_ID),
        u'lastStatus': 'PENDING',
        u'name': 'app'
      }
    ]
  }],
  'failures': []
}
RUNNING_TASK_RESULT = copy.deepcopy(START_TASK_RESULT)
RUNNING_TASK_RESULT['tasks'][0]['lastStatus'] = 'RUNNING'
RUNNING_TASK_RESULT['tasks'][0]['startedAt'] = RUNNING_TASK_RESULT['tasks'][0]['createdAt'] + 2
RUNNING_TASK_RESULT['tasks'][0]['containers'][0]['lastStatus'] = 'RUNNING'
RUNNING_TASK_RESULT['tasks'][0]['containers'][0]['networkBindings'] = []
STOPPED_TASK_RESULT = copy.deepcopy(RUNNING_TASK_RESULT)
STOPPED_TASK_RESULT['tasks'][0]['lastStatus'] = 'STOPPED'
STOPPED_TASK_RESULT['tasks'][0]['desiredStatus'] = 'STOPPED'
STOPPED_TASK_RESULT['tasks'][0]['stoppedReason'] = 'Container exited'
STOPPED_TASK_RESULT['tasks'][0]['containers'][0]['lastStatus'] = 'STOPPED'
STOPPED_TASK_RESULT['tasks'][0]['containers'][0]['exitCode'] = 0
FAILED_TASK_RESULT = copy.deepcopy(STOPPED_TASK_RESULT)
FAILED_TASK_RESULT['tasks'][0]['containers'][0]['exitCode'] = 1
TASK_FAILURE= [
  {
    "reason": "RESOURCE:MEMORY",
    "arn": "arn:aws:ecs:%s:%s:container-instance/7de72b16-8e6d-4a22-9317-8c74f15d3382" % (AWS_REGION, AWS_ACCOUNT_ID)
  }
]

class LambdaContext:
  def __init__(self):
    self.aws_request_id = REQUEST_ID
    self.invoked_function_arn = FUNCTION_ARN
    self.client_context = None
    self.identity = None
    self.function_name = FUNCTION_NAME
    self.function_version = u'$LATEST'
    self.memory_limit_in_mb = MEMORY_LIMIT

@pytest.fixture
def context():
  return LambdaContext()

@pytest.fixture(scope="function")
def create_task():
  with mock.patch('boto3.client') as client:
    import create_task
    client.run_task.return_value = START_TASK_RESULT
    task_mgr = EcsTaskManager()
    task_mgr.client = client
    create_task.task_mgr = task_mgr
    yield create_task

@pytest.fixture(scope="function")
def check_task():
  with mock.patch('boto3.client') as client:
    import check_task
    client.describe_tasks.return_value = RUNNING_TASK_RESULT
    task_mgr = EcsTaskManager()
    task_mgr.client = client
    check_task.task_mgr = task_mgr
    yield check_task

@pytest.fixture
def create_event():
  return {
    u'Cluster': unicode(CLUSTER_NAME),
    u'TaskDefinition': unicode(TASK_DEFINITION_ARN),
    u'Count': 1
  }

@pytest.fixture
def check_event():
  return {
    u'Cluster': unicode(CLUSTER_NAME),
    u'TaskDefinition': unicode(TASK_DEFINITION_ARN),
    u'Count': 1,
    u'Status': 'PENDING',
    u'Tasks': START_TASK_RESULT['tasks'],
    u'Failures': [],
    u'CreateTimestamp': UTC.isoformat() + 'Z',
    u'Timeout': 60
  }