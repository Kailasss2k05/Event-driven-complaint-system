"""OAuth2 password bearer scheme for FastAPI."""
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
