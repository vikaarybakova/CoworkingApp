from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routers import coworkings, bookings, users, admin
from app.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Coworking App API", version="1.0.0")

app.include_router(coworkings.router)
app.include_router(bookings.router)
app.include_router(users.router)
app.include_router(admin.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return {"message": "Coworking API is running", "version": "1.0.0"}