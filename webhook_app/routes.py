from flask import Blueprint, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
from bot.config import Config
from bot.models import User, Subscription, db
from bot import app as bot_app
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/paystack/webhook', methods=['POST'])
async def paystack_webhook():
    """Handle Paystack webhook notifications."""
    if not verify_paystack_signature(request):
        logger.warning("Invalid Paystack webhook signature")
        return jsonify({"status": "error", "message": "Invalid signature"}), 401

    event = request.json
    event_type = event.get('event')
    logger.info(f"Received Paystack webhook: {event_type}")

    if event_type == 'subscription.create':
        return await handle_subscription_create(event)
    elif event_type == 'invoice.update':
        return await handle_invoice_update(event)
    elif event_type == 'customer.subscription.disable':
        return await handle_subscription_cancel(event)
    else:
        logger.info(f"Unhandled event type: {event_type}")
        return jsonify({"status": "ok"}), 200

def verify_paystack_signature(request):
    """Verify the Paystack webhook signature."""
    if not Config.PAYSTACK_SECRET_KEY:
        return False
    raw_body = request.get_data()
    signature = request.headers.get('x-paystack-signature')
    if not signature:
        return False
    computed_hash = hmac.new(Config.PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed_hash, signature)

async def handle_subscription_create(event):
    """Handle new subscription creation."""
    data = event.get('data', {})
    subscription = data.get('subscription', {})
    customer = data.get('customer', {})
    metadata = subscription.get('metadata', {})
    telegram_id = metadata.get('telegram_id')

    if not telegram_id:
        return jsonify({"status": "error", "message": "No Telegram ID"}), 400

    with bot_app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

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

    # Send a confirmation message to the user
    try:
        bot = Bot(token=Config.BOT_TOKEN)
        await bot.send_message(
            chat_id=telegram_id,
            text="🎉 **Payment Successful!**\n\nYour subscription is now active. You have full access to all premium features!",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Subscription confirmation sent to user {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send subscription confirmation: {e}")

    return jsonify({"status": "ok"}), 200

async def handle_invoice_update(event):
    """Handle subscription payment updates."""
    data = event.get('data', {})
    invoice = data.get('invoice', {})
    metadata = invoice.get('metadata', {})
    telegram_id = metadata.get('telegram_id')

    if not telegram_id:
        return jsonify({"status": "error", "message": "No Telegram ID"}), 400

    with bot_app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        subscription = Subscription.query.filter_by(
            user_id=user.id,
            paystack_subscription_code=invoice.get('subscription')
        ).first()

        if not subscription:
            return jsonify({"status": "error", "message": "Subscription not found"}), 404

        subscription.status = 'active' if invoice.get('status') == 'active' else 'inactive'
        subscription.next_payment_date = invoice.get('next_payment_date')
        db.session.commit()

    # Send a confirmation message to the user
    try:
        bot = Bot(token=Config.BOT_TOKEN)
        await bot.send_message(
            chat_id=telegram_id,
            text="✅ **Payment Received!**\n\nYour subscription has been updated.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Invoice update confirmation sent to user {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send invoice update confirmation: {e}")

    return jsonify({"status": "ok"}), 200

async def handle_subscription_cancel(event):
    """Handle subscription cancellation."""
    data = event.get('data', {})
    subscription = data.get('subscription', {})
    metadata = subscription.get('metadata', {})
    telegram_id = metadata.get('telegram_id')

    if not telegram_id:
        return jsonify({"status": "error", "message": "No Telegram ID"}), 400

    with bot_app.app_context():
        user = User.query.filter_by(telegram_id=telegram_id).first()
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        subscription_record = Subscription.query.filter_by(
            user_id=user.id,
            paystack_subscription_code=subscription.get('id')
        ).first()

        if not subscription_record:
            return jsonify({"status": "error", "message": "Subscription not found"}), 404

        subscription_record.status = 'cancelled'
        db.session.commit()

    # Send a cancellation message to the user
    try:
        bot = Bot(token=Config.BOT_TOKEN)
        await bot.send_message(
            chat_id=telegram_id,
            text="⚠️ **Subscription Cancelled**\n\nYour subscription has been cancelled. You will lose access to premium features.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info(f"Subscription cancellation sent to user {telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send subscription cancellation confirmation: {e}")

    return jsonify({"status": "ok"}), 200
