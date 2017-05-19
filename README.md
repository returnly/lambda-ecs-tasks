# CloudFormation ECS Tasks Function

This repository defines the Lamdba function `ecsTasks`.

This function includes the following modules:

- [`ecs_tasks`](src/ecs_tasks.py) - CloudFormation custom resource that runs ECS tasks and polls the task until successful completion or failure.
- [`create_task`](src/create_task.py) - function intended to be used in a Step Function for creating (running) a task
- [`check_task`](src/check_task.py) - function intended to be used in a Step Function for checking the status of a task

When creating a Lambda function, you need to specify the correct module and correct handler (entrypoint) as follows:

- [`ecs_tasks`](src/ecs_tasks.py) - specify `ecs_tasks.handler` as the handler
- [`create_task`](src/create_task.py) - specify `create_task.handler` as the handler
- [`check_task`](src/check_task.py) - specify `check_task.handler` as the handler

## Build Instructions

Any dependencies need to defined in `src/requirements.txt`.  Note that you do not need to include `boto3`, as this is provided by AWS for Python Lambda functions.

To build the function and its dependencies:

`make build`

This will create a local Docker build environment, run tests and output a ZIP package in the `build` folder.  This file is suitable for upload to the AWS Lambda service to create a Lambda function.

```
$ make build
=> Creating lambda build...
Building lambda
Step 1/13 : FROM amazonlinux
latest: Pulling from library/amazonlinux
Digest: sha256:7c781c9234e712f135ee402a13ffd5dbf342a9ff1394c73bc5ae4d9b9078e0f8
Status: Image is up to date for amazonlinux:latest
 ---> 766ebb052d4f
...
...
Step 13/13 : CMD pytest -vv --junitxml report.xml
 ---> Running in f55ab3846db1
 ---> 474d3457c67a
Removing intermediate container f55ab3846db1
Successfully built 474d3457c67a
=> Copying lambda build...
Creating network "lambdaecstasks_default" with the default driver
Creating lambdaecstasks_lambda_1
Attaching to lambdaecstasks_lambda_1
lambda_1  | ============================= test session starts ==============================
lambda_1  | platform linux2 -- Python 2.7.12, pytest-3.0.7, py-1.4.33, pluggy-0.4.0 -- /usr/bin/python2.7
lambda_1  | cachedir: .cache
lambda_1  | rootdir: /build/src, inifile:
lambda_1  | collecting ... collected 50 items
lambda_1  |
lambda_1  | tests/test_cfn.py::test_run_when_run_on_rollback_disabled PASSED
lambda_1  | tests/test_cfn.py::test_run_when_update_criteria_met PASSED
lambda_1  | tests/test_cfn.py::test_no_run_when_update_criteria_not_met PASSED
lambda_1  | tests/test_cfn.py::test_no_run_when_run_on_update_disabled PASSED
lambda_1  | tests/test_cfn.py::test_run_task[Create] PASSED
lambda_1  | tests/test_cfn.py::test_run_task[Update] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_zero_timeout[Create] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_zero_timeout[Update] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_failure[Create] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_failure[Update] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_non_zero_exit_code[Create] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_non_zero_exit_code[Update] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_execution_timeout[Create] PASSED
lambda_1  | tests/test_cfn.py::test_run_task_execution_timeout[Update] PASSED
lambda_1  | tests/test_cfn.py::test_create_new_task_completion_timeout[Create] PASSED
lambda_1  | tests/test_cfn.py::test_create_new_task_completion_timeout[Update] PASSED
lambda_1  | tests/test_cfn.py::test_missing_property[Create-Cluster] PASSED
lambda_1  | tests/test_cfn.py::test_missing_property[Create-TaskDefinition] PASSED
lambda_1  | tests/test_cfn.py::test_missing_property[Update-Cluster] PASSED
lambda_1  | tests/test_cfn.py::test_missing_property[Update-TaskDefinition] PASSED
lambda_1  | tests/test_cfn.py::test_missing_property[Delete-Cluster] PASSED
lambda_1  | tests/test_cfn.py::test_missing_property[Delete-TaskDefinition] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-Count] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-RunOnUpdate] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-RunOnRollback] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-Timeout] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-PollInterval] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-Instances] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Create-Overrides] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-Count] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-RunOnUpdate] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-RunOnRollback] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-Timeout] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-PollInterval] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-Instances] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Update-Overrides] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-Count] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-RunOnUpdate] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-RunOnRollback] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-Timeout] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-PollInterval] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-Instances] PASSED
lambda_1  | tests/test_cfn.py::test_invalid_property[Delete-Overrides] PASSED
lambda_1  | tests/test_ecs.py::test_create_task_created PASSED
lambda_1  | tests/test_ecs.py::test_create_task_failure PASSED
lambda_1  | tests/test_ecs.py::test_check_task_running PASSED
lambda_1  | tests/test_ecs.py::test_check_task_completed PASSED
lambda_1  | tests/test_ecs.py::test_check_task_timeout PASSED
lambda_1  | tests/test_ecs.py::test_check_task_exited_non_zero PASSED
lambda_1  | tests/test_ecs.py::test_check_task_failure PASSED
lambda_1  |
lambda_1  | ------------------ generated xml file: /build/src/report.xml -------------------
lambda_1  | ========================== 50 passed in 0.47 seconds ===========================
lambdaecstasks_lambda_1 exited with code 0
=> Build complete
```

### Function Naming

The default name for this function is `ecsTasks` and the corresponding ZIP package that is generated is called `ecsTasks.zip`.

If you want to change the function name, you can either update the `FUNCTION_NAME` setting in the `Makefile` or alternatively configure an environment variable of the same name to override the default function name.

## Publishing the Function

When you publish the function, you are simply copying the built ZIP package to an S3 bucket.  Before you can do this, you must ensure you have created the S3 bucket and your environment is configured correctly with appropriate AWS credentials and/or profiles.

To specify the S3 bucket that the function should be published to, you can either configure the `S3_BUCKET` setting in the `Makefile` or alternatively configure an environment variable of the same name to override the default S3 bucket name.

> [Versioning](http://docs.aws.amazon.com/AmazonS3/latest/dev/Versioning.html) should be enabled on the S3 bucket

To deploy the built ZIP package:

`make publish`

This will upload the built ZIP package to the configured S3 bucket.

> When a new or updated package is published, the S3 object version will be displayed.

### Publishing to a Custom S3 Bucket

If you want to publish to a custom S3 bucket, you can set the `S3_BUCKET` environment variable and then run `make publish`.

> [Versioning](http://docs.aws.amazon.com/AmazonS3/latest/dev/Versioning.html) must be enabled on the S3 bucket

### Publish Example

```
$ make publish
=> Publishing ecsTasks.zip to s3://012345678901-cfn-lambda...
=> Published to S3 URL: https://s3.amazonaws.com/012345678901-cfn-lambda/ecsTasks.zip
=> S3 Object Version: HJCxTQfAIRSS6bYi7C0TL41PNKMZLvhi
```

## CloudFormation Usage

The [`ecs_tasks`](src/ecs_tasks.py) function is designed to be called from a CloudFormation template as a custom resource.

The following custom resource calls this Lambda function when the resource is created, updated or deleted:

```
  MigrateTask:
    Type: "Custom::ECSTask"
    Properties:
      ServiceToken: "arn:aws:lambda:us-west-2:012345678901:function:dev-ecsTasks"
      Cluster: { "Ref": "ApplicationCluster" }
      TaskDefinition: { "Ref": "ApplicationTaskDefinition" }
      Count: 1              
      Timeout: 1800           # The maximum amount of time to wait for the task to complete - defaults to 290 seconds
      RunOnUpdate: True       # Controls if the task should run for update operations - defaults to True
      RunOnRollback: False    # Controls if the task should run in the event of a stack rollback - defaults to True
      UpdateCriteria:         # Specifies criteria to determine if a task update should run
        - Container: app
          EnvironmentKeys:    # List of environment keys to compare.  The task is only run if the environment key value has changed.
            - DB_HOST
      PollInterval: 30        # How often to poll the status of a given task
      Overrides:              # Task definition overrides
        containerOverrides:
          - name: app
            command:
              - manage.py
              - migrate
            environment:
              - name SOME_VAR
                value
      Instances:              # Optional list of container instances to run the task on
        - arn:aws:ecs:us-west-2:012345678901:container-instance/9d8698b5-5477-4b8b-bb63-dfd1e140b0d8

```

The following table describes the various properties:

| Property       | Description                                                                                                                                                                                                                                                                                                                                                                                          | Required | Default Value |
|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------|---------------|
| ServiceToken   | The ARN of the Lambda function                                                                                                                                                                                                                                                                                                                                                                       | Yes      |               |
| Cluster        | The name of the ECS Cluster to run the task on                                                                                                                                                                                                                                                                                                                                                       | Yes      |               |
| TaskDefinition | The family, family:revision or full ARN of the ECS task definition that the ECS task is executed from.                                                                                                                                                                                                                                                                                               | Yes      |               |
| Count          | The number of task instances to run.  If the Instances property is set, this count value is ignored as one task per instance will be run.  If set to 0, no tasks will be run (even if the Instances property is set).                                                                                                                                                                                | No       | 1             |
| Timeout        | The maximum time in seconds to wait for the task to complete successfully.  If set to 0, the function will run the task and return immediately.                                                                                                                                                                                                                                                      | No       | 290           |
| RunOnUpdate    | Controls if the task should be run for update to the resource.                                                                                                                                                                                                                                                                                                                                       | No       | True          |
| RunOnRollback  | Controls if the task should be run if the stack is in a rollback state                                                                                                                                                                                                                                                                                                                               | No       | True          |
| UpdateCriteria | Optional list of criteria used to determine if the task should be run for an update to the resource.   If specified, you must configure the `Container` property as the name of a container in the task definition, and specify a list of environment variable keys using the `EnvironmentKey` property.  If any of the specified environment variable values  have changed, then the task will run. | No       |               |
| Overrides      | Optional task definition overrides to apply to the specified task definition.                                                                                                                                                                                                                                                                                                                        | No       |               |
| Instances      | Optional list of ECS container instances to run the task on.  If specified, you must use the ARN of each ECS container instance.                                                                                                                                                                                                                                                                     | No       |               |
| Triggers       | List of triggers that can be used to trigger updates to this resource, based upon changes to other resources.  This property is ignored by the Lambda function.                                                                                                                                                                                                                                      |          |               |

# License

Copyright (C) 2017.  Case Commons, Inc.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

See www.gnu.org/licenses/agpl.html
