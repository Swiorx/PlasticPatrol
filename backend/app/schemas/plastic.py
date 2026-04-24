from pydantic import BaseModel

class PlasticReportCreate(BaseModel):
    lat: float
    lon: float
