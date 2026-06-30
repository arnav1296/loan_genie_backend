# tools/underwriting_tools.py
from crewai.tools import tool
import requests
import os

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@tool("get_customer_credit_info")
def get_customer_credit_info(customer_id: str) -> dict:
    """
    Get customer credit score, pre-approved limit, and other loan-relevant information.
    Use this to check eligibility for loan approval.
    
    Args:
        customer_id: The customer's unique ID
    
    Returns:
        Dictionary with credit_score, pre_approved_limit, monthly_income, existing_loan_amount, etc.
    """
    try:
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        
        if response.status_code == 404:
            return {"error": "Customer not found"}
        
        if response.status_code != 200:
            return {"error": f"API error: {response.status_code}"}
        
        customer = response.json()
        
        return {
            "customer_id": customer["customer_id"],
            "name": customer["name"],
            "credit_score": customer["credit_score"],
            "pre_approved_limit": customer["pre_approved_limit"],
            "monthly_income": customer["monthly_income"],
            "existing_loan_amount": customer["existing_loan_amount"],
            "employment_status": customer["employment_status"]
        }
    
    except Exception as e:
        return {"error": f"Failed to fetch customer info: {str(e)}"}


@tool("calculate_emi")
def calculate_emi(loan_amount: float, tenure_months: int = 12, annual_interest_rate: float = 0.10) -> dict:
    """
    Calculate monthly EMI for a loan.
    Use this to determine if the EMI is affordable for the customer.
    
    Args:
        loan_amount: Loan amount in rupees
        tenure_months: Loan tenure in months (default: 12)
        annual_interest_rate: Annual interest rate as decimal (default: 0.10 for 10%)
    
    Returns:
        Dictionary with emi, loan_amount, tenure_months, annual_interest_rate
    """
    try:
        monthly_interest = annual_interest_rate / 12
        
        # EMI formula: P × r × (1 + r)^n / ((1 + r)^n - 1)
        emi = (loan_amount * monthly_interest * (1 + monthly_interest)**tenure_months) / \
              ((1 + monthly_interest)**tenure_months - 1)
        
        return {
            "emi": round(emi, 2),
            "loan_amount": loan_amount,
            "tenure_months": tenure_months,
            "annual_interest_rate": annual_interest_rate,
            "total_payable": round(emi * tenure_months, 2),
            "total_interest": round((emi * tenure_months) - loan_amount, 2)
        }
    
    except Exception as e:
        return {"error": f"Failed to calculate EMI: {str(e)}"}


@tool("check_loan_eligibility")
def check_loan_eligibility(customer_id: str, loan_amount: float) -> dict:
    """
    Check if a customer is eligible for a loan based on:
    - Credit score (must be >= 700)
    - Pre-approved limit
    - Loan amount requested
    
    Rules:
    - If credit score < 700: REJECT
    - If loan amount <= pre-approved limit: APPROVE INSTANTLY
    - If loan amount <= 2× pre-approved limit: REQUIRES SALARY SLIP
    - If loan amount > 2× pre-approved limit: REJECT
    
    Args:
        customer_id: The customer's unique ID
        loan_amount: Requested loan amount in rupees
    
    Returns:
        Dictionary with eligibility status, decision, reason, and customer info
    """
    try:
        # Get customer info
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        
        if response.status_code == 404:
            return {
                "eligible": False,
                "decision": "REJECTED",
                "reason": "Customer not found in system"
            }
        
        if response.status_code != 200:
            return {
                "eligible": False,
                "decision": "ERROR",
                "reason": f"API error: {response.status_code}"
            }
        
        customer = response.json()
        credit_score = customer["credit_score"]
        pre_approved_limit = customer["pre_approved_limit"]
        
        # Rule 1: Check credit score
        if credit_score < 700:
            return {
                "eligible": False,
                "decision": "REJECTED",
                "reason": f"Credit score ({credit_score}) is below minimum requirement (700)",
                "credit_score": credit_score,
                "pre_approved_limit": pre_approved_limit
            }
        
        # Rule 2: Instant approval if within pre-approved limit
        if loan_amount <= pre_approved_limit:
            return {
                "eligible": True,
                "decision": "APPROVED",
                "reason": f"Loan amount (₹{loan_amount:,.2f}) is within pre-approved limit (₹{pre_approved_limit:,.2f})",
                "credit_score": credit_score,
                "pre_approved_limit": pre_approved_limit,
                "requires_salary_slip": False
            }
        
        # Rule 3: Requires salary slip if <= 2× pre-approved limit
        elif loan_amount <= 2 * pre_approved_limit:
            return {
                "eligible": True,
                "decision": "PENDING_SALARY_VERIFICATION",
                "reason": f"Loan amount (₹{loan_amount:,.2f}) requires salary slip verification (between ₹{pre_approved_limit:,.2f} and ₹{2 * pre_approved_limit:,.2f})",
                "credit_score": credit_score,
                "pre_approved_limit": pre_approved_limit,
                "max_eligible_with_salary": 2 * pre_approved_limit,
                "requires_salary_slip": True
            }
        
        # Rule 4: Reject if > 2× pre-approved limit
        else:
            return {
                "eligible": False,
                "decision": "REJECTED",
                "reason": f"Loan amount (₹{loan_amount:,.2f}) exceeds maximum eligible amount (₹{2 * pre_approved_limit:,.2f})",
                "credit_score": credit_score,
                "pre_approved_limit": pre_approved_limit,
                "max_eligible_with_salary": 2 * pre_approved_limit,
                "requires_salary_slip": False
            }
    
    except Exception as e:
        return {
            "eligible": False,
            "decision": "ERROR",
            "reason": f"Failed to check eligibility: {str(e)}"
        }


@tool("verify_salary_affordability")
def verify_salary_affordability(
    monthly_salary: float, 
    loan_amount: float, 
    tenure_months: int = 12, 
    annual_interest_rate: float = 0.10
) -> dict:
    """
    Verify if the loan EMI is affordable based on salary.
    Rule: EMI must be <= 50% of monthly salary
    
    Use this after customer uploads salary slip and you extract the monthly salary amount.
    
    Args:
        monthly_salary: Customer's monthly salary from salary slip
        loan_amount: Requested loan amount
        tenure_months: Loan tenure in months (default: 12)
        annual_interest_rate: Annual interest rate as decimal (default: 0.10)
    
    Returns:
        Dictionary with affordability decision, EMI details, and percentages
    """
    try:
        # Calculate EMI
        monthly_interest = annual_interest_rate / 12
        emi = (loan_amount * monthly_interest * (1 + monthly_interest)**tenure_months) / \
              ((1 + monthly_interest)**tenure_months - 1)
        emi = round(emi, 2)
        
        # Calculate percentages
        max_affordable_emi = monthly_salary * 0.5
        emi_percentage = (emi / monthly_salary) * 100
        
        # Check affordability
        if emi <= max_affordable_emi:
            return {
                "affordable": True,
                "decision": "APPROVED",
                "reason": f"EMI (₹{emi:,.2f}) is {emi_percentage:.1f}% of monthly salary, which is within the 50% limit",
                "emi": emi,
                "monthly_salary": monthly_salary,
                "max_affordable_emi": max_affordable_emi,
                "emi_percentage": round(emi_percentage, 2)
            }
        else:
            return {
                "affordable": False,
                "decision": "REJECTED",
                "reason": f"EMI (₹{emi:,.2f}) is {emi_percentage:.1f}% of monthly salary, which exceeds the 50% limit (max affordable: ₹{max_affordable_emi:,.2f})",
                "emi": emi,
                "monthly_salary": monthly_salary,
                "max_affordable_emi": max_affordable_emi,
                "emi_percentage": round(emi_percentage, 2)
            }
    
    except Exception as e:
        return {
            "affordable": False,
            "decision": "ERROR",
            "reason": f"Failed to verify affordability: {str(e)}"
        }