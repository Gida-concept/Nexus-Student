from flask import Blueprint, request, jsonify
from bot.config import Config
from bot.models import User, Subscription
from bot import db_app
from paystackapi.transaction import Transaction
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/paystack/webhook', methods=['POST'])
def paystack_webhook():
    """Handle Paystack webhook notifications."""
    # Verify the webhook signature
    if not verify_paystack_signature(request):
        logger.warning("Invalid Paystack webhook signature")
        return jsonify({"status": "error", "message": "Invalid signature"}), 401

    # Get the event data
    event = request.json
    event_type = event.get('event')

    logger.info(f"Received Paystack webhook: {event_type}")

    # Handle different event types
    if event_type == 'subscription.create':
        return handle_subscription_create(event)
    elif event_type == 'invoice.update':
        return handle_invoice_update(event)
    elif event_type == 'customer.subscription.disable':
        return handle_subscription_cancel(event)
    else:
        logger.info(f"Unhandled event type: {event_type}")
        return jsonify({"status": "ok"}), 200

def verify_paystack_signature(request):
    """Verify the Paystack webhook signature."""
    if not Config.PAYSTACK_SECRET_KEY:
        logger.error("Paystack secret key not configured")
        return False

    # Get the raw body and headers
    raw_body = request.get_data()
    signature = request.headers.get('x-paystack-signature')

    if not signature:
        logger.warning("No signature in headers")
        return False

    # Create the hash
    computed_hash = hmac.new(
        Config.PAYSTACK_SECRET_KEY.encode(),
        raw_body,
        hashlib.sha512
    ).hexdigest()

    # Compare with the provided signature
    return hmac.compare_digest(computed_hash, signature)

def handle_subscription_create(event):
    """Handle new subscription creation."""
    data = event.get('data', {})
    subscription = data.get('subscription', {})
    customer = data.get('customer', {})

    # Extract metadata
    metadata = subscription.get('metadata', {})
    telegram_id = metadata.get('telegram_id')

    if not telegram_id:
        logger.error("No Telegram ID in subscription metadata")
        return jsonify({"status": "error", "message": "No Telegram ID"}), 400

    # Update user subscription in database
    with db_app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            logger.error(f"User not found for Telegram ID: {telegram_id}")
            return jsonify({"status": "error", "message": "User not found"}), 404

        # Create or update subscription
        subscription_record = Subscription(
            user_id=user.id,
            paystack_subscription_code=subscription.get('id'),
            paystack_customer_code=customer.get('id'),
            paystack_email=customer.get('email'),
            status='active',
            next_payment_date=subscription.get('next_payment_date')
        )

        db.session.merge(subscription_record)
        db.session.commit()

    logger.info(f"Subscription created for user {telegram_id}")
    return jsonify({"status": "ok"}), 200

def handle_invoice_update(event):
    """Handle subscription payment updates."""
    data = event.get('data', {})
    invoice = data.get('invoice', {})

    # Extract metadata
    metadata = invoice.get('metadata', {})
    telegram_id = metadata.get('telegram_id')

    if not telegram_id:
        logger.error("No Telegram ID in invoice metadata")
        return jsonify({"status": "error", "message": "No Telegram ID"}), 400

    # Update subscription status
    with db_app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            logger.error(f"User not found for Telegram ID: {telegram_id}")
            return jsonify({"status": "error", "message": "User not found"}), 404

        subscription = Subscription.query.filter_by(
            user_id=user.id,
            paystack_subscription_code=invoice.get('subscription')
        ).first()

        if not subscription:
            logger.error(f"Subscription not found for user {telegram_id}")
            return jsonify({"status": "error", "message": "Subscription not found"}), 404

        # Update subscription status
        subscription.status = 'active' if invoice.get('status') == 'active' else 'inactive'
        subscription.next_payment_date = invoice.get('next_payment_date')

        db.session.commit()

    logger.info(f"Invoice updated for user {telegram_id}")
    return jsonify({"status": "ok"}), 200

def handle_subscription_cancel(event):
    """Handle subscription cancellation."""
    data = event.get('data', {})
    subscription = data.get('subscription', {})

    # Extract metadata
    metadata = subscription.get('metadata', {})
    telegram_id = metadata.get('telegram_id')

    if not telegram_id:
        logger.error("No Telegram ID in subscription metadata")
        return jsonify({"status": "error", "message": "No Telegram ID"}), 400

    # Update subscription status
    with db_app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            logger.error(f"User not found for Telegram ID: {telegram_id}")
            return jsonify({"status": "error", "message": "User not found"}), 404

        subscription_record = Subscription.query.filter_by(
            user_id=user.id,
            paystack_subscription_code=subscription.get('id')
        ).first()

        if not subscription_record:
            logger.error(f"Subscription not found for user {telegram_id}")
            return jsonify({"status": "error", "message": "Subscription not found"}), 404

        subscription_record.status = 'cancelled'
        db.session.commit()

    logger.info(f"Subscription cancelled for user {telegram_id}")
    return jsonify({"status": "ok"}), 200