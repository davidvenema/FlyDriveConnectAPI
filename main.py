from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import airports, rates, cars, members, bookings, subscriptions, search_logs

app = FastAPI(title="FlyDrive API")

# CORS (loose for now; tighten later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# Routers
app.include_router(airports.router)
app.include_router(rates.router)
app.include_router(cars.router)
app.include_router(members.router)
app.include_router(bookings.router)
app.include_router(subscriptions.router)
app.include_router(search_logs.router)

@app.get("/")
def root():
    return {"ok": True, "service": "FlyDrive API"}
