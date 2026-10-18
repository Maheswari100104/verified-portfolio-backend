
import os
import requests

from dotenv import load_dotenv

load_dotenv()


def send_shortlist_email(
    candidate_email: str,
    candidate_name: str,
    opportunity_title: str,
    company_name: str,
    company_website: str | None = None,
    company_phone: str | None = None,
    company_email: str | None = None,
) -> bool:

    try:
        # -------------------------------------------------
        # Brevo configuration
        # -------------------------------------------------

        brevo_api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")

        if not brevo_api_key:
            print("BREVO_API_KEY is not configured.")
            return False

        if not sender_email:
            print("BREVO_SENDER_EMAIL is not configured.")
            return False

        if not candidate_email:
            print("Candidate email is missing.")
            return False

        # -------------------------------------------------
        # Company contact details
        # -------------------------------------------------

        website_text = company_website or "Not provided"
        phone_text = company_phone or "Not provided"
        email_text = company_email or "Not provided"

        # -------------------------------------------------
        # Email content
        # -------------------------------------------------

        email_body = f"""
Dear {candidate_name},

Congratulations!

We are pleased to inform you that your profile has been
shortlisted for the following opportunity.

Opportunity: {opportunity_title}
Company: {company_name}

Company Contact Details
-----------------------
Website: {website_text}
Phone: {phone_text}
Email: {email_text}

Please log in to your CareerVault account to view the
opportunity details and check for any further updates
or next steps.

Thank you for using CareerVault.

Best regards,
CareerVault Team
"""

        # -------------------------------------------------
        # Send through Brevo HTTP API
        # -------------------------------------------------

        url = "https://api.brevo.com/v3/smtp/email"

        headers = {
            "accept": "application/json",
            "api-key": brevo_api_key,
            "content-type": "application/json",
        }

        payload = {
            "sender": {
                "name": "CareerVault",
                "email": sender_email,
            },
            "to": [
                {
                    "email": candidate_email,
                    "name": candidate_name,
                }
            ],
            "subject": (
                f"You have been shortlisted for "
                f"{opportunity_title}"
            ),
            "textContent": email_body,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code in (200, 201, 202):
            print(
                f"Brevo accepted the shortlist email for "
                f"{candidate_email}. "
                f"Message ID: {response.json().get('messageId', 'N/A')}"
            )
            return True

        print(
            "Brevo email request failed:",
            response.status_code,
            response.text,
        )
        return False

    except requests.RequestException as error:
        print("Brevo request failed:", error)
        return False

    except Exception as error:
        print("Failed to send shortlist email:", error)
        return False
