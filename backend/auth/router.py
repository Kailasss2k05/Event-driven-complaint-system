"""Authentication router with signup and login endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from backend.auth.schemas import UserCreate, Token, UserResponse
from backend.auth.security import hash_password, verify_password
from backend.auth.jwt_handler import create_access_token
from backend.db import database

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    """Register a new user."""
    # Check if user already exists
    existing_user = database.get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = database.get_user_by_email(user.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password and create user
    hashed_password = hash_password(user.password)
    user_id = database.create_user(
        user.username, 
        user.email, 
        hashed_password, 
        user.role.value if user.role else "user", 
        user.department_name
    )
    
    # Get the created user to return with role and department
    created_user = database.get_user_by_id(user_id)
    
    return {
        "id": created_user["id"],
        "username": created_user["username"],
        "email": created_user["email"],
        "role": created_user["role"],
        "department_name": created_user["department_name"]
    }

@router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    # Get user from database
    user = database.get_user_by_username(form_data.username)
    
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["username"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(database.get_current_user)):
    """Get current logged-in user information."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "role": current_user["role"],
        "department_name": current_user["department_name"]
    }
