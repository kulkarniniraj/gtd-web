from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from sqlmodel import SQLModel, Field as SQLField

# SQLModel/Pydantic model for Task data transfer
class Task(SQLModel, table=True):
    # 'id' is Optional for new tasks, but will be set once stored.
    # It's here for consistency when retrieving tasks.
    id: Optional[int] = SQLField(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    state: str = "inbox"  # inbox | active | maybe | completed
    schedule: Optional[str] = None # today | week | month
    due_date: Optional[date] = None
    project: str = "default" # Default to "default" as per spec
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Abstract Base Class for the Storage Adapter
class IStorage(ABC):
    """
    An abstract interface for a storage adapter. It defines the contract
    for data operations, allowing for interchangeable storage backends
    (e.g., in-memory, database).
    """

    @abstractmethod
    def get_tasks(self, **filters: Any) -> List[Task]:
        """
        Retrieves a list of tasks, optionally filtered by given criteria.
        
        :param filters: Keyword arguments for filtering (e.g., state="inbox").
        :return: A list of Task objects.
        """
        pass

    @abstractmethod
    def add_task(self, task_data: Dict[str, Any]) -> Task:
        """
        Adds a new task to the storage.
        
        :param task_data: A dictionary containing the new task's data.
                          Must include 'title'.
        :return: The newly created Task object, including its ID.
        """
        pass

    @abstractmethod
    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Retrieves a single task by its ID.
        
        :param task_id: The ID of the task to retrieve.
        :return: A Task object if found, otherwise None.
        """
        pass

    @abstractmethod
    def update_task(self, task_id: int, update_data: Dict[str, Any]) -> Optional[Task]:
        """
        Updates an existing task.
        
        :param task_id: The ID of the task to update.
        :param update_data: A dictionary with the fields to update.
                           Must not include 'id', 'created_at'.
        :return: The updated Task object if found, otherwise None.
        """
        pass

    @abstractmethod
    def delete_task(self, task_id: int) -> bool:
        """
        Deletes a task.
        
        :param task_id: The ID of the task to delete.
        :return: True if deletion was successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_projects(self) -> List[str]:
        """
        Retrieves a list of all unique project names.
        
        :return: A list of strings, where each string is a unique project name.
        """
        pass
