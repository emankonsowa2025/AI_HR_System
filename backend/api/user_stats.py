from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/stats")
def get_user_stats(db: Session = Depends(get_db)):
    """Return total user count and sample usernames"""
    total = db.query(User).count()
    # Get up to 5 most recent users
    users = db.query(User).order_by(User.created_at.desc()).limit(5).all()
    usernames = [u.username for u in users]
    return {"total_users": total, "recent_usernames": usernames}
