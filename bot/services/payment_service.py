from paystackapi.transaction import Transaction
from paystackapi.plan import Plan as PaystackPlan
from bot.config import Config
import logging

logger = logging.getLogger(__name__)


def get_payment_link(telegram_id: int, plan_code: str, user_email: str) -> str:
    """
    Generates a unique Paystack payment link for a user to subscribe to a specific plan.

    Args:
        telegram_id (int): The user's Telegram ID for identification in webhooks.
        plan_code (str): The Paystack plan code (e.g., "PLN_xxx") the user wants.
        user_email (str): A dummy email is required by Paystack if user doesn't provide one.

    Returns:
        str: The authorization URL (payment link) or None if it fails.
    """
    try:
        # Initialize Paystack with secret key
        transaction = Transaction(secret_key=Config.PAYSTACK_SECRET_KEY)

        # Create the transaction
        # By passing 'plan', Paystack automatically handles the recurring billing
        response = transaction.initialize(
            amount=0,  # Amount is determined by the plan, so we pass 0 or let Paystack handle it
            email=user_email,
            plan=plan_code,
            metadata={
                "telegram_id": str(telegram_id),  # Store ID so webhook knows who paid
                "custom_fields": [
                    {"display_name": "Telegram ID", "variable_name": "telegram_id", "value": str(telegram_id)}
                ]
            }
        )

        if response['status']:
            return response['data']['authorization_url']
        else:
            logger.error(f"Paystack Init Error: {response.get('message')}")
            return None

    except Exception as e:
        logger.error(f"Payment Service Exception: {str(e)}")
        return None


def sync_paystack_plans():
    """
    (Optional) Helper to sync plans from Paystack to local DB.
    This is useful for admin setup or ensuring local DB matches Paystack.
    """
    try:
        paystack_plan = Plan(secret_key=Config.PAYSTACK_SECRET_KEY)
        plans = paystack_plan.list_plan()
        # Logic to sync these to bot.models.PricingPlan would go here
        return plans
    except Exception as e:
        logger.error(f"Plan Sync Error: {str(e)}")
        return []