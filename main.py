"""
Main FastAPI application with authentication and college suggestion features
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.routes import router as college_router
from app.auth_routes import auth_router, user_router, admin_router
from app.database import engine, Base

# Create database tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("Application shutting down...")

# Create FastAPI app
app = FastAPI(
    title="College Connect - College Suggester API",
    description="""
    A comprehensive API for college suggestions and admissions data with role-based authentication.
    
    Features:
    - College recommendation based on CET rank and preferences
    - Branch normalization (e.g., Computer Science → CSE)
    - Role-based access control (RBAC)
    - User authentication and management
    - Admin panel for user and role management
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(college_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to College Connect API v2.0",
        "features": [
            "College recommendations with CET rank filtering",
            "Branch normalization (CS, CSE, IT, etc.)",
            "Role-based authentication system",
            "User management and admin panel",
            "Comprehensive college and branch data"
        ],
        "docs": "/docs",
        "auth_endpoints": {
            "register": "/auth/register",
            "login": "/auth/login",
            "profile": "/auth/me"
        },
        "main_endpoints": {
            "recommend": "/api/v1/recommend",
            "branches": "/api/v1/available-branches",
            "regions": "/api/v1/available-regions"
        }
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
