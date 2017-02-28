# Project variables
export PROJECT_NAME ?= lambda-ecs-tasks

# Parameters
export FUNCTION_NAME ?= cfnEcsTasks
S3_BUCKET ?= 160775127577-cfn-lambda
AWS_DEFAULT_REGION ?= us-west-2

include Makefile.settings

.PHONY: test build publish clean

test:
	@ ${INFO} "Creating lambda build..."
	@ docker-compose $(TEST_ARGS) build $(PULL_FLAG) lambda
	@ ${INFO} "Copying lambda build..."
	@ docker-compose $(TEST_ARGS) up lambda
	@ rm -rf build
	@ mkdir -p build
	@ docker cp $$(docker-compose $(TEST_ARGS) ps -q lambda):/build/src/report.xml build/
	@ $(call check_exit_code,$(TEST_ARGS),lambda)
	@ docker cp $$(docker-compose $(TEST_ARGS) ps -q lambda):/build/$(FUNCTION_NAME).zip build/
	@ ${INFO} "Build complete"

build:
	@ ${INFO} "Building $(FUNCTION_NAME).zip..."
	@ rm -rf src/vendor
	@ cd src && pip install -t vendor/ -r requirements.txt --upgrade
	@ mkdir -p build
	@ cd src && zip -9 -r ../build/$(FUNCTION_NAME).zip * -x *.pyc -x requirements_test.txt -x tests/ -x tests/**\*
	@ ${INFO} "Built build/$(FUNCTION_NAME).zip"

publish:
	@ ${INFO} "Publishing $(FUNCTION_NAME).zip to s3://$(S3_BUCKET)..."
	@ aws s3 cp --quiet build/$(FUNCTION_NAME).zip s3://$(S3_BUCKET)
	@ ${INFO} "Published to S3 URL: https://s3.amazonaws.com/$(S3_BUCKET)/$(FUNCTION_NAME).zip"
	@ ${INFO} "S3 Object Version: $(S3_OBJECT_VERSION)"

clean:
	${INFO} "Destroying build environment..."
	@ docker-compose $(TEST_ARGS) down -v || true
	${INFO} "Removing dangling images..."
	@ $(call clean_dangling_images,$(PROJECT_NAME))
	@ ${INFO} "Removing all distributions..."
	@ rm -rf src/*.pyc src/vendor build
	${INFO} "Clean complete"