from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import SearchLog
from schemas import SearchLogCreate, SearchLogOut

router = APIRouter(prefix="/search_logs", tags=["search_logs"])

@router.get("/", response_model=list[SearchLogOut])
def list_logs(db: Session = Depends(get_db), member_id: int | None = None, airport_id: int | None = None):
    q = db.query(SearchLog)
    if member_id is not None:
        q = q.filter(SearchLog.member_id == member_id)
    if airport_id is not None:
        q = q.filter(SearchLog.airport_id == airport_id)
    return q.order_by(SearchLog.search_time.desc()).all()

@router.post("/", response_model=SearchLogOut)
def create_log(payload: SearchLogCreate, db: Session = Depends(get_db)):
    obj = SearchLog(**payload.model_dump(exclude_unset=True))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj
