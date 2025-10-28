from fastapi import Depends
from .db import get_db
from .auth import get_current_user, require_admin

db_dep = Depends(get_db)
user_dep = Depends(get_current_user)
admin_dep = Depends(require_admin)
