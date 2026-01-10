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
              hx_target="#inbox-task-list-inner", # Updated target
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

@rt("/tasks") # Renamed endpoint to /tasks
def get_tasks(view: str = "inbox"): # Renamed function, added view parameter
    """Fetch and render tasks based on the selected view (inbox, today, active, maybe)."""
    if view == "today":
        tasks = storage.get_tasks(due_date=date.today())
        header_title = "Today"
    elif view == "inbox": # Default to "inbox"
        tasks = storage.get_tasks(state="inbox")
        header_title = "Inbox"
    else:
        # Default fallback, should ideally not be hit with proper frontend setup
        tasks = storage.get_tasks(state="inbox")
        header_title = "Inbox"

    task_items = [render_task_item(task) for task in tasks]

    return Group(
        render_sidebar(current_view=view),
        H1(header_title, id="main-content-header", _class="text-2xl font-bold", 
           hx_swap_oob="true"),
        Div(*task_items, id="inbox-task-list-inner")
    )

def render_sidebar(current_view: str):
    """Renders the sidebar, highlighting the current view."""
    def get_link_classes(view_name: str):
        if view_name == current_view:
            return "flex items-center justify-between px-3 py-2 rounded-lg bg-orange-100 text-orange-600 font-medium text-base"
        return "flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-100 text-gray-700 font-medium text-base"

    return Aside(
        Div(
            Div(
                H1("GTD App", cls="text-xl font-bold text-gray-800"),
                cls="p-5 border-b border-gray-200"
            ),
            Div(
                Button(
                    Svg(
                        SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M12 4v16m8-8H4"),
                        cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                    ),
                    Span("Add task"),
                    onclick="openModal('newTaskModal')",
                    cls="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-red-500 hover:bg-red-600 rounded-lg shadow-sm text-white text-base font-medium"
                ),
                Div(
                    Svg(
                        SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"),
                        cls="absolute left-3.5 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400",
                        fill="none", stroke="currentColor", viewBox="0 0 24 24"
                    ),
                    Input(type="text", placeholder="Search",
                          cls="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 text-base"),
                    cls="mt-4 relative"
                ),
                cls="p-5"
            ),
            Div(
                Div(
                    A(
                        Div(
                            Svg(
                                SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"),
                                cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                            ),
                            Span("Inbox"),
                            cls="flex items-center gap-3"
                        ),
                        Span("13", cls="text-sm font-semibold"),
                        href="/tasks?view=inbox", hx_get="/tasks?view=inbox", hx_target="#inbox-task-list-inner", hx_push_url="true",
                        cls=get_link_classes("inbox")
                    ),
                    A(
                        Div(
                            Svg(
                                SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"),
                                cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                            ),
                            Span("Today"),
                            cls="flex items-center gap-3"
                        ),
                        Span("25", cls="text-sm font-semibold"),
                        href="/tasks?view=today", hx_get="/tasks?view=today", hx_target="#inbox-task-list-inner", hx_push_url="true",
                        cls=get_link_classes("today")
                    ),
                    A(
                        Div(
                            Svg(
                                SvgPath(stroke_linecap="round", stroke_linejoin="round", d="M13 10V3L4 14h7v7l9-11h-7z"),
                                cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                            ),
                            Span("Active"),
                            cls="flex items-center gap-3"
                        ),
                        href="#",
                        cls=get_link_classes("active")
                    ),
                    A(
                        Div(
                            Svg(
                                SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"),
                                cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                            ),
                            Span("Maybe"),
                            cls="flex items-center gap-3"
                        ),
                        href="#",
                        cls=get_link_classes("maybe")
                    ),
                    cls="space-y-1.5"
                ),
                Hr(cls="my-4 border-gray-200"),
                Div(
                    A(
                        Div(
                            Svg(
                                SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M5 13l4 4L19 7"),
                                cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                            ),
                            Span("Completed"),
                            cls="flex items-center gap-3"
                        ),
                        href="#",
                        cls="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-100 text-gray-700 font-medium text-base"
                    ),
                    cls="space-y-1.5"
                ),
                Hr(cls="my-4 border-gray-200"),
                Div(
                    H3("My Projects", cls="px-3 py-2 text-sm font-semibold text-gray-500 uppercase tracking-wider"),
                    Div(
                        A(
                            Div(
                                Span("#", cls="font-semibold text-gray-400"),
                                Span("Home"),
                                cls="flex items-center gap-3"
                            ),
                            Span("5", cls="text-sm text-gray-500"),
                            href="#",
                            cls="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-100 text-gray-700 font-medium text-base"
                        ),
                        A(
                            Div(
                                Span("#", cls="font-semibold text-gray-400"),
                                Span("volleyball"),
                                cls="flex items-center gap-3"
                            ),
                            href="#",
                            cls="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-gray-100 text-gray-700 font-medium text-base"
                        ),
                        cls="space-y-1.5 mt-2"
                    )
                ),
                cls="flex-1 overflow-y-auto px-5"
            ),
            cls="flex flex-col flex-1"
        ),
        Div(
            A(
                Svg(
                    SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.096 2.572-1.065z"),
                    SvgPath(stroke_linecap="round", stroke_linejoin="round", stroke_width="2", d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"),
                    cls="w-5 h-5", fill="none", stroke="currentColor", viewBox="0 0 24 24"
                ),
                "Settings",
                href="#",
                cls="flex items-center gap-3 text-gray-600 hover:text-gray-800 text-base font-medium"
            ),
            cls="p-5 border-t border-gray-200"
        ),
        id="left-sidebar",
        cls="w-80 bg-gray-50 border-r border-gray-200 flex flex-col",
        hx_swap_oob="true"
    )

@rt("/add-task")
def post(form: AddTaskForm):
    """Handles adding a new task from the modal form."""
    task_data = form.model_dump(exclude_unset=True)
    
    # Ensure project is "default" if not provided or empty string
    if task_data.get('project') is None or task_data.get('project').strip() == '':
        task_data['project'] = 'default'
    
    storage.add_task(task_data)
    
    # Re-render the task list and send a header to trigger modal closure
    # After adding a task, we should refresh the inbox view
    response = get_tasks(view="inbox")
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
    response = get_tasks(view="inbox") # After updating, refresh to inbox view
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
