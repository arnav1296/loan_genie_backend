from crewai import Task, Crew
from agents.sales_agent import sales_agent
from agents.verification_agent import verification_agent
from agents.underwriting_agent import underwriting_agent

def chat():
    print("=== Loan Application System ===")
    print("Type 'exit' or 'quit' to end the conversation\n")

    conversation_history = []
    current_agent = sales_agent  # Start with sales
    stage = "underwriting"  # Track stage: sales -> verification -> approval

    while True:
        customer_query = input("Customer: ")
        
        if customer_query.lower() in ['exit', 'quit', 'bye']:
            print("Agent: Thank you for your time! Have a great day!")
            break
        
        conversation_history.append(f"Customer: {customer_query}")
        context = "\n".join(conversation_history[-10:])
        
        # SALES STAGE
        if stage == "sales":
            sales_task = Task(
                description=f"""Previous conversation:
{context}

Customer's latest message: "{customer_query}"

Your job:
1. Respond naturally to their message
2. Gather loan information (amount, purpose, income, employment)
3. Keep the conversation flowing
4. If you have ALL required information, end your response with: [READY_FOR_VERIFICATION]

Be conversational and helpful.""",
                agent=sales_agent,
                expected_output="A natural conversational response"
            )
            
            crew = Crew(agents=[sales_agent], tasks=[sales_task], verbose=False)
            result = crew.kickoff()
            
            # Check if ready to move to verification
            if "[READY_FOR_VERIFICATION]" in str(result):
                result = str(result).replace("[READY_FOR_VERIFICATION]", "")
                stage = "verification"
                current_agent = verification_agent
                print(f"\nAgent: {result}")
                print("\n--- Transferring to KYC Verification Specialist ---\n")
            else:
                conversation_history.append(f"Agent: {result}")
                print(f"\nAgent: {result}\n")
        
        # VERIFICATION STAGE
        elif stage == "verification":
            verification_task = Task(
                description=f"""Previous conversation:
{context}

Customer's latest message: "{customer_query}"

Your job:
1. Verify the customer's phone number first
2. Then verify their address
3. If both are verified, complete KYC verification
4. Guide them through any verification issues


Be professional and clear about what you need.""",
                agent=verification_agent,
                expected_output="A professional verification response"
            )
            
            crew = Crew(agents=[verification_agent], tasks=[verification_task], verbose=False)
            result = crew.kickoff()
            
            # Check if KYC is complete
            if "[KYC_COMPLETE]" in str(result):
                result = str(result).replace("[KYC_COMPLETE]", "")
                print(f"\nAgent: {result}")
                print("\n✓ Application Complete! Moving to approval stage...\n")
                break
            else:
                conversation_history.append(f"Agent: {result}")
                print(f"\nAgent: {result}\n")
                
                
        elif stage == 'underwriting':
            underwriting_task = Task(
                description=f'''Previous conversation:
{context}

Customer's latest message: "{customer_query}"

Your job:

Extract the customer_id and requested loan_amount from the conversation or handoff summary.

Use the check_loan_eligibility tool to determine the loan status.

Based on the tool response:

APPROVED → Congratulate the customer and clearly explain the approval details and next steps.

REJECTED → Politely explain the reason (low credit score or loan amount too high).

PENDING_SALARY_VERIFICATION → Request the customer to upload their latest salary slip for verification.

If the customer uploads a salary slip:

Extract the monthly_salary from the document.

Use verify_salary_affordability to check whether the EMI is affordable.

Approve or reject based on the affordability result.

Clearly communicate the final decision with reasoning and next steps.''',
                agent=underwriting_agent,
                expected_output="A professional underwriting decision response"
            )
            
            crew = Crew(
                agents=[underwriting_agent],
                tasks=[underwriting_task],
                verbose=False
            )

            result = crew.kickoff()

            conversation_history.append(f"Agent: {result}")
            print(f"\nAgent: {result}\n")

            # If approved or rejected → end application
            if "APPROVED" in str(result) or "REJECTED" in str(result):
                print("✓ Underwriting decision completed.\n")
                break

            # If salary verification needed → stay in underwriting stage
            elif "PENDING_SALARY_VERIFICATION" in str(result):
                print("Waiting for salary slip upload...\n")
            
            
