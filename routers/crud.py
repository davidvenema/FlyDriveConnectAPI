from sqlalchemy.orm import Session
from typing import Type, Any

def create_record(db: Session, model: Type[Any], data: dict):
    obj = model(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def update_record(db: Session, obj: Any, data: dict):
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj
