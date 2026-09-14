from pydantic import BaseModel


class Merchant(BaseModel):
    merchant_id: str
    name: str
    category: str
    average_transaction_amount: float
    transaction_count: int
    fraud_reports: int = 0
    risk_level: str = "LOW"
