# Use AWS Lambda Python base image
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements and install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy all Python modules (self-contained in this directory)
COPY simple_crawler.py ${LAMBDA_TASK_ROOT}/
COPY zillow.py ${LAMBDA_TASK_ROOT}/
COPY handler.py ${LAMBDA_TASK_ROOT}/

# Fix file permissions for Lambda runtime
RUN chmod 644 ${LAMBDA_TASK_ROOT}/*.py

# Set the Lambda handler
CMD ["handler.lambda_handler"]
