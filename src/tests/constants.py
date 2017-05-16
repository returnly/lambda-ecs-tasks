import copy
import time
import datetime
from dateutil.tz import tzutc
from uuid import uuid4

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
    'StackStatus': 'ROLLBACK_IN_PROGRESS', 
    'DisableRollback': False, 
    'LastUpdatedTime': datetime.datetime(2017, 3, 17, 22, 8, 34, 728000, tzinfo=tzutc())
  }]
}