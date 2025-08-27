from fastapi import FastAPI
from .routes import router


app = FastAPI(title="IRB and Session Packager")

# Include API routes under /api
app.include_router(router, prefix='/api')


@app.get('/')
async def root():
    """Root endpoint providing basic project information."""
    return {'detail': 'IRB and Session Packager API'}
