from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import json
from .models import (
    PricingPlan,
    PaymentTransaction,
    PaymentQueue,
    MpesaCallback,
    InternetAccess
)


class BasePaymentView(View):
    """Base view for payment functionality"""

    def json_response(self, data, status=200):
        return JsonResponse(data, status=status)

    def error_response(self, message, status=400):
        return self.json_response({'error': message}, status=status)

    def parse_json_body(self, request):
        try:
            return json.loads(request.body)
        except json.JSONDecodeError:
            return None


@method_decorator(csrf_exempt, name='dispatch')
class PricingPlansView(BasePaymentView):

    def get(self, request):
        """Get all active pricing plans"""
        try:
            plans = PricingPlan.objects.filter(is_active=True).order_by('display_order')

            plans_data = []
            for plan in plans:
                plans_data.append({
                    'id': str(plan.id),
                    'name': plan.name,
                    'duration': plan.duration,
                    'duration_display': plan.get_duration_display(),
                    'price': float(plan.price),
                    'original_price': float(plan.original_price) if plan.original_price else None,
                    'savings_percentage': plan.savings_percentage,
                    'is_popular': plan.is_popular,
                    'features': plan.features,
                    'duration_minutes': plan.duration_minutes
                })

            return self.json_response({'plans': plans_data})

        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class InitiatePaymentView(BasePaymentView):

    @method_decorator(login_required)
    def post(self, request):
        """Initiate a payment transaction"""
        try:
            data = self.parse_json_body(request)
            if not data:
                return self.error_response('Invalid JSON')

            plan_id = data.get('plan_id')
            payment_method = data.get('payment_method')
            phone_number = data.get('phone_number')  # For M-Pesa

            # Validate plan
            try:
                plan = PricingPlan.objects.get(id=plan_id, is_active=True)
            except PricingPlan.DoesNotExist:
                return self.error_response('Invalid pricing plan', 400)

            # Create payment transaction
            transaction = PaymentTransaction.objects.create(
                user=request.user,
                plan=plan,
                amount=plan.price,
                payment_method=payment_method,
                expires_at=timezone.now() + timedelta(minutes=10),  # 10 minutes to complete payment
                mpesa_phone=phone_number if payment_method == 'mpesa' else None
            )

            # Initiate payment based on method
            if payment_method == 'mpesa':
                result = self.initiate_mpesa_payment(transaction, phone_number)
            else:
                result = self.initiate_card_payment(transaction, data)

            if result['success']:
                # Add to payment queue if M-Pesa
                if payment_method == 'mpesa':
                    queue_position = self.add_to_payment_queue(transaction)
                    result['queue_position'] = queue_position

                return self.json_response({
                    'message': 'Payment initiated successfully',
                    'transaction_id': str(transaction.id),
                    'queue_position': result.get('queue_position'),
                    'instructions': result.get('instructions', 'Check your phone for payment prompt')
                })
            else:
                transaction.status = 'failed'
                transaction.save()
                return self.error_response(result['message'], 400)

        except Exception as e:
            return self.error_response(str(e), 500)

    def initiate_mpesa_payment(self, transaction, phone_number):
        """Initiate M-Pesa STK push"""
        try:
            # This would integrate with actual M-Pesa API
            # For demo purposes, we'll simulate the API call

            # Simulate M-Pesa API response
            mock_response = {
                'success': True,
                'merchant_request_id': 'AG_2024_' + str(transaction.id)[:8],
                'checkout_request_id': 'ws_CO_2024_' + str(transaction.id)[:8],
                'response_description': 'Success. Request accepted for processing'
            }

            # Update transaction with M-Pesa IDs
            transaction.mpesa_merchant_request_id = mock_response['merchant_request_id']
            transaction.mpesa_checkout_request_id = mock_response['checkout_request_id']
            transaction.save()

            return {
                'success': True,
                'instructions': 'Check your phone for M-Pesa prompt and enter your PIN to complete payment'
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'M-Pesa payment initiation failed: {str(e)}'
            }

    def initiate_card_payment(self, transaction, card_data):
        """Initiate card payment (simplified for demo)"""
        # In a real implementation, this would integrate with a payment gateway
        # like Stripe, PayPal, etc.
        return {
            'success': True,
            'instructions': 'Card payment initiated successfully'
        }

    def add_to_payment_queue(self, transaction):
        """Add transaction to payment processing queue"""
        current_queue_count = PaymentQueue.objects.filter(processed_at__isnull=True).count()
        queue_position = current_queue_count + 1

        PaymentQueue.objects.create(
            transaction=transaction,
            position=queue_position,
            estimated_wait_time=queue_position * 30  # 30 seconds per position
        )

        transaction.queue_position = queue_position
        transaction.save()

        return queue_position


@method_decorator(csrf_exempt, name='dispatch')
class PaymentStatusView(BasePaymentView):

    @method_decorator(login_required)
    def get(self, request, transaction_id):
        """Check payment status"""
        try:
            transaction = PaymentTransaction.objects.get(
                id=transaction_id,
                user=request.user
            )

            # Simulate status check (in real implementation, this would check with payment provider)
            status_data = {
                'status': transaction.status,
                'transaction_id': str(transaction.id),
                'amount': float(transaction.amount),
                'plan_name': transaction.plan.name,
                'queue_position': transaction.queue_position,
                'is_expired': transaction.is_expired
            }

            # If payment is completed, include access details
            if transaction.status == 'completed' and hasattr(transaction, 'access'):
                access = transaction.access
                status_data['access'] = {
                    'start_time': access.start_time.isoformat(),
                    'end_time': access.end_time.isoformat(),
                    'remaining_minutes': access.remaining_time,
                    'is_active': access.is_active
                }

            return self.json_response(status_data)

        except PaymentTransaction.DoesNotExist:
            return self.error_response('Transaction not found', 404)
        except Exception as e:
            return self.error_response(str(e), 500)


@method_decorator(csrf_exempt, name='dispatch')
class MpesaCallbackView(BasePaymentView):
    """Handle M-Pesa callback notifications"""

    def post(self, request):
        try:
            callback_data = self.parse_json_body(request)

            # Log the callback
            callback = MpesaCallback.objects.create(
                callback_data=callback_data
            )

            # Process the callback
            result = self.process_mpesa_callback(callback_data)

            if result['success']:
                callback.processed = True
                callback.save()
                return self.json_response({'result': 'Success'})
            else:
                callback.processing_error = result['error']
                callback.save()
                return self.error_response(result['error'], 400)

        except Exception as e:
            return self.error_response(str(e), 500)

    def process_mpesa_callback(self, callback_data):
        """Process M-Pesa callback and update transaction status"""
        try:
            # Extract transaction details from callback
            result_code = callback_data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            checkout_request_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')

            if result_code == 0:
                # Payment successful
                try:
                    transaction = PaymentTransaction.objects.get(
                        mpesa_checkout_request_id=checkout_request_id
                    )
                    transaction.status = 'completed'
                    transaction.completed_at = timezone.now()
                    transaction.mpesa_transaction_id = callback_data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [{}])[0].get('Value')
                    transaction.save()

                    # Create internet access
                    self.create_internet_access(transaction)

                    # Mark queue as processed
                    if hasattr(transaction, 'queue_entry'):
                        transaction.queue_entry.processed_at = timezone.now()
                        transaction.queue_entry.save()

                    return {'success': True}

                except PaymentTransaction.DoesNotExist:
                    return {'success': False, 'error': 'Transaction not found'}
            else:
                # Payment failed
                try:
                    transaction = PaymentTransaction.objects.get(
                        mpesa_checkout_request_id=checkout_request_id
                    )
                    transaction.status = 'failed'
                    transaction.save()
                    return {'success': True}
                except PaymentTransaction.DoesNotExist:
                    return {'success': False, 'error': 'Transaction not found'}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_internet_access(self, transaction):
        """Create internet access record for completed payment"""
        end_time = timezone.now() + timedelta(minutes=transaction.plan.duration_minutes)

        InternetAccess.objects.create(
            user=transaction.user,
            payment=transaction,
            plan=transaction.plan,
            end_time=end_time,
            bandwidth_limit=self.get_bandwidth_for_plan(transaction.plan)
        )

    def get_bandwidth_for_plan(self, plan):
        """Get bandwidth limit based on plan"""
        bandwidth_map = {
            '30min': 10,
            '1hour': 25,
            '4hours': 50,
            '1day': 100,
            '1week': 200,
            '1month': 1000
        }
        return bandwidth_map.get(plan.duration, 10)


@method_decorator(csrf_exempt, name='dispatch')
class UserAccessView(BasePaymentView):

    @method_decorator(login_required)
    def get(self, request):
        """Get user's current internet access status"""
        try:
            current_access = InternetAccess.objects.filter(
                user=request.user,
                status='active'
            ).select_related('plan').first()

            if current_access and current_access.is_active:
                access_data = {
                    'has_access': True,
                    'plan_name': current_access.plan.name,
                    'start_time': current_access.start_time.isoformat(),
                    'end_time': current_access.end_time.isoformat(),
                    'remaining_minutes': current_access.remaining_time,
                    'bandwidth': current_access.bandwidth_limit,
                    'data_used': current_access.data_used
                }
            else:
                access_data = {
                    'has_access': False,
                    'message': 'No active internet access'
                }

            # Get payment history
            payment_history = PaymentTransaction.objects.filter(
                user=request.user
            ).select_related('plan').order_by('-initiated_at')[:10]

            history_data = []
            for payment in payment_history:
                history_data.append({
                    'plan': payment.plan.name,
                    'amount': float(payment.amount),
                    'status': payment.status,
                    'method': payment.payment_method,
                    'date': payment.initiated_at.isoformat()
                })

            return self.json_response({
                'current_access': access_data,
                'payment_history': history_data
            })

        except Exception as e:
            return self.error_response(str(e), 500)
