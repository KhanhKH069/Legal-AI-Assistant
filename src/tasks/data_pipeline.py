import subprocess
from celery import shared_task
import logging

logger = logging.getLogger(__name__)

@shared_task(name="src.tasks.data_pipeline.run_pipeline")
def run_pipeline():
    logger.info("Starting Daily Data Pipeline...")
    try:
        # Step 1: Download latest datasets (assuming a script exists)
        # subprocess.run(["python", "scripts/download_datasets.py"], check=True)
        
        # Step 2: Index to ChromaDB
        subprocess.run(["python", "scripts/index_legal_to_chromadb.py"], check=True)
        
        # Step 3: Index to Neo4j
        subprocess.run(["python", "scripts/index_to_neo4j.py"], check=True)
        
        logger.info("Data pipeline completed successfully.")
        return {"status": "success", "message": "Data pipeline ran successfully."}
    except subprocess.CalledProcessError as e:
        logger.error(f"Data pipeline failed: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"status": "error", "error": str(e)}
