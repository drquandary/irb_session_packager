from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .routes import router

app = FastAPI(title="IRB and Session Packager")

# Set up templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# Mount static files (if any)
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routes under /api
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    return templates.TemplateResponse("index.html", {"request": {}})


@app.get("/api/")
async def api_root():
    """API root endpoint providing basic project information."""
    return {"detail": "IRB and Session Packager API"}
