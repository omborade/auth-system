from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str


class AssignRoleRequest(BaseModel):
    user_id: int
    role_name: str


class RoleResponse(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}
