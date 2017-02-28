from functools import partial
import boto3

class EcsTaskFailureError(Exception):
    def __init__(self,tasks):
        self.tasks = tasks
        self.failures = tasks.get('failures')

class EcsTaskExitCodeError(Exception):
    def __init__(self,tasks,non_zero):
        self.tasks = tasks
        self.non_zero = non_zero

class EcsTaskManager:
  """Handles ECS Tasks"""
  def __init__(self):
    self.client = boto3.client('ecs')

  def get_container_instances(self, cluster, instance_ids):
    containers = self.client.list_container_instances(cluster).get('containerInstanceArns')
    describe_containers = self.client.describe_container_instances(cluster=cluster, containerInstances=containers).get('containerInstances')
    return [c.get('containerInstanceArn') for c in describe_containers if c.get('ec2InstanceId') in instance_ids]
    
  def list_container_instances(self, cluster):
    func = partial(self.client.list_container_instances,cluster=cluster)
    return self.paginated_response(func, 'containerInstanceArns')

  def start_task(self, cluster, task_definition, overrides, count, started_by, instances):
    if instances:
      return self.client.start_task(
        cluster=cluster, 
        taskDefinition=task_definition, 
        overrides=overrides, 
        containerInstances=instances, 
        startedBy=started_by
      )
    else:
      return self.client.run_task(
        cluster=cluster, 
        taskDefinition=task_definition, 
        overrides=overrides, 
        count=count, 
        startedBy=started_by
      )

  def describe_tasks(self, cluster, tasks):
    return self.client.describe_tasks(cluster=cluster, tasks=tasks)

  def describe_task_definition(self, task_definition):
    response = self.client.describe_task_definition(taskDefinition=task_definition)
    return response['taskDefinition']

  def list_tasks(self, cluster, **kwargs):
    func = partial(self.client.list_tasks,cluster=cluster,**kwargs)
    return self.paginated_response(func, 'taskArns')

  def stop_task(self, cluster, task, reason='unknown'):
    return self.client.stop_task(cluster=cluster, task=task, reason=reason)

  def paginated_response(self, func, result_key, next_token=None):
    '''
    Returns expanded response for paginated operations.
    The 'result_key' is used to define the concatenated results that are combined from each paginated response.
    '''
    args=dict()
    if next_token:
        args['NextToken'] = next_token
    response = func(**args)
    result = response.get(result_key)
    next_token = response.get('NextToken')
    if not next_token:
       return result
    return result + self.paginated_response(func, result_key, next_token)