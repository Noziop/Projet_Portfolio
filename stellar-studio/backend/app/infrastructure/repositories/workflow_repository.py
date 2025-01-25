# app/infrastructure/repositories/workflow_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from .base_repository import BaseRepository
from ..repositories.models.workflow import Workflow as WorkflowModel
from app.domain.models.workflow import Workflow, ProcessingStep, ProcessingStepType

class WorkflowRepository(BaseRepository[Workflow]):
    def __init__(self, db_session: Session):
        super().__init__(db_session)

    def _convert_steps_to_json(self, steps: List[ProcessingStep]) -> List[dict]:
        return [
            {
                'type': step.type.value,
                'order': step.order,
                'parameters': step.parameters,
                'description': step.description
            }
            for step in steps
        ]

    def _convert_json_to_steps(self, steps_json: List[dict]) -> List[ProcessingStep]:
        return [
            ProcessingStep(
                type=ProcessingStepType(step['type']),
                order=step['order'],
                parameters=step['parameters'],
                description=step['description']
            )
            for step in steps_json
        ]

    async def get_by_id(self, id: str) -> Optional[Workflow]:
        query = select(WorkflowModel).where(WorkflowModel.id == id)
        result = await self.db_session.execute(query)
        db_workflow = result.scalar_one_or_none()
        
        if db_workflow is None:
            return None
            
        return Workflow(
            id=db_workflow.id,
            name=db_workflow.name,
            description=db_workflow.description,
            steps=self._convert_json_to_steps(db_workflow.steps),
            is_default=db_workflow.is_default,
            target_type=db_workflow.target_type,
            required_filters=db_workflow.required_filters
        )

    async def list(self) -> List[Workflow]:
        query = select(WorkflowModel)
        result = await self.db_session.execute(query)
        db_workflows = result.scalars().all()
        
        return [
            Workflow(
                id=db_workflow.id,
                name=db_workflow.name,
                description=db_workflow.description,
                steps=self._convert_json_to_steps(db_workflow.steps),
                is_default=db_workflow.is_default,
                target_type=db_workflow.target_type,
                required_filters=db_workflow.required_filters
            )
            for db_workflow in db_workflows
        ]

    async def list_by_target_type(self, target_type: str) -> List[Workflow]:
        query = select(WorkflowModel).where(WorkflowModel.target_type == target_type)
        result = await self.db_session.execute(query)
        db_workflows = result.scalars().all()
        
        return [
            Workflow(
                id=db_workflow.id,
                name=db_workflow.name,
                description=db_workflow.description,
                steps=self._convert_json_to_steps(db_workflow.steps),
                is_default=db_workflow.is_default,
                target_type=db_workflow.target_type,
                required_filters=db_workflow.required_filters
            )
            for db_workflow in db_workflows
        ]

    async def create(self, workflow: Workflow) -> Workflow:
        db_workflow = WorkflowModel(
            id=str(uuid.uuid4()),
            name=workflow.name,
            description=workflow.description,
            steps=self._convert_steps_to_json(workflow.steps),
            is_default=workflow.is_default,
            target_type=workflow.target_type,
            required_filters=workflow.required_filters
        )
        
        self.db_session.add(db_workflow)
        await self.db_session.commit()
        await self.db_session.refresh(db_workflow)
        
        return workflow

    async def update(self, workflow: Workflow) -> Workflow:
        query = select(WorkflowModel).where(WorkflowModel.id == workflow.id)
        result = await self.db_session.execute(query)
        db_workflow = result.scalar_one_or_none()
        
        if db_workflow is None:
            raise ValueError(f"Workflow with id {workflow.id} not found")
            
        db_workflow.name = workflow.name
        db_workflow.description = workflow.description
        db_workflow.steps = self._convert_steps_to_json(workflow.steps)
        db_workflow.is_default = workflow.is_default
        db_workflow.target_type = workflow.target_type
        db_workflow.required_filters = workflow.required_filters
        
        await self.db_session.commit()
        await self.db_session.refresh(db_workflow)
        
        return workflow

    async def delete(self, id: str) -> bool:
        query = select(WorkflowModel).where(WorkflowModel.id == id)
        result = await self.db_session.execute(query)
        db_workflow = result.scalar_one_or_none()
        
        if db_workflow is None:
            return False
            
        await self.db_session.delete(db_workflow)
        await self.db_session.commit()
        
        return True
