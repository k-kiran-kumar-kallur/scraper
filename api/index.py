from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import uvicorn
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Web Scraping MCP")

# Store for scraped data and jobs
scrape_jobs = {}
scrape_results = {}
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScrapeRequest(BaseModel):
    url: str
    selector: str = "body"
    job_name: str

def perform_scrape(job_id: str, url: str, selector: str):
    try:
        scrape_jobs[job_id]["status"] = "running"
        response = requests.get(url, headers={"User-Agent": "MCP Scraper 1.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select(selector)
        scrape_results[job_id] = [item.text for item in results]
        scrape_jobs[job_id]["status"] = "completed"
    except Exception as e:
        scrape_jobs[job_id]["status"] = "failed"
        scrape_jobs[job_id]["error"] = str(e)

@app.post("/scrape")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    job_id = f"{request.job_name}_{datetime.now().timestamp()}"
    scrape_jobs[job_id] = {
        "url": request.url,
        "selector": request.selector,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    background_tasks.add_task(perform_scrape, job_id, request.url, request.selector)
    return {"job_id": job_id, "status": "pending"}

@app.get("/jobs")
async def list_jobs():
    return scrape_jobs

@app.get("/results/{job_id}")
async def get_results(job_id: str):
    if job_id not in scrape_jobs:
        return {"error": "Job not found"}
    
    result = {
        "job": scrape_jobs[job_id],
        "data": scrape_results.get(job_id, [])
    }
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
