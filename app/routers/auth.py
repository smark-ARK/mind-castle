from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import IntegrityError


from app.schemas import UserBase, UserCreate, ResponseToken, UserResponse
from app.models import User
from app.database import get_db
from app.utils import hash_password, verify_password
from app.oauth2 import create_access_token, create_refresh_token, verify_refresh_token


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    user.password = hash_password(plain_password=user.password)
    try:
        new_user = User(**user.model_dump())
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError as e:
        raise HTTPException(
            detail="The User with this name or email already exists",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        raise HTTPException(detail=str(e), status_code=status.HTTP_400_BAD_REQUEST)
    return new_user


@router.post("/login", response_model=ResponseToken)
def login(
    response: Response,
    user_cred: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == user_cred.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials"
        )
    if not verify_password(user_cred.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="invalid credentials"
        )
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )
    refresh_token = create_refresh_token(
        data={"user_id": user.id, "username": user.username}
    )

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="none",
        secure=True,
        domain=None,
    )  # set HttpOnly cookie in response

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh_token(request: Request, response: Response):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token found in cookies")

    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    new_access_token = create_access_token(data=payload)
    refresh_token = create_refresh_token(data={"user_id": payload})

    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return {"access_token": new_access_token, "token_type": "bearer"}
