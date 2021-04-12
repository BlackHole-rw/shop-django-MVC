from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm, PromoCode, RefundForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund
from django.conf import settings
import stripe
import random
import string
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

class HomeView(ListView):
    model = Item
    paginate_by = 8
    template_name = 'home.html'

class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.html'

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order,
            }
            return render(self.request, 'order-summary.html', context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")

class CheckoutView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        try:
            form = CheckoutForm()
            formcode = PromoCode()
            context = {
                'form': form,
                'object': order,
                'formcode': formcode
            }
            return render(self.request, 'checkout.html', context)
        except ObjectDoesNotExist:
            return redirect("/")

    def post(self, *args, **kwargs):
        formcoupon = PromoCode(self.request.POST or None)
        form = CheckoutForm(self.request.POST or None)

        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_shipping_address = form.cleaned_data.get('use_shipping_address')
                if use_shipping_address:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='S',
                        default=True
                    )
                    order.shipping_address = address_qs[0]
                    order.save()
                    return redirect('core:checkout')

                    save_shipping_address = form.cleaned_data.get('save_shipping_address')
                    if save_shipping_address:
                        shipping_address1 = form.cleaned_data.get('shipping_address1')
                        shipping_address2 = form.cleaned_data.get('shipping_address2')
                        shipping_country = form.cleaned_data.get('shipping_country')
                        shipping_zip = form.cleaned_data.get('shipping_zip')

                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S',
                            default=True
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                use_billing_address = form.cleaned_data.get('use_billing_address')
                if use_billing_address:
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type='B',
                        default=True
                    )
                    order.billing_address = address_qs[0]
                    order.save()
                    return redirect('core:checkout')

                    save_billing_address = form.cleaned_data.get('save_billing_address')
                    if save_billing_address:
                        billing_address1 = form.cleaned_data.get('billing_address1')
                        billing_address2 = form.cleaned_data.get('billing_address2')
                        billing_country = form.cleaned_data.get('billing_country')
                        billing_zip = form.cleaned_data.get('billing_zip')

                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B',
                            default=True
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                payment_option = form.cleaned_data.get('payment_option')
                if payment_option == 'S':
                    return redirect('core:payment', payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment', payment_option='paypal')
                else:
                    messages.warning(self.request, "Invalid payment option selected")
                    return redirect('core:checkout')

            if formcoupon.is_valid():
                code = formcoupon.cleaned_data.get('code')
                promo_code = Coupon.objects.all()
                for coupon in promo_code:
                    if code == coupon.code:
                        order.promo_code = coupon
                        order.save()
                        messages.success(self.request, "Promo code was updated")
                        return redirect('core:checkout')
                messages.warning(self.request, "Promo code isn't valid")
                return redirect('core:checkout')

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order")
            return redirect("/")

class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        context = {
            'object': order
        }
        return render(self.request, "payment.html", context)

    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        token = self.request.POST.get('stripeToken')
        amount = int(order.total_price() * 100)
        try:
            charge = stripe.Charge.create(
                amount=amount,  # cents
                currency="usd",
                source=token
            )
            # create the payment
            payment = Payment()
            payment.stripe_charge_id = charge['id']
            payment.user = self.request.user
            payment.amount = charge['amount']
            payment.save()

            # assign the payment to the order
            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()

            messages.success(self.request, "Your order was successful")
            return redirect("/")
        except stripe.error.CardError as e:
            messages.error(self.request, f"{err.get('messages')}")
            return redirect("/")

        except stripe.error.RateLimitError as e:
            messages.error(self.request, "Rate limit error")
            return redirect("/")

        except stripe.error.InvalidRequestError as e:
            messages.error(self.request, "Invalid request error")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
            messages.error(self.request, "Authentication error")
            return redirect("/")

        except stripe.error.APIConnectionError as e:
            messages.error(self.request, "Api connection error")
            return redirect("/")

        except stripe.error.StripeError as e:
            messages.error(self.request, "Stripe error")
            return redirect("/")

        except Exception as e:
            #send a email to ourselves
            messages.error(self.request, "Something wrong.Please try again..")
            return redirect("/")



def checkout_page(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "checkout.html", context)

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item, user=request.user, ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
    return redirect('core:product', slug=slug)

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, "This item was removed from your cart.")
            return redirect('core:order-summary')
        else:
            messages.info(request, "This item was removed from your cart.")
            return redirect('core:product', slug=slug)
    else:
        messages.info(request, "This item was not in your cart.")
        return redirect('core:product', slug=slug)
    messages.info(request, "You do not have an active order.")
    return redirect('core:product', slug=slug)

def remove_single_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request, "This item quantity was updated")
            return redirect('core:order-summary')

def add_single_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item, user=request.user, ordered=False)[0]
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated")
            return redirect('core:order-summary')

class RefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form': form
        }
        return render(self.request, "refund-view.html", context)

    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST or None)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()
                messages.info(self.request, "Your request was sent")
                return redirect("/")
            except ObjectDoesNotExist:
                messages.warning(self.request, "Your request was failed")
                return redirect("core:refund")
        messages.warning(self.request, "Your request was failed")
        return redirect("core:refund")