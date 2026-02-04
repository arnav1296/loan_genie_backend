# database/models.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class Customer(BaseModel):
    customer_id: str
    name: str
    phone: str = Field(..., pattern=r'^\d{10}$')  # 10 digit phone
    email: Optional[str] = None
    address: str
    city: str
    state: str
    pincode: str = Field(..., pattern=r'^\d{6}$')  # 6 digit pincode
    date_of_birth: Optional[str] = None
    age: int
    monthly_income: float
    employment_status: str  # employed, self-employed, retired, student
    employer_name: Optional[str] = None
    credit_score: int
    existing_loan_amount: float
    existing_loan_type: Optional[str] = None
    pre_approved_limit: float
    kyc_verified: bool = False

class KYCVerificationRequest(BaseModel):
    phone: str = Field(..., pattern=r'^\d{10}$')
    address: Optional[str] = None

class KYCVerificationResponse(BaseModel):
    verified: bool
    customer_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    message: str

class LoanOffer(BaseModel):
    offer_id: str
    loan_type: str
    min_amount: float
    max_amount: float
    interest_rate: float
    tenure_months: int
    processing_fee_percentage: float
    description: str