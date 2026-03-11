"""
Router for handling payments.
"""
from fastapi import APIRouter
from ..services.payment_service import create_payment, handle_webhook

router = APIRouter()


@router.post("/create")
def create_payment_endpoint():
    """
    Endpoint to initialize a new payment.
    """
    return create_payment()


@router.post("/webhook")
def payment_webhook(payload: dict):
    """
    Endpoint to receive payment webhook notifications.
    """
    return handle_webhook(payload)
