"""
Seeder: runs on app startup to ensure default roles & permissions exist.
Safe to re-run — uses get-or-create pattern.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.role import Role, Permission
from app.database import AsyncSessionLocal

DEFAULT_ROLES = ["admin", "user"]
DEFAULT_PERMISSIONS = ["read", "write", "delete"]

# role → permissions mapping
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "delete"],
    "user":  ["read"],
}


async def seed_roles_and_permissions():
    async with AsyncSessionLocal() as db:
        # 1. Create permissions
        perm_map: dict[str, Permission] = {}
        for pname in DEFAULT_PERMISSIONS:
            result = await db.execute(select(Permission).where(Permission.name == pname))
            perm = result.scalars().first()
            if not perm:
                perm = Permission(name=pname)
                db.add(perm)
                await db.flush()
            perm_map[pname] = perm

        # 2. Create roles and assign permissions
        for rname in DEFAULT_ROLES:
            result = await db.execute(select(Role).where(Role.name == rname))
            role = result.scalars().first()
            if not role:
                role = Role(name=rname)
                db.add(role)
                await db.flush()

            # Assign permissions
            for pname in ROLE_PERMISSIONS.get(rname, []):
                perm = perm_map[pname]
                if perm not in role.permissions:
                    role.permissions.append(perm)

        await db.commit()
        print("✅  Seeded: roles (admin, user) + permissions (read, write, delete)")
