from fastapi import APIRouter, HTTPException

from backend.app.data.repository import get_merchant


router = APIRouter(prefix="/merchants", tags=["Merchants"])


@router.get("/{merchant_id}")
def get_merchant_details(merchant_id: str):

    merchant = get_merchant(merchant_id)

    if merchant is None:
        raise HTTPException(
            status_code=404,
            detail="Merchant not found"
        )

    return merchant
