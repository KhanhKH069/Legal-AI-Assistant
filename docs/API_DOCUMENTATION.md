# API Documentation

## HRAgentApp Class

### Methods

#### `chat(user_id: str, message: str, api_key: str = None) -> dict`

Process user message through the system.

**Parameters:**
- `user_id`: User identifier
- `message`: User message text
- `api_key`: Optional API key for authentication

**Returns:**
```python
{
    'status': 'success',
    'response': 'Agent response text',
    'intent': 'POLICY_AGENT',
    'user_id': 'user001'
}
```

**Example:**
```python
app = HRAgentApp()
response = app.chat("user001", "Có bao nhiêu ngày phép?")
print(response['response'])
```

## API Gateway

### Authentication

All requests must include valid user_id.

### Rate Limiting

- 10 requests per minute per user
- Returns 429 error when exceeded

## Agents

### Policy Agent
Handles HR policy questions.

**Tools:**
- get_policy_info
- calculate_leave_days
- search_hr_qa

### Onboard Agent
Handles onboarding questions.

**Tools:**
- get_onboarding_checklist
- search_hr_qa

## Error Codes

- 200: Success
- 401: Unauthorized
- 429: Rate limit exceeded
- 500: Internal error
