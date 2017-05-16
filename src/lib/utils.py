def paginated_response(func, result_key, next_token=None):
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
  return result + paginated_response(func, result_key, next_token)
  