from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routes import router as college_router
from app.auth_routes import auth_router, user_router, admin_router
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="Maharashtra CAP College Recommender")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  #  Angular dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Include routes
app.include_router(college_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
