from typing import Any, Dict

from pydantic import BaseModel, constr


class Item(BaseModel):
    path: constr(min_length=1)
    server_id: constr(min_length=1)
