import json
import redis
import os
from celery import shared_task
from src.agents.contract_reviewer_agent import run_contract_review

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

@shared_task(bind=True, name="src.tasks.async_review.process_contract")
def process_contract(self, combined_text: str):
    job_id = self.request.id
    
    # Notify start
    redis_client.publish(f"job_status_{job_id}", json.dumps({"status": "processing"}))
    
    try:
        # Run heavy LangGraph agent
        result = run_contract_review(combined_text)
        
        # Publish success
        redis_client.publish(
            f"job_status_{job_id}", 
            json.dumps({"status": "success", "result": result})
        )
        return {"status": "success", "result": result}
        
    except Exception as e:
        # Publish error
        error_msg = str(e)
        redis_client.publish(
            f"job_status_{job_id}", 
            json.dumps({"status": "error", "error": error_msg})
        )
        return {"status": "error", "error": error_msg}
