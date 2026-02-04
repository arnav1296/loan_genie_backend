from crewai.tools import tool
import requests
from typing import Dict, Any
import json

API_BASE_URL = "http://localhost:8000/kyc"

@tool("Verify Phone Number")
def verify_phone(phone: str) -> str:
    """
    Use this tool to verify if a customer's phone number exists in the CRM system.
    This is the first step in KYC verification.
    
    Args:
        phone: 10-digit phone number to verify (e.g., "9876543210")
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/verify-phone",
            json={"phone": phone},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("verified", False):
            customer_data = data.get("customer_data", {})
            result = f"✓ Phone number verified successfully!\n\n"
            result += f"Customer Details:\n"
            result += f"  - Name: {customer_data.get('name', 'N/A')}\n"
            result += f"  - Customer ID: {customer_data.get('customer_id', 'N/A')}\n"
            result += f"  - City: {customer_data.get('city', 'N/A')}, {customer_data.get('state', 'N/A')}\n"
            result += f"  - KYC Status: {'Verified' if customer_data.get('kyc_verified') else 'Not Verified'}\n"
            result += f"\nMessage: {data.get('message', '')}"
            return result
        else:
            return f"✗ Phone verification failed\n\nMessage: {data.get('message', 'Phone number not found in our records')}"
            
    except requests.RequestException as e:
        return f"Error verifying phone number: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@tool("Verify Address")
def verify_address(phone: str, address: str) -> str:
    """
    Use this tool to verify if the provided address matches the customer's 
    registered address in the CRM system. Use this after phone verification.
    
    Args:
        phone: 10-digit phone number (e.g., "9876543210")
        address: Full address to verify against CRM records
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/verify-address",
            json={
                "phone": phone,
                "address": address
            },
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("verified", False):
            result = f"✓ Address verified successfully!\n\n"
            result += f"Message: {data.get('message', '')}\n"
            result += f"Match Score: {data.get('match_score', 'N/A')}\n"
            
            if 'registered_address' in data:
                result += f"\nRegistered Address: {data['registered_address']}"
            
            return result
        else:
            result = f"✗ Address verification failed\n\n"
            result += f"Message: {data.get('message', '')}\n"
            
            if 'registered_address' in data:
                result += f"\nRegistered Address on file: {data['registered_address']}\n"
                result += f"Provided Address: {address}"
            
            return result
            
    except requests.RequestException as e:
        return f"Error verifying address: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@tool("Complete KYC Verification")
def complete_kyc(customer_id: str) -> str:
    """
    Use this tool to mark a customer as KYC verified after successful 
    phone and address verification. This is the final step in the KYC process.
    
    Args:
        customer_id: The customer's unique ID from the CRM system
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/complete-verification/{customer_id}",
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        result = f"✓ KYC Verification Completed!\n\n"
        result += f"Customer ID: {data.get('customer_id', 'N/A')}\n"
        result += f"KYC Status: {'Verified' if data.get('kyc_verified') else 'Pending'}\n"
        result += f"Message: {data.get('message', '')}"
        
        return result
            
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return f"✗ Customer not found with ID: {customer_id}"
        return f"Error completing KYC verification: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@tool("Get Customer by Phone")
def get_customer_by_phone(phone: str) -> str:
    """
    Use this tool to retrieve full customer details using their phone number.
    Useful for checking customer information and KYC status.
    
    Args:
        phone: 10-digit phone number (e.g., "9876543210")
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/phone/{phone}",
            timeout=10
        )
        response.raise_for_status()
        
        customer = response.json()
        
        result = f"Customer Information:\n\n"
        result += f"Customer ID: {customer.get('customer_id', 'N/A')}\n"
        result += f"Name: {customer.get('name', 'N/A')}\n"
        result += f"Phone: {customer.get('phone', 'N/A')}\n"
        result += f"Email: {customer.get('email', 'N/A')}\n"
        result += f"Address: {customer.get('address', 'N/A')}\n"
        result += f"City: {customer.get('city', 'N/A')}, {customer.get('state', 'N/A')} - {customer.get('pincode', 'N/A')}\n"
        result += f"Age: {customer.get('age', 'N/A')}\n"
        result += f"Monthly Income: ₹{customer.get('monthly_income', 0):,.0f}\n"
        result += f"Employment: {customer.get('employment_status', 'N/A')}\n"
        
        if customer.get('employer_name'):
            result += f"Employer: {customer.get('employer_name')}\n"
        
        result += f"Credit Score: {customer.get('credit_score', 'N/A')}\n"
        result += f"Existing Loan Amount: ₹{customer.get('existing_loan_amount', 0):,.0f}\n"
        
        if customer.get('existing_loan_type'):
            result += f"Existing Loan Type: {customer.get('existing_loan_type')}\n"
        
        result += f"Pre-approved Limit: ₹{customer.get('pre_approved_limit', 0):,.0f}\n"
        result += f"KYC Verified: {'Yes ✓' if customer.get('kyc_verified') else 'No ✗'}\n"
        
        return result
            
    except requests.HTTPError as e:
        if e.response.status_code == 404:
            return f"✗ No customer found with phone number: {phone}"
        return f"Error fetching customer details: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"