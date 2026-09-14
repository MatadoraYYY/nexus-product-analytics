from pydantic import BaseModel

class ErrorBody(BaseModel):
    code:str
    message:str
    request_id:str

class OverviewResponse(BaseModel):
    period:str
    dau:int
    mau:int
    stickiness:float|None
    activation_rate:float|None
    d30_retention:float|None
    mrr:float
    churn:float|None
    arpu:float|None
    arppu:float|None
    ltv:float|None
    cac:float|None
    ltv_cac:float|None
