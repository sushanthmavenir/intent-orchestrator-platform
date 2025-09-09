from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid


class ExpressionLanguage(str, Enum):
    TURTLE = "Turtle"
    JSON_LD = "JSON-LD"
    RDF_XML = "RDF-XML"


class ExpressionType(str, Enum):
    TURTLE_EXPRESSION = "TurtleExpression"
    JSON_LD_EXPRESSION = "JsonLdExpression"
    RDXML_EXPRESSION = "RdxmlExpression"


class LifecycleStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    PENDING = "pending"
    FULFILLED = "fulfilled"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TERMINATED = "terminated"


class Extensible(BaseModel):
    base_type: Optional[str] = Field(None, alias="@baseType")
    schema_location: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")


class TimePeriod(BaseModel):
    start_date_time: Optional[datetime] = Field(None, alias="startDateTime")
    end_date_time: Optional[datetime] = Field(None, alias="endDateTime")


class Expression(Extensible):
    expression_language: ExpressionLanguage = Field(alias="expressionLanguage")
    iri: Optional[str] = None
    
    class Config:
        use_enum_values = True


class TurtleExpression(Expression):
    expression_value: str = Field(alias="expressionValue")
    expression_language: ExpressionLanguage = Field(ExpressionLanguage.TURTLE, alias="expressionLanguage")
    type: ExpressionType = Field(ExpressionType.TURTLE_EXPRESSION, alias="@type")


class JsonLdExpression(Expression):
    expression_value: str = Field(alias="expressionValue")
    expression_language: ExpressionLanguage = Field(ExpressionLanguage.JSON_LD, alias="expressionLanguage")
    type: ExpressionType = Field(ExpressionType.JSON_LD_EXPRESSION, alias="@type")


class RdxmlExpression(Expression):
    expression_value: str = Field(alias="expressionValue")
    expression_language: ExpressionLanguage = Field(ExpressionLanguage.RDF_XML, alias="expressionLanguage")
    type: ExpressionType = Field(ExpressionType.RDXML_EXPRESSION, alias="@type")


class Entity(BaseModel):
    id: Optional[str] = None
    href: Optional[str] = None
    base_type: Optional[str] = Field(None, alias="@baseType")
    schema_location: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")


class EntityRef(Entity):
    name: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class IntentRef(EntityRef):
    pass


class IntentRefOrValue(BaseModel):
    id: Optional[str] = None
    href: Optional[str] = None
    creation_date: Optional[datetime] = Field(None, alias="creationDate")
    description: Optional[str] = None
    last_update: Optional[datetime] = Field(None, alias="lastUpdate")
    lifecycle_status: Optional[LifecycleStatus] = Field(None, alias="lifecycleStatus")
    name: Optional[str] = None
    status_change_date: Optional[datetime] = Field(None, alias="statusChangeDate")
    version: Optional[str] = "1.0"
    expression: Optional[Expression] = None
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    base_type: Optional[str] = Field(None, alias="@baseType")
    schema_location: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")
    referred_type: Optional[str] = Field(None, alias="@referredType")


class Intent(Entity):
    creation_date: Optional[datetime] = Field(None, alias="creationDate")
    description: Optional[str] = None
    last_update: Optional[datetime] = Field(None, alias="lastUpdate")
    lifecycle_status: Optional[LifecycleStatus] = Field(LifecycleStatus.CREATED, alias="lifecycleStatus")
    name: Optional[str] = None
    status_change_date: Optional[datetime] = Field(None, alias="statusChangeDate")
    version: Optional[str] = "1.0"
    expression: Optional[Expression] = None
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    
    @validator("id", pre=True, always=True)
    def generate_id(cls, v):
        return v or str(uuid.uuid4())
    
    @validator("creation_date", pre=True, always=True)
    def set_creation_date(cls, v):
        return v or datetime.utcnow()
    
    @validator("last_update", pre=True, always=True)
    def set_last_update(cls, v):
        return v or datetime.utcnow()
    
    @validator("status_change_date", pre=True, always=True)
    def set_status_change_date(cls, v):
        return v or datetime.utcnow()
    
    @validator("href", pre=True, always=True)
    def generate_href(cls, v, values):
        if not v and "id" in values:
            return f"/tmf-api/intent/v4/intent/{values['id']}"
        return v


class IntentCreate(BaseModel):
    creation_date: Optional[datetime] = Field(None, alias="creationDate")
    description: Optional[str] = None
    last_update: Optional[datetime] = Field(None, alias="lastUpdate")
    lifecycle_status: Optional[LifecycleStatus] = Field(LifecycleStatus.CREATED, alias="lifecycleStatus")
    name: str
    status_change_date: Optional[datetime] = Field(None, alias="statusChangeDate")
    version: Optional[str] = "1.0"
    expression: Expression
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    base_type: Optional[str] = Field(None, alias="@baseType")
    schema_location: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")


class IntentUpdate(BaseModel):
    creation_date: Optional[datetime] = Field(None, alias="creationDate")
    description: Optional[str] = None
    last_update: Optional[datetime] = Field(None, alias="lastUpdate")
    lifecycle_status: Optional[LifecycleStatus] = Field(None, alias="lifecycleStatus")
    name: Optional[str] = None
    status_change_date: Optional[datetime] = Field(None, alias="statusChangeDate")
    version: Optional[str] = None
    expression: Optional[Expression] = None
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    base_type: Optional[str] = Field(None, alias="@baseType")
    schema_location: Optional[str] = Field(None, alias="@schemaLocation")


class IntentReport(Entity):
    creation_date: Optional[datetime] = Field(None, alias="creationDate")
    description: Optional[str] = None
    name: Optional[str] = None
    expression: Optional[Expression] = None
    intent: IntentRefOrValue
    valid_for: Optional[TimePeriod] = Field(None, alias="validFor")
    
    @validator("id", pre=True, always=True)
    def generate_id(cls, v):
        return v or str(uuid.uuid4())
    
    @validator("creation_date", pre=True, always=True)
    def set_creation_date(cls, v):
        return v or datetime.utcnow()
    
    @validator("href", pre=True, always=True)
    def generate_href(cls, v, values):
        if not v and "id" in values and hasattr(values.get("intent"), "id"):
            intent_id = values["intent"].id if hasattr(values["intent"], "id") else "unknown"
            return f"/tmf-api/intent/v4/intent/{intent_id}/intentReport/{values['id']}"
        return v


class EventSubscription(BaseModel):
    id: str
    callback: str
    query: Optional[str] = None


class EventSubscriptionInput(BaseModel):
    callback: str
    query: Optional[str] = None


class EventPayload(BaseModel):
    event_id: Optional[str] = Field(None, alias="eventId")
    event_time: Optional[datetime] = Field(None, alias="eventTime")
    event_type: Optional[str] = Field(None, alias="eventType")
    correlation_id: Optional[str] = Field(None, alias="correlationId")
    domain: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    time_occurred: Optional[datetime] = Field(None, alias="timeOcurred")


class IntentCreateEventPayload(BaseModel):
    intent: Intent


class IntentCreateEvent(EventPayload):
    event: IntentCreateEventPayload


class IntentChangeEventPayload(BaseModel):
    intent: Intent


class IntentChangeEvent(EventPayload):
    event: IntentChangeEventPayload


class IntentDeleteEventPayload(BaseModel):
    intent: Intent


class IntentDeleteEvent(EventPayload):
    event: IntentDeleteEventPayload


class IntentReportCreateEventPayload(BaseModel):
    intent_report: IntentReport = Field(alias="intentReport")


class IntentReportCreateEvent(EventPayload):
    event: IntentReportCreateEventPayload


class IntentReportChangeEventPayload(BaseModel):
    intent_report: IntentReport = Field(alias="intentReport")


class IntentReportChangeEvent(EventPayload):
    event: IntentReportChangeEventPayload


class IntentReportDeleteEventPayload(BaseModel):
    intent_report: IntentReport = Field(alias="intentReport")


class IntentReportDeleteEvent(EventPayload):
    event: IntentReportDeleteEventPayload


class Error(BaseModel):
    code: str
    reason: str
    message: Optional[str] = None
    status: Optional[str] = None
    reference_error: Optional[str] = Field(None, alias="referenceError")
    base_type: Optional[str] = Field(None, alias="@baseType")
    schema_location: Optional[str] = Field(None, alias="@schemaLocation")
    type: Optional[str] = Field(None, alias="@type")


class ListResponse(BaseModel):
    items: List[Dict[str, Any]]
    total_count: int
    result_count: int
    offset: Optional[int] = 0
    limit: Optional[int] = None