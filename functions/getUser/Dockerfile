# Use AWS Lambda base image for Python 3.11
FROM public.ecr.aws/lambda/python:3.11-slim

# Copy requirements.txt and install dependencies
COPY src/requirements.txt ./
RUN pip install -r requirements.txt

# Copy the function code (e.g., app.py)
COPY src/app.py ./

# Set the Lambda handler (app.py → lambda_handler)
CMD ["app.lambda_handler"]