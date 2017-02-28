FROM amazonlinux
MAINTAINER Pema Geyleg <pema@casecommons.org>
ARG project_name
LABEL application=${project_name}

# Install build dependencies
RUN yum install python27-pip zip -y && \
    pip install -U pip

# Copy requirements
COPY src/requirements* /build/src/

# Install test dependencies
RUN pip install -r /build/src/requirements_test.txt

# Install function dependencies
WORKDIR /build/src
RUN pip install -t vendor/ -r requirements.txt --upgrade

# Create function archive
COPY src /build/src
ARG function_name
RUN zip -9 -r ../${function_name}.zip * -x *.pyc -x requirements_test.txt -x tests/ -x tests/**\*

# Run tests
CMD ["pytest", "--junitxml", "report.xml"]