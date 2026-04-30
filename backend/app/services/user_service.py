from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..models.schemas import UserCreate, User
from ..core.security import get_password_hash, verify_password, create_access_token

logger = logging.getLogger(__name__)


class UserService:
    """用户服务 - 简化版，使用内存存储"""
    
    def __init__(self):
        self.users: Dict[str, Dict[str, Any]] = {}
        self.user_id_counter = 1
    
    async def create_user(self, user_in: UserCreate) -> User:
        """创建新用户"""
        if user_in.email in self.users:
            raise ValueError("该邮箱已被注册")
        
        hashed_password = get_password_hash(user_in.password)
        
        user = {
            "id": self.user_id_counter,
            "email": user_in.email,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.now()
        }
        
        self.users[user_in.email] = user
        self.user_id_counter += 1
        
        logger.info(f"Created user: {user_in.email}")
        
        return User(
            id=user["id"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """验证用户"""
        user = self.users.get(email)
        
        if not user:
            return None
        
        if not verify_password(password, user["hashed_password"]):
            return None
        
        if not user["is_active"]:
            return None
        
        return User(
            id=user["id"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        user = self.users.get(email)
        
        if not user:
            return None
        
        return User(
            id=user["id"],
            email=user["email"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        )
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        for user in self.users.values():
            if user["id"] == user_id:
                return User(
                    id=user["id"],
                    email=user["email"],
                    is_active=user["is_active"],
                    created_at=user["created_at"]
                )
        return None
    
    async def login_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """用户登录，返回令牌"""
        user = await self.authenticate_user(email, password)
        
        if not user:
            return None
        
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email
            }
        }


user_service = UserService()
