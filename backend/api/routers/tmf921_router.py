from fastapi import APIRouter, HTTPException, Query, Path, Header, Depends
from fastapi.responses import Response
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from ..models.tmf921_models import (
    Intent, IntentCreate, IntentUpdate, IntentReport,
    EventSubscription, EventSubscriptionInput, Error,
    ListResponse
)
from ..database.database import IntentDatabase


router = APIRouter(prefix="/tmf-api/intent/v4", tags=["TMF921 Intent Management"])
db = IntentDatabase()


def get_database():
    return db


@router.post("/intent", response_model=Intent, status_code=201)
async def create_intent(
    intent: IntentCreate,
    database: IntentDatabase = Depends(get_database)
):
    """Create a new Intent"""
    try:
        intent_id = str(uuid.uuid4())
        intent_dict = intent.dict(by_alias=True, exclude_unset=True)
        intent_dict["id"] = intent_id
        intent_dict["href"] = f"/tmf-api/intent/v4/intent/{intent_id}"
        
        if "creation_date" not in intent_dict:
            intent_dict["creation_date"] = datetime.utcnow()
        if "last_update" not in intent_dict:
            intent_dict["last_update"] = datetime.utcnow()
        if "status_change_date" not in intent_dict:
            intent_dict["status_change_date"] = datetime.utcnow()
        
        created_intent = database.create_intent(intent_dict)
        return Intent(**created_intent)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent", response_model=List[Intent])
async def list_intents(
    fields: Optional[str] = Query(None, description="Comma-separated properties to be provided in response"),
    offset: Optional[int] = Query(0, description="Requested index for start of resources"),
    limit: Optional[int] = Query(None, description="Requested number of resources"),
    database: IntentDatabase = Depends(get_database)
):
    """List or find Intent objects"""
    try:
        filters = {}
        
        result = database.list_intents(offset=offset, limit=limit, filters=filters)
        
        intents = []
        for intent_data in result["items"]:
            try:
                intents.append(Intent(**intent_data))
            except Exception as e:
                continue
        
        response = Response(
            content=ListResponse(
                items=[intent.dict(by_alias=True) for intent in intents],
                total_count=result["total_count"],
                result_count=result["result_count"],
                offset=offset,
                limit=limit
            ).json(),
            media_type="application/json"
        )
        
        response.headers["X-Total-Count"] = str(result["total_count"])
        response.headers["X-Result-Count"] = str(result["result_count"])
        
        return intents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{id}", response_model=Intent)
async def retrieve_intent(
    id: str = Path(..., description="Identifier of the Intent"),
    fields: Optional[str] = Query(None, description="Comma-separated properties to provide in response"),
    database: IntentDatabase = Depends(get_database)
):
    """Retrieve an Intent by ID"""
    try:
        intent_data = database.get_intent(id)
        if not intent_data:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        return Intent(**intent_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/intent/{id}", response_model=Intent)
async def update_intent(
    intent_update: IntentUpdate,
    id: str = Path(..., description="Identifier of the Intent"),
    database: IntentDatabase = Depends(get_database)
):
    """Update an Intent partially"""
    try:
        existing_intent = database.get_intent(id)
        if not existing_intent:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        update_dict = intent_update.dict(by_alias=True, exclude_unset=True)
        update_dict["last_update"] = datetime.utcnow()
        update_dict["status_change_date"] = datetime.utcnow()
        
        updated_intent = database.update_intent(id, update_dict)
        return Intent(**updated_intent)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/intent/{id}", status_code=204)
async def delete_intent(
    id: str = Path(..., description="Identifier of the Intent"),
    database: IntentDatabase = Depends(get_database)
):
    """Delete an Intent"""
    try:
        success = database.delete_intent(id)
        if not success:
            raise HTTPException(status_code=404, detail="Intent not found")
        
        return Response(status_code=204)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{intent_id}/intentReport", response_model=List[IntentReport])
async def list_intent_reports(
    intent_id: str = Path(..., description="Identifier of the parent Intent entity"),
    fields: Optional[str] = Query(None, description="Comma-separated properties to be provided in response"),
    offset: Optional[int] = Query(0, description="Requested index for start of resources"),
    limit: Optional[int] = Query(None, description="Requested number of resources"),
    database: IntentDatabase = Depends(get_database)
):
    """List or find IntentReport objects"""
    try:
        result = database.list_intent_reports(intent_id, offset=offset, limit=limit)
        
        reports = []
        for report_data in result["items"]:
            try:
                reports.append(IntentReport(**report_data))
            except Exception:
                continue
        
        response = Response(
            content=ListResponse(
                items=[report.dict(by_alias=True) for report in reports],
                total_count=result["total_count"],
                result_count=result["result_count"],
                offset=offset,
                limit=limit
            ).json(),
            media_type="application/json"
        )
        
        response.headers["X-Total-Count"] = str(result["total_count"])
        response.headers["X-Result-Count"] = str(result["result_count"])
        
        return reports
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/intent/{intent_id}/intentReport/{id}", response_model=IntentReport)
async def retrieve_intent_report(
    intent_id: str = Path(..., description="Identifier of the parent Intent entity"),
    id: str = Path(..., description="Identifier of the IntentReport"),
    fields: Optional[str] = Query(None, description="Comma-separated properties to provide in response"),
    database: IntentDatabase = Depends(get_database)
):
    """Retrieve an IntentReport by ID"""
    try:
        report_data = database.get_intent_report(intent_id, id)
        if not report_data:
            raise HTTPException(status_code=404, detail="IntentReport not found")
        
        return IntentReport(**report_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/intent/{intent_id}/intentReport/{id}", status_code=204)
async def delete_intent_report(
    intent_id: str = Path(..., description="Identifier of the parent Intent entity"),
    id: str = Path(..., description="Identifier of the IntentReport"),
    database: IntentDatabase = Depends(get_database)
):
    """Delete an IntentReport"""
    try:
        success = database.delete_intent_report(intent_id, id)
        if not success:
            raise HTTPException(status_code=404, detail="IntentReport not found")
        
        return Response(status_code=204)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/hub", response_model=EventSubscription, status_code=201)
async def register_listener(
    data: EventSubscriptionInput,
    database: IntentDatabase = Depends(get_database)
):
    """Register a listener"""
    try:
        subscription_id = str(uuid.uuid4())
        subscription_data = {
            "id": subscription_id,
            "callback": data.callback,
            "query": data.query
        }
        
        created_subscription = database.create_subscription(subscription_data)
        return EventSubscription(**created_subscription)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/hub/{id}", status_code=204)
async def unregister_listener(
    id: str = Path(..., description="The id of the registered listener"),
    database: IntentDatabase = Depends(get_database)
):
    """Unregister a listener"""
    try:
        success = database.delete_subscription(id)
        if not success:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        return Response(status_code=204)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/listener/intentCreateEvent", status_code=201)
async def listen_to_intent_create_event(data: Dict[str, Any]):
    """Client listener for IntentCreateEvent"""
    return {"status": "received"}


@router.post("/listener/intentChangeEvent", status_code=201)
async def listen_to_intent_change_event(data: Dict[str, Any]):
    """Client listener for IntentChangeEvent"""
    return {"status": "received"}


@router.post("/listener/intentDeleteEvent", status_code=201)
async def listen_to_intent_delete_event(data: Dict[str, Any]):
    """Client listener for IntentDeleteEvent"""
    return {"status": "received"}


@router.post("/listener/intentReportCreateEvent", status_code=201)
async def listen_to_intent_report_create_event(data: Dict[str, Any]):
    """Client listener for IntentReportCreateEvent"""
    return {"status": "received"}


@router.post("/listener/intentReportChangeEvent", status_code=201)
async def listen_to_intent_report_change_event(data: Dict[str, Any]):
    """Client listener for IntentReportChangeEvent"""
    return {"status": "received"}


@router.post("/listener/intentReportDeleteEvent", status_code=201)
async def listen_to_intent_report_delete_event(data: Dict[str, Any]):
    """Client listener for IntentReportDeleteEvent"""
    return {"status": "received"}