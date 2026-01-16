from storage_interface import IStorage, Task
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlmodel import create_engine, Session, select, SQLModel
from pathlib import Path

class SQLiteStorage(IStorage):
    def __init__(self, db_path: str = "gtd.db"):
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}")
        self._create_database()
        self._seed_data()

    def _create_database(self):
        """Create database tables if they don't exist"""
        SQLModel.metadata.create_all(self.engine)

    def _seed_data(self):
        """Seed initial data if database is empty"""
        with Session(self.engine) as session:
            # Check if database is empty
            existing_tasks = session.exec(select(Task)).first()
            if existing_tasks is None:
                # Seed some dummy tasks (same as in_memory_storage.py)
                seed_tasks = [
                    Task(title="create datasets management webapp", due_date=date(2025, 7, 7), project="maybe", schedule="today", state="inbox"),
                    Task(title="create local docker repository", project="maybe", state="inbox"),
                    Task(title="basketball player tracking: get detections without NMS", project="maybe", state="inbox"),
                    Task(title="generic framework for resuming processes after power fail/restart", due_date=date(2025, 7, 11), project="next", schedule="week", state="active"),
                    Task(title="joint ball and carrier detection", state="inbox"),
                    Task(title="Vollyball total match count", due_date=date(2025, 9, 15), project="maybe", state="inbox"),
                    Task(title="Ball carrier filter", due_date=date(2025, 9, 22), project="next", state="inbox"),
                ]
                for task in seed_tasks:
                    session.add(task)
                session.commit()

    def get_tasks(self, **filters: Any) -> List[Task]:
        with Session(self.engine) as session:
            statement = select(Task)
            
            # Apply filters (including __ne support)
            for key, value in filters.items():
                if key.endswith('__ne'):
                    attr_name = key[:-4]  # Remove '__ne'
                    statement = statement.where(getattr(Task, attr_name) != value)
                else:
                    statement = statement.where(getattr(Task, key) == value)
            
            return list(session.exec(statement).all())

    def add_task(self, task_data: Dict[str, Any]) -> Task:
        with Session(self.engine) as session:
            now = datetime.now()
            new_task = Task(
                title=task_data.get("title", "Untitled Task"),
                description=task_data.get("description"),
                state=task_data.get("state", "inbox"),
                schedule=task_data.get("schedule"),
                due_date=task_data.get("due_date"),
                project=task_data.get("project", "default"),
                completed_at=None,
                created_at=now,
                updated_at=now,
            )
            
            session.add(new_task)
            session.commit()
            session.refresh(new_task)
            return new_task

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        with Session(self.engine) as session:
            statement = select(Task).where(Task.id == task_id)
            return session.exec(statement).first()

    def update_task(self, task_id: int, update_data: Dict[str, Any]) -> Optional[Task]:
        with Session(self.engine) as session:
            statement = select(Task).where(Task.id == task_id)
            task = session.exec(statement).first()
            
            if task:
                for key, value in update_data.items():
                    if key in ["id", "created_at"]:
                        continue  # Don't update these fields
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                task.updated_at = datetime.now()
                session.add(task)
                session.commit()
                session.refresh(task)
                return task
            return None

    def delete_task(self, task_id: int) -> bool:
        with Session(self.engine) as session:
            statement = select(Task).where(Task.id == task_id)
            task = session.exec(statement).first()
            
            if task:
                session.delete(task)
                session.commit()
                return True
            return False

    def get_projects(self) -> List[str]:
        with Session(self.engine) as session:
            statement = select(Task.project).where(Task.project != "default").distinct()
            projects = session.exec(statement).all()
            return sorted(list(projects))

# Initialize the SQLite storage
storage = SQLiteStorage()