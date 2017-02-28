from voluptuous import Required, All, Any, Range, Schema, Length

def ToInt(value):
  return int(value)

# Validation Helper
def ToBool(value):
  if value.lower() in ['true','yes']:
    return True
  elif value.lower() in ['false','no']:
    return False
  else:
    raise ValueError

# Validation Helper
def get_validator():
  return Schema({
  Required('Cluster'): Any(str, unicode),
  Required('TaskDefinition'): Any(str, unicode),
  Required('Count', default=1): All(ToInt, Range(min=0, max=10)),
  Required('RunOnUpdate', default=True): All(ToBool),
  Required('UpdateCriteria', default=[]): All([Schema({
    Required('Container'): Any(str, unicode),
    Required('EnvironmentKeys'): All(list)
  })]),
  Required('Timeout', default=290): All(ToInt, Range(min=10)),
  Required('PollInterval', default=10): All(ToInt, Range(min=10, max=60)),
  Required('Overrides', default=dict()): All(dict),
  Required('Instances', default=list()): All(list, Length(max=10)),
}, extra=True)

# Validation Helper
def validate(data):
  request_validator = get_validator()
  return request_validator(data)