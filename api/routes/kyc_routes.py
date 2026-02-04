# routes/kyc_routes.py
from fastapi import APIRouter, HTTPException
from database.models import KYCVerificationRequest, KYCVerificationResponse
from services import customer_service

router = APIRouter(prefix="/kyc", tags=["KYC Verification"])

@router.post("/verify-phone", response_model=KYCVerificationResponse)
def verify_phone(request: KYCVerificationRequest):
    """Verify customer phone number exists in CRM"""
    return customer_service.verify_phone(request.phone)

@router.post("/verify-address", response_model=KYCVerificationResponse)
def verify_address(request: KYCVerificationRequest):
    """Verify customer address matches the phone number in records"""
    if not request.address:
        raise HTTPException(status_code=400, detail="Address is required for verification")
    
    return customer_service.verify_address(request.phone, request.address)

@router.post("/complete-verification/{customer_id}")
def complete_kyc_verification(customer_id: str):
    """Mark a customer as KYC verified after successful verification"""
    success = customer_service.mark_kyc_verified(customer_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return {
        "message": "KYC verification completed successfully",
        "customer_id": customer_id,
        "kyc_verified": True
    }

@router.get("/phone/{phone}")
def get_customer_by_phone(phone: str):
    """Get customer details by phone number"""
    customer = customer_service.get_by_phone(phone)
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found with this phone number")
    
    return customer