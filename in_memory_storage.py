from storage_interface import IStorage, Task
from typing import List, Dict, Any, Optional
from datetime import datetime, date

class InMemoryStorage(IStorage):
    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._next_id = 1
        self._seed_data()

    def _seed_data(self):
        # Seed some dummy tasks
        self.add_task({"title": "create datasets management webapp", "due_date": date(2025, 7, 7), "project": "maybe", "schedule": "today", "state": "inbox"})
        self.add_task({"title": "create local docker repository", "project": "maybe", "state": "inbox"})
        self.add_task({"title": "basketball player tracking: get detections without NMS", "project": "maybe", "state": "inbox"})
        self.add_task({"title": "generic framework for resuming processes after power fail/restart", "due_date": date(2025, 7, 11), "project": "next", "schedule": "week", "state": "active"})
        self.add_task({"title": "joint ball and carrier detection", "state": "inbox"})
        self.add_task({"title": "Vollyball total match count", "due_date": date(2025, 9, 15), "project": "maybe", "state": "inbox"})
        self.add_task({"title": "Ball carrier filter", "due_date": date(2025, 9, 22), "project": "next", "state": "inbox"})


    def get_tasks(self, **filters: Any) -> List[Task]:
        filtered_tasks = []
        for task in self._tasks.values():
            match = True
            for key, value in filters.items():
                if not hasattr(task, key) or getattr(task, key) != value:
                    match = False
                    break
            if match:
                filtered_tasks.append(task)
        return filtered_tasks

    def add_task(self, task_data: Dict[str, Any]) -> Task:
        # Generate ID and fill in default/calculated fields
        task_id = self._next_id
        self._next_id += 1
        
        now = datetime.now()
        full_task_data = {
            "id": task_id,
            "title": task_data.get("title", "Untitled Task"),
            "description": task_data.get("description"),
            "state": task_data.get("state", "inbox"),
            "schedule": task_data.get("schedule"),
            "due_date": task_data.get("due_date"),
            "project": task_data.get("project", "default"),
            "completed_at": None,
            "created_at": now,
            "updated_at": now,
        }
        
        # Validate with Pydantic model
        new_task = Task(**full_task_data)
        self._tasks[task_id] = new_task
        return new_task

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def update_task(self, task_id: int, update_data: Dict[str, Any]) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task:
            updated_fields = task.dict()
            for key, value in update_data.items():
                if key in updated_fields and key not in ["id", "created_at"]:
                    updated_fields[key] = value
            updated_fields["updated_at"] = datetime.now()
            
            # Re-validate with Pydantic model
            updated_task = Task(**updated_fields)
            self._tasks[task_id] = updated_task
            return updated_task
        return None

    def delete_task(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def get_projects(self) -> List[str]:
        projects = {task.project for task in self._tasks.values() if task.project and task.project != "default"}
        return sorted(list(projects))

# Initialize the in-memory storage
storage = InMemoryStorage()

# Example usage (for testing purposes)
if __name__ == "__main__":
    s = InMemoryStorage()
    print("All tasks:", s.get_tasks())
    
    new_t = s.add_task({"title": "Learn FastHTML", "description": "Read docs", "project": "dev"})
    print("Added task:", new_t)
    
    found_t = s.get_task_by_id(new_t.id)
    print("Found task:", found_t)
    
    updated_t = s.update_task(new_t.id, {"state": "completed", "completed_at": datetime.now()})
    print("Updated task:", updated_t)
    
    s.delete_task(new_t.id)
    print("Remaining tasks:", s.get_tasks())
