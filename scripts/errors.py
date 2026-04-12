from botocore.exceptions import ClientError, NoCredentialsError

def format_aws_error(error: ClientError, context: dict | None) -> str:
    code = error.response["Error"]["Code"]

    if code == "UnauthorizedOperation":
        message = error.response["Error"].get("Message", "")
        return f"Insufficient permissions. {message}"

    if code == "RequestLimitExceeded":
        return "AWS API rate limit reached. Please wait and try again."
    
    return f"AWS error ({code}): {error.response['Error'].get('Message', 'Unknown error')}"

def credential_error(error: NoCredentialsError, context: dict | None) -> str:
    
    return (
    "AWS credentials not found. Configure credentials using "
    "`aws configure` or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
    "environment variables."
    ) 
    