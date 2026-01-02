from fasthtml.common import *
from in_memory_storage import InMemoryStorage, Task
from datetime import datetime, date
from pathlib import Path
from starlette.responses import HTMLResponse

# Initialize the in-memory storage
storage = InMemoryStorage()

# FastHTML App Initialization - using idiomatic pattern
app, rt = fast_app()

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
        Path(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"),
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
    return Div(*task_items, id="inbox-task-list")

# Index route - serves the main HTML page
@rt
def index():
    """Serve the main HTML page"""
    html_file = Path(__file__).parent / "main_page.html"
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

serve()
