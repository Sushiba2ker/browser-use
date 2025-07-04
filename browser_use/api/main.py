from fastapi import FastAPI, HTTPException
from browser_use.api import service
from browser_use.api.views import TaskRequest, TaskStatus, TaskCreateResponse

app = FastAPI(
    title="Browser-Use Bridge API",
    description="An API to control the browser-use agent.",
)

@app.post("/agent/run", response_model=TaskCreateResponse)
async def run_agent(request: TaskRequest):
    """
    Starts a new browser agent task in a separate process.
    """
    task_id = service.create_task(request.task, request.model_name)
    service.start_agent_process(task_id, request.task, request.model_name)
    return TaskCreateResponse(task_id=task_id, status="running")


@app.get("/agent/tasks/{task_id}", response_model=TaskStatus)
async def get_task(task_id: str):
    """
    Retrieves the status and result of a specific task.
    """
    task = service.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.get("/")
def read_root():
    return {"message": "Welcome to the Browser-Use Bridge API"}

# To run this API, save it as main.py and run the following command in your terminal:
# uvicorn browser_use.api.main:app --reload 