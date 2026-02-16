from paystackapi.transaction import Transaction
from bot.config import Config
import logging

logger = logging.getLogger(__name__)

def get_payment_link(telegram_id: int, amount: int, user_email: str, plan_name: str) -> str:
    """
    Generates a unique Paystack payment link for a user.
    """
    try:
        # Initialize Paystack with secret key
        transaction = Transaction(secret_key=Config.PAYSTACK_SECRET_KEY)

        # Create the transaction
        response = transaction.initialize(
            amount=amount,
            email=user_email,
            channels=['card', 'bank', 'ussd'],  # Common payment channels
            metadata={
                "telegram_id": str(telegram_id),
                "plan_name": plan_name,
                "custom_fields": [
                    {"display_name": "Telegram ID", "variable_name": "telegram_id", "value": str(telegram_id)},
                    {"display_name": "Plan Name", "variable_name": "plan_name", "value": plan_name}
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
