import logging
import sys
import os
from multiprocessing import Process, Queue
from typing import Optional, Any
from pydantic import BaseModel
from langchain.agents import Agent
from langchain.llms import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for tasks
tasks: dict[str, Any] = {}

def agent_process_wrapper(queue, task_description, model_name):
    """A wrapper to run the agent in a separate process."""
    import asyncio
    try:
        llm = ChatOpenAI(model=model_name)
        agent = Agent(task=task_description, llm=llm)
        history = asyncio.run(agent.run())
        queue.put({'status': 'completed', 'result': history.model_dump()})
    except Exception as e:
        # It's tricky to pass the full exception, so we pass a string representation.
        queue.put({'status': 'failed', 'result': str(e)})

async def run_agent_task(task_id: str, task_description: str, model_name: str):
    """
    Runs the agent in the background using a separate process to avoid event loop conflicts.
    """
    logging.info(f"Starting task {task_id}")
    tasks[task_id] = TaskStatus(task_id=task_id, status='pending')
    
    q = Queue()
    p = Process(target=agent_process_wrapper, args=(q, task_description, model_name))
    p.start()
    
    # This part is tricky in an async function. We can't just block.
    # For this implementation, we will assume the main app will poll for status.
    # A more robust solution might involve a callback or a websocket.
    # We will check the queue in the get_task_status function.
    # For now, let's store the process and queue to check later.
    tasks[task_id].process = p
    tasks[task_id].queue = q

def get_task_status(task_id: str) -> TaskStatus:
    """
    Retrieves the status of a task, checking the process queue if it's still running.
    """
    task_info = tasks.get(task_id)
    if not task_info:
        return None

    if hasattr(task_info, 'process') and task_info.process.is_alive():
        return task_info # It's still running

    # If process is done, check the queue for the result.
    if hasattr(task_info, 'queue') and not task_info.queue.empty():
        result = task_info.queue.get()
        task_info.status = result['status']
        task_info.result = result['result']
        # Clean up
        delattr(task_info, 'process')
        delattr(task_info, 'queue')
        
    return task_info

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    process: Optional[Any] = None # To hold the process object
    queue: Optional[Any] = None # To hold the queue

    class Config:
        arbitrary_types_allowed = True 