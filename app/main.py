from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from .database import engine
from app import models
from app.routers import auth, notes


app = FastAPI()

# models.Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(notes.router)
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://*",
    "http://127.0.0.1:8000",
    "https://simple-social-smark.netlify.app",
    "http://127.0.0.1:3000",
    "localhost:3000",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Hello World!"}
