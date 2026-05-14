"""Backlog local (épicos, histórias, tarefas) e exportação para `.squad/backlog.json`."""

from __future__ import annotations

from core.backlog.backlog_exporter import export_backlog_to_project_file
from core.backlog.backlog_service import (
    assign_task_to_agent,
    create_epic,
    create_story,
    create_task,
    list_epics,
    list_stories,
    list_tasks,
    update_epic_status,
    update_story_status,
    update_task_status,
)

__all__ = [
    "assign_task_to_agent",
    "create_epic",
    "create_story",
    "create_task",
    "export_backlog_to_project_file",
    "list_epics",
    "list_stories",
    "list_tasks",
    "update_epic_status",
    "update_story_status",
    "update_task_status",
]
