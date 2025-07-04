import logging
import sys
import os
from multiprocessing import Process, Queue
import uuid
from typing import Dict, Any, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from browser_use.agent.service import Agent
from browser_use.api.views import TaskStatus
from browser_use.llm.openai.chat import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, filename='api_service.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# In-memory storage for tasks.
tasks: Dict[str, Any] = {}

def agent_process_wrapper(queue: Queue, task_description: str, model_name: Optional[str]):
    """A wrapper to run the agent in a separate process."""
    import asyncio
    try:
        logging.info("Agent process started.")
        effective_model_name = model_name or 'gpt-4o'
        llm = ChatOpenAI(model=effective_model_name)
        agent = Agent(task=task_description, llm=llm)
        history = asyncio.run(agent.run())
        queue.put({'status': 'completed', 'result': history.model_dump()})
        logging.info("Agent process finished successfully.")
    except Exception as e:
        logging.error(f"Agent process failed: {e}", exc_info=True)
        queue.put({'status': 'failed', 'result': str(e)})

def start_agent_process(task_id: str, task_description: str, model_name: Optional[str]):
    """Starts the agent process and updates the task entry."""
    q = Queue()
    p = Process(target=agent_process_wrapper, args=(q, task_description, model_name))
    p.start()
    tasks[task_id]['process'] = p
    tasks[task_id]['queue'] = q
    logging.info(f"Started process for task {task_id}")


async def run_agent_task(task_id: str, task_description: str, model_name: Optional[str]):
    """
    Runs the agent in the background using a separate process.
    """
    logging.info(f"Queueing task {task_id}")
    tasks[task_id]['status'] = 'running'
    # This function is now just a placeholder to be called by background_tasks
    # The actual process is started by `start_agent_process` which should be called
    # from the main thread to avoid issues with multiprocessing in threads.
    # Let's simplify and call it directly from the endpoint.
    # The background_tasks will run this, but we'll start the *real* work in a process.
    start_agent_process(task_id, task_description, model_name)


def create_task(task_description: str, model_name: Optional[str]) -> str:
    """
    Creates a new task and returns the task ID.
    """
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"task_id": task_id, "status": "pending", "result": None}
    return task_id

def get_task_status(task_id: str) -> TaskStatus:
    """
    Retrieves the status of a task, checking the process queue if it's still running.
    """
    task_info = tasks.get(task_id)
    if not task_info:
        return None

    process = task_info.get('process')
    if process and process.is_alive():
        return TaskStatus(**task_info) # It's still running

    queue = task_info.get('queue')
    if queue and not queue.empty():
        result = queue.get()
        task_info['status'] = result['status']
        task_info['result'] = result['result']
        if 'process' in task_info:
            del task_info['process']
        if 'queue' in task_info:
            del task_info['queue']

    return TaskStatus(**task_info) 