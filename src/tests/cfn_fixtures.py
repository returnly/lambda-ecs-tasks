import pytest
import time
import copy
import mock
import datetime
from dateutil.tz import tzutc
from uuid import uuid4
from lib import EcsTaskManager, CfnManager

AWS_ACCOUNT_ID = 123456789012
AWS_REGION = 'us-west-2'
STACK_NAME = 'my-stack'
REQUEST_ID = str(uuid4())
RESOURCE_TYPE = 'Custom::LogGroup'
FUNCTION_NAME = 'cfnEcsTasks'
FUNCTION_ARN = 'arn:aws:lambda:%s:%s:function:%s-%s' % (AWS_REGION, AWS_ACCOUNT_ID, STACK_NAME, FUNCTION_NAME)
CLUSTER_NAME = 'my-stack-ApplicationCluster'
OLD_TASK_DEFINITION_ARN = u'arn:aws:ecs:%s:%s:task-definition/my-stack-AdhocTaskDefinition:1' % (AWS_REGION, AWS_ACCOUNT_ID)
NEW_TASK_DEFINITION_ARN = u'arn:aws:ecs:%s:%s:task-definition/my-stack-AdhocTaskDefinition:2' % (AWS_REGION, AWS_ACCOUNT_ID)
MEMORY_LIMIT = '128'
STACK_ID = 'arn:aws:cloudformation:%s:%s:stack/%s/%s' % (AWS_REGION, AWS_ACCOUNT_ID, STACK_NAME, str(uuid4()))
LOGICAL_RESOURCE_ID = 'MyEcsTask'
PHYSICAL_RESOURCE_ID = 'arn:aws:ecs:%s:%s:task/96052dc0-a646-4068-86d5-4c947b9a88b5' % (AWS_REGION, AWS_ACCOUNT_ID)
OLD_DB_HOST = u'my-old-app-db.example.org'
NEW_DB_HOST = u'my-new-app-db.example.org'
UTC = datetime.datetime.utcnow()
NOW = int(time.time())
UPDATE_CRITERIA = [{'Container': 'app', 'EnvironmentKeys':['DB_HOST']}]
OLD_TASK_DEFINITION_RESULT = {
  u'taskDefinition': {
    u'status': u'ACTIVE',
    u'family': u'my-stack-AdhocTaskDefinition', 
    u'containerDefinitions': [{
      u'memoryReservation': 100, 
      u'name': u'app', 
      u'command': [], 
      u'image': u'%s.dkr.ecr.%s.amazonaws.com/org/my-app:latest' % (AWS_ACCOUNT_ID,AWS_REGION), 
      u'cpu': 0, 
      u'environment': [
        { u'name': u'DB_HOST', u'value': OLD_DB_HOST }
      ], 
      u'essential': True, 
    }], 
    u'volumes': [], 
    u'taskDefinitionArn': OLD_TASK_DEFINITION_ARN, 
    u'revision': 1
  }, 
  u'ResponseMetadata': {}
}
NEW_TASK_DEFINITION_RESULT = copy.deepcopy(OLD_TASK_DEFINITION_RESULT)
NEW_TASK_DEFINITION_RESULT['taskDefinition']['containerDefinitions'][0]['environment'][0]['value'] = NEW_DB_HOST
NEW_TASK_DEFINITION_RESULT['taskDefinition']['taskDefinitionArn'] = NEW_TASK_DEFINITION_ARN
TASK_DEFINITION_RESULTS={
  OLD_TASK_DEFINITION_ARN: OLD_TASK_DEFINITION_RESULT,
  NEW_TASK_DEFINITION_ARN: NEW_TASK_DEFINITION_RESULT
}

START_TASK_RESULT = {
  u'tasks': [{
    u'taskArn': PHYSICAL_RESOURCE_ID,
    u'group': 'family:my-stack-ApplicationTaskDefinition',
    u'overrides': {u'containerOverrides': [{u'name': 'app'}]},
    u'lastStatus': 'PENDING',
    u'containerInstanceArn': 'arn:aws:ecs:%s:%s:container-instance/7de72b16-8e6d-4a22-9317-8c74f15d3382' % (AWS_REGION, AWS_ACCOUNT_ID),
    u'createdAt': NOW,
    u'version': 1,
    u'clusterArn': 'arn:aws:ecs:%s:%s:cluster/%s' % (AWS_REGION, AWS_ACCOUNT_ID, CLUSTER_NAME),
    u'desiredStatus': 'RUNNING',
    u'taskDefinitionArn': OLD_TASK_DEFINITION_ARN,
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
TASK_FAILURE= {
  'tasks': [],
  'failures' : [{
      "reason": "RESOURCE:MEMORY",
      "arn": "arn:aws:ecs:%s:%s:container-instance/7de72b16-8e6d-4a22-9317-8c74f15d3382" % (AWS_REGION, AWS_ACCOUNT_ID)
    }]
  }

DESCRIBE_STACKS_RESULT = {
  'Stacks': [{
    'StackId': STACK_ID, 
    'Description': STACK_NAME, 
    'Tags': [], 
    'CreationTime': datetime.datetime(2016, 12, 7, 11, 11, 56, 940000, tzinfo=tzutc()), 
    'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'], 
    'StackName': STACK_NAME, 
    'NotificationARNs': [], 
    'StackStatus': 'UPDATE_COMPLETE', 
    'DisableRollback': False, 
    'LastUpdatedTime': datetime.datetime(2017, 3, 17, 22, 8, 34, 728000, tzinfo=tzutc())
  }]
}

@pytest.fixture
def context():
  context = mock.Mock()
  context.aws_request_id = REQUEST_ID
  context.invoked_function_arn = FUNCTION_ARN
  context.client_context = None
  context.identity = None
  context.function_name = FUNCTION_NAME
  context.function_version = u'$LATEST'
  context.memory_limit_in_mb = MEMORY_LIMIT
  context.get_remaining_time_in_millis.return_value = 300000
  yield context

@pytest.fixture
def time():
  with mock.patch('time.sleep', return_value=None) as time:
    yield time

@pytest.fixture
def now(time):
  with mock.patch('time.time', return_value=NOW) as now:
    yield now

@pytest.fixture
def task_mgr():
  with mock.patch('boto3.client') as client:
    client.run_task.return_value = START_TASK_RESULT
    client.describe_tasks.return_value = STOPPED_TASK_RESULT
    client.describe_task_definition.side_effect = lambda taskDefinition: TASK_DEFINITION_RESULTS[taskDefinition]
    task_mgr = EcsTaskManager()
    task_mgr.client = client
    yield task_mgr

@pytest.fixture
def cfn_mgr():
  with mock.patch('boto3.client') as client:
    cfn_mgr = CfnManager()
    client.describe_stacks.side_effect = lambda StackName: DESCRIBE_STACKS_RESULT
    cfn_mgr.client = client
    yield cfn_mgr

@pytest.fixture
def ecs_tasks():
  with mock.patch('boto3.client') as client:
    import ecs_tasks
    client.run_task.return_value = START_TASK_RESULT
    client.describe_tasks.return_value = STOPPED_TASK_RESULT
    client.describe_task_definition.side_effect = lambda taskDefinition: TASK_DEFINITION_RESULTS[taskDefinition]
    task_mgr = EcsTaskManager()
    task_mgr.client = client
    ecs_tasks.task_mgr = task_mgr
    yield ecs_tasks

@pytest.fixture
def create_event():
  return {
    u'StackId': unicode(STACK_ID),
    u'ResponseURL': u'https://cloudformation-custom-resource-response-uswest2.s3-us-west-2.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-west-2%3A429614120872%3Astack/intake-accelerator-dev/12947b30-d31a-11e6-93df-503acbd4dc61%7CMyLogGroup%7C720958cb-c5b7-4225-b12f-e7c5ab6c499b?AWSAccessKeyId=AKIAI4KYMPPRGIACET5Q&Expires=1483789136&Signature=GoZZ7Leg5xRsKq1hjU%2FO81oeJmw%3D',
    u'ResourceProperties': {
      u'ServiceToken': unicode(FUNCTION_ARN),
      u'Cluster': CLUSTER_NAME,
      u'TaskDefinition': OLD_TASK_DEFINITION_ARN
    },
    u'ResourceType': unicode(RESOURCE_TYPE),
    u'RequestType': u'Create',
    'CreationTime': NOW,
    u'ServiceToken': unicode(FUNCTION_ARN),
    u'RequestId': unicode(REQUEST_ID),
    u'LogicalResourceId': unicode(LOGICAL_RESOURCE_ID)
  }

@pytest.fixture
def update_event():
  event = create_event()
  event[u'RequestType'] = u'Update'
  event[u'PhysicalResourceId'] = unicode(PHYSICAL_RESOURCE_ID)
  event[u'OldResourceProperties'] = {
    u'Destroy': u'false', 
    u'ServiceToken': unicode(FUNCTION_ARN),
    u'Cluster': unicode(CLUSTER_NAME),
    u'TaskDefinition': OLD_TASK_DEFINITION_ARN
  }
  return event

@pytest.fixture
def delete_event():
  event = create_event()
  event[u'RequestType'] = u'Delete'
  event[u'PhysicalResourceId'] = unicode(PHYSICAL_RESOURCE_ID)
  return event

# Generates each handler with corresponding event
@pytest.fixture(
  ids=['Create','Update','Delete'],
  params=[
    ('handle_create',create_event),
    ('handle_update',update_event),
    ('handle_delete',delete_event)
  ]
)
def handlers(request):
  yield(request.param[0],request.param[1]())

# Generates Create and Update handlers with corresponding event
@pytest.fixture(
  ids=['Create','Update'],
  params=[
    ('handle_create',create_event),
    ('handle_update',update_event)
  ]
)
def create_update_handlers(request):
  yield(request.param[0],request.param[1]())

# Check validation of required properties for different request types
@pytest.fixture(params = ['Cluster','TaskDefinition'])
def required_property(request):
  yield request.param
  
# Check validation of illegal property values for different request types
@pytest.fixture(
  ids = [
    'Count','RunOnUpdate','RunOnRollback','Timeout','PollInterval','Instances','Overrides'
  ], 
  params=[
    ('Count','50'),               # Maximum count = 10
    ('RunOnUpdate','never'),      # RunOnUpdate is a boolean
    ('RunOnRollback', 'always'),  # RunOnRollback is a boolean
    ('Timeout','4000'),           # Maximum timeout = 4000
    ('PollInterval','300'),       # Maximum poll interval = 60
    ('Instances',range(0,11)),    # Maximum number of instances = 10
    ('Overrides',[])              # Overrides is of type dict
  ])
def invalid_property(request):
  yield request.param