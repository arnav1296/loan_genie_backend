from typing import Optional, List, Dict
from database.connection import customers_collection
from database.models import Customer, KYCVerificationResponse, KYCVerificationRequest
from datetime import datetime

def get_all(skip: int = 0, limit: int = 100) -> List[Customer]:
    docs = customers_collection.find({}, {"_id": 0}).skip(skip).limit(limit)
    return [Customer(**doc) for doc in docs]

def get_by_id(customer_id: str) -> Optional[Customer]:
    doc = customers_collection.find_one({"customer_id": customer_id}, {"_id": 0})
    return Customer(**doc) if doc else None

def get_by_name(name: str) -> Optional[Customer]:
    doc = customers_collection.find_one(
        {"name": {"$regex": name, "$options": "i"}},
        {"_id": 0}
    )
    return Customer(**doc) if doc else None

def create(customer: Customer) -> Customer:
    customers_collection.insert_one(customer.model_dump())
    return customer

def update(customer_id: str, updates: dict) -> Optional[Customer]:
    result = customers_collection.update_one(
        {"customer_id": customer_id},
        {"$set": updates}
    )
    return get_by_id(customer_id) if result.modified_count > 0 else None

def delete(customer_id: str) -> bool:
    result = customers_collection.delete_one({"customer_id": customer_id})
    return result.deleted_count > 0

def get_by_phone(phone: str)-> Optional[Customer]:
        phone = phone.strip().replace('-','').replace(' ','').replace('+91','')
        doc = customers_collection.find_one({'phone': phone}, {'_id': 0})
        return Customer(**doc) if doc else None
    

def verify_phone(phone: str) -> KYCVerificationResponse:
    """Verify customer phone number exists in CRM"""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+91", "")
    customer = get_by_phone(phone)
    
    if customer:
        return KYCVerificationResponse(
            verified=True,
            customer_id=customer.customer_id,
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            message="Phone number verified successfully"
        )
    
    return KYCVerificationResponse(
        verified=False,
        message="Phone number not found in our records"
    )

def verify_address(phone: str, address: str) -> KYCVerificationResponse:
    """Verify customer address matches phone number"""
    phone = phone.strip().replace(" ", "").replace("-", "").replace("+91", "")
    provided_address = address.lower().strip()
    customer = get_by_phone(phone)
    
    if not customer:
        return KYCVerificationResponse(
            verified=False,
            message="Phone number not found in our records"
        )
    
    stored_address = customer.address.lower().strip()
    
    # Simple matching - checks if provided address is in stored address or vice versa
    if stored_address == provided_address or provided_address in stored_address or stored_address in provided_address:
        return KYCVerificationResponse(
            verified=True,
            customer_id=customer.customer_id,
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            message="Address verified successfully"
        )
    else:
        return KYCVerificationResponse(
            verified=False,
            phone=phone,
            address=customer.address,
            message=f"Address does not match. Our records show: {customer.address}"
        )

def mark_kyc_verified(customer_id: str) -> bool:
    """Mark a customer as KYC verified"""
    result = customers_collection.update_one(
        {"customer_id": customer_id},
        {
            "$set": {
                "kyc_verified": True,
                "updated_at": datetime.now()
            }
        }
    )
    return result.modified_count > 0    
        