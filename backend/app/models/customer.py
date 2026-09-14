from pydantic import BaseModel
from typing import List


class Customer(BaseModel):
    customer_id: str
    name: str
    account_age_days: int
    average_transaction_amount: float
    transaction_count: int
    known_devices: List[str]
    known_locations: List[str]
    previous_fraud_reports: int = 0