"""API Client Example"""
# Example of how to use the agent as an API client

def call_agent(user_id, message):
    response = {
        'user_id': user_id,
        'message': message,
        'response': 'Mock API response'
    }
    return response

print(call_agent("user001", "Test message"))
