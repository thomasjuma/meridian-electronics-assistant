import os
from fastapi.middleware.cors import CORSMiddleware
from routes import app
from database import Base, engine
from dotenv import load_dotenv

load_dotenv(override=True)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Startup event: create tables automatically
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    print("Database and tables created!")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)