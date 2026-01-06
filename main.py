import calendar
from fasthtml.common import *
from fasthtml.svg import *
from fasthtml.svg import Path as SvgPath
from in_memory_storage import InMemoryStorage, Task
from datetime import datetime, date, timedelta
from pathlib import Path
from starlette.responses import HTMLResponse

from pydantic import BaseModel # Added this import

# Initialize the in-memory storage
storage = InMemoryStorage()

# FastHTML App Initialization - using idiomatic pattern
app, rt = fast_app()

# Pydantic model for adding a new task from the form
class AddTaskForm(BaseModel):
    title: str
    description: Optional[str] = None
    project: Optional[str] = None

# Pydantic model for editing an existing task from the form
class EditTaskForm(BaseModel):
    title: str
    description: Optional[str] = None
    project: Optional[str] = None
    schedule: Optional[str] = None # Added schedule field

# Helper function to render a single task item HTML using FastHTML DSL
def render_task_item(task: Task):
    date_label = ""
    date_color = ""
    if task.due_date:
        if task.due_date == date.today():
            date_label = "Today"
            date_color = "text-red-600"
        elif task.due_date < date.today():
            date_label = "Overdue"
            date_color = "text-red-800 font-bold"
        else:
            date_label = task.due_date.strftime("%b %d") # e.g., Jul 07
            date_color = "text-gray-500" # Default for future dates
    
    project_html_element = None
    if task.project and task.project != "default":
        project_html_element = Span(
            Span("#", cls="font-semibold text-gray-400"),
            task.project,
            cls="flex items-center gap-1.5 px-2 py-0.5 rounded text-sm font-medium bg-yellow-100 text-yellow-800"
        )
    elif task.project == "default":
        project_html_element = Span(
            Span("#", cls="font-semibold text-gray-400"),
            "default",
            cls="flex items-center gap-1.5 px-2 py-0.5 rounded text-sm font-medium bg-gray-100 text-gray-600"
        )

    calendar_svg_element = Svg(
        SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"),
        cls="w-4 h-4", fill="none", stroke="currentColor", viewBox="0 0 24 24"
    )

    checked_attr = True if task.state == "completed" else False
    line_through_cls = "line-through text-gray-500" if task.state == "completed" else ""

    return Div(
        Input(type="checkbox", checked=checked_attr,
              cls="mt-1 flex-shrink-0 w-5 h-5 rounded-full border-gray-400 focus:ring-green-500",
              hx_post=f"/toggle-task-complete/{task.id}",
              hx_target="#inbox-task-list",
              hx_swap="innerHTML",
              onclick="event.stopPropagation();"), # Stop propagation to prevent opening edit modal
        Div(
            P(task.title, cls=f"text-base text-gray-800 {line_through_cls}"),
            Div(
                Span(
                    calendar_svg_element,
                    date_label,
                    cls=f"flex items-center gap-1.5 text-sm {date_color}"
                ) if date_label else None,
                project_html_element,
                cls="flex items-center gap-4 flex-wrap mt-1"
            ),
            cls="flex-1"
        ),
        id=f"task-{task.id}",
        hx_get=f"/get-task-data/{task.id}",
        hx_target="#editTaskModal-content-area", # Target specific area in edit modal
        hx_swap="innerHTML",
        onclick="document.getElementById('editTaskModal').classList.remove('hidden');", # Open modal via JS
        cls="flex items-start gap-4 p-3 hover:bg-gray-50 rounded-lg border-b border-gray-200 cursor-pointer"
    )

@rt("/tasks-list")
def get_tasks_list():
    """Fetch and render the list of tasks in the inbox"""
    tasks = storage.get_tasks()  # Inbox tasks
    task_items = [render_task_item(task) for task in tasks]
    return Div(*task_items, id="inbox-task-list-inner")

@rt("/add-task")
def post(form: AddTaskForm):
    """Handles adding a new task from the modal form."""
    task_data = form.model_dump(exclude_unset=True)
    
    # Ensure project is "default" if not provided or empty string
    if task_data.get('project') is None or task_data.get('project').strip() == '':
        task_data['project'] = 'default'
    
    storage.add_task(task_data)
    
    # Re-render the task list and send a header to trigger modal closure
    response = get_tasks_list()
    # response.hx_trigger = "taskAdded"
    return Response(to_xml(response), headers={"HX-Trigger": "taskAdded"})

@rt("/get-task-data/{task_id}")
def get(task_id: int):
    """Fetches a single task's data and renders the edit form."""
    task = storage.get_task_by_id(task_id)
    if not task:
        return Div("Task not found", cls="text-red-500")

    return Form(
        Div(
            Label("Task name", fr="editTaskName", cls="block text-base font-medium text-gray-700 mb-2"),
            Input(type="text", id="editTaskName", name="title", value=task.title,
                  cls="w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 text-base"),
            cls="mb-4"
        ),
        Div(
            Label("Description", fr="editTaskDescription", cls="block text-base font-medium text-gray-700 mb-2"),
            Textarea(task.description or "", id="editTaskDescription", name="description", 
                     cls="w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 resize-y h-24 text-base"),
            cls="mb-4"
        ),
        Div(
            Select(
                Option("No Date", value="none", selected=task.schedule is None or task.schedule == ""),
                Option("Today", value="today", selected=task.schedule == "today"),
                Option("This Week", value="week", selected=task.schedule == "week"),
                Option("This Month", value="month", selected=task.schedule == "month"),
                Option("Maybe", value="maybe", selected=task.schedule == "maybe"),
                name="schedule",
                id="editTaskSchedule",
                cls="block w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 text-base"
            ),
            Input(type="text", id="editTaskProject", name="project", value=task.project if task.project != "default" else "",
                  cls="w-full px-4 py-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 text-base", placeholder="Project (e.g., #Work)"),
            cls="flex items-center gap-4 mb-6"
        ),
        Div(
            Button("Cancel", type="button", onclick="closeModal('editTaskModal')",
                   cls="px-5 py-2.5 text-base font-medium text-gray-700 hover:bg-gray-100 rounded-md"),
            Button("Save changes", type="submit",
                   cls="px-5 py-2.5 text-base font-medium text-white bg-red-500 hover:bg-red-600 rounded-md"),
            cls="flex items-center justify-end gap-3"
        ),
        hx_put=f"/update-task/{task.id}", # HTMX PUT request to update task
        hx_target="#inbox-task-list",       # Target to replace after update
        hx_swap="innerHTML",                # Swap innerHTML of the target
        # hx_trigger="taskEdited from:body"  # Custom event to close modal after success
    )

@rt("/update-task/{task_id}")
async def put(task_id: int, form: EditTaskForm):
    """Handles updating an existing task from the modal form."""
    update_data = form.model_dump(exclude_unset=True)

    # Calculate due_date based on schedule
    schedule = form.schedule
    due_date = None
    new_state = None # To store potential new state

    if schedule == "today":
        due_date = date.today()
        new_state = "active" # A task with a 'today' schedule should be active
    elif schedule == "week":
        today = date.today()
        # Calculate days until next Friday (weekday 4)
        days_until_friday = (4 - today.weekday() + 7) % 7
        due_date = today + timedelta(days=days_until_friday)
        new_state = "active" # A task with a 'week' schedule should be active
    elif schedule == "month":
        today = date.today()
        year = today.year
        month = today.month
        last_day = calendar.monthrange(year, month)[1]
        due_date = date(year, month, last_day)
        new_state = "active" # A task with a 'month' schedule should be active
    elif schedule == "maybe":
        due_date = None
        new_state = "maybe" # Set state to 'maybe' if schedule is 'maybe'
    elif schedule == "none": # Explicitly "none" or if schedule is not provided, clear due_date
        due_date = None
        new_state = "inbox" # Move it back to inbox if no specific schedule

    update_data['due_date'] = due_date
    update_data['schedule'] = schedule # Store the selected schedule string

    if new_state:
        update_data['state'] = new_state

    # Ensure project is "default" if not provided or empty string
    if update_data.get('project') is None or update_data.get('project').strip() == '':
        update_data['project'] = 'default'

    updated_task = storage.update_task(task_id, update_data)
    if not updated_task:
        return Div("Task not found or failed to update", cls="text-red-500")

    # Re-render the task list and send a header to trigger modal closure
    response = get_tasks_list()
    return Response(to_xml(response), headers={"HX-Trigger": "taskEdited"})

# Index route - serves the main HTML page
@rt
def index():
    """Serve the main HTML page"""
    html_file = Path(__file__).parent / "main_page.html"
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

serve()
