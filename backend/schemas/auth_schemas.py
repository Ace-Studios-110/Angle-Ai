from pydantic import BaseModel, EmailStr, Field

class SignUpSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    
class SignInSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    
class ResetPasswordSchema(BaseModel):
    email: EmailStr
    
class RefreshTokenSchema(BaseModel):
    refresh_token: str