from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from security import get_current_member
from models import SearchLog
from schemas import SearchLogCreate, SearchLogOut
from datetime import timezone

router = APIRouter(prefix="/search_logs", tags=["search_logs"])


# ======================================================
# Helper: require admin
# ======================================================
def require_admin(current_user = Depends(get_current_member)):
    if getattr(current_user, "platform", "") != "admin":
        raise HTTPException(403, "Admin access required.")
    return current_user


# ======================================================
# ADMIN — LIST ALL SEARCH LOGS
# ======================================================
@router.get("/", response_model=list[SearchLogOut], dependencies=[Depends(require_admin)])
def list_logs(
    db: Session = Depends(get_db),
    member_id: int | None = None,
    airport_id: int | None = None,
):
    q = db.query(SearchLog)

    if member_id is not None:
        q = q.filter(SearchLog.member_id == member_id)
    if airport_id is not None:
        q = q.filter(SearchLog.airport_id == airport_id)

    return q.order_by(SearchLog.search_time.desc()).all()


# ======================================================
# INTERNAL — API SHOULD INSERT SEARCH LOGS
# Not directly exposed to mobile clients
# ======================================================
@router.post("/", response_model=SearchLogOut, dependencies=[Depends(require_admin)])
def create_log(
    payload: SearchLogCreate,
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)

    for field in ("search_time", "desired_start", "desired_end"):
        dt = data.get(field)
        if dt is not None:
            if dt.tzinfo is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"{field} must include timezone information (UTC)",
                )
            data[field] = dt.astimezone(timezone.utc)

    obj = SearchLog(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


