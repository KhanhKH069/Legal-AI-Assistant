"""Helper Functions"""

def format_response(status: str, data=None, error=None):
    response = {'status': status}
    if data:
        response['data'] = data
    if error:
        response['error'] = error
    return response
