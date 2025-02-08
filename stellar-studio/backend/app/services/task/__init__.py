from .service import TaskService, download_fits

task_service = TaskService()

__all__ = ['task_service',
           'download_fits']
