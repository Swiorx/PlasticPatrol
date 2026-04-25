from pydantic import BaseModel, Field

class PlasticReportCreate(BaseModel):
    lat: float = Field(..., example=6.44, description="Latitudinea punctului (între -90 și 90)")
    lon: float = Field(..., example=3.40, description="Longitudinea punctului (între -180 și 180)")
