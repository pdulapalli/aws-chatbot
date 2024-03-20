# aws-langchain

## Overview

This project provides a simple natural language chatbot that can answer questions about an AWS account.

It's capable of discovering some portion of information for the following services:
- S3
- EC2
- IAM
- Cost Explorer

## Setup

### Dependencies

This application requires Python 3.10 or above. Please ensure such a version of [Python](https://www.python.org/downloads/) is installed on your system. 

The preferred way to set up and run this application is with a Python virtual environment.

Navigate to the project root directory. Create a virtual environment and enter it like so:
```
python3 -m venv <your-virtualenv-name-here>
source <your-virtualenv-name-here>/bin/activate
```

Install dependencies like so:
```
pip install -r requirements.txt
```

### Configuration

Navigate to the project root directory. Please copy `.env.sample` to `.env` and populate the necessary variables. These will be needed for programmatic access to the OpenAI and AWS APIs.

## Running

This can be run locally via `chainlit`, which will automatically be installed if following the [Setup](#setup) instructions.

Next, in a terminal session, please navigate to the root of this project directory. Enter your Python virtual environment:
```
source <your-virtualenv-name-here>/bin/activate
```

Then run:
```
chainlit run app.py
```

A chatbot application will be served on `localhost`. Please refer to the command output, which should mention the port as part of a URL like so: `http://localhost:<portNumber>`