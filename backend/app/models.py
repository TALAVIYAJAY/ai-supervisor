import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from .config import settings

class Supervisor(SQLModel, table=True):
    __tablename__ = "supervisors"
    
    id: str = Field(default_factory=lambda: f"sup_{uuid.uuid4().hex[:8]}", primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)
    base_instruction: str = Field(default="")
    available_tools: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    wake_up_policy: str = Field(default="balanced")
    model_name: str = Field(default_factory=lambda: settings.GEMINI_MODEL)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrderRun(SQLModel, table=True):
    __tablename__ = "order_runs"
    
    id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:10]}", primary_key=True)
    order_id: str = Field(index=True)
    supervisor_id: str = Field(foreign_key="supervisors.id", index=True)
    status: str = Field(default="ACTIVE", index=True)
    
    order_context: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    compact_memory: str = Field(default="")
    runtime_instructions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    next_wake_time: Optional[datetime] = Field(default=None)
    last_wake_time: Optional[datetime] = Field(default=None)
    
    final_summary: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ActivityLog(SQLModel, table=True):
    __tablename__ = "activity_logs"
    
    id: str = Field(default_factory=lambda: f"log_{uuid.uuid4().hex[:12]}", primary_key=True)
    run_id: str = Field(foreign_key="order_runs.id", index=True)
    log_type: str = Field(index=True)
    trigger_source: str = Field(default="SIGNAL")
    
    title: str
    details: Optional[str] = Field(default=None)
    metadata_payload: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
