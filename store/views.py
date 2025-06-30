from django.shortcuts import render,redirect
from .models import Product,Order,Category
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import Paginator
import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseRedirect
# Create your views here.
stripe.api_key = settings.STRIPE_SECRET_KEY

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    searchvalue = request.GET.get('searchvalue','')
    category = request.GET.get('category','')
    print('search',searchvalue)
    print('category',category)
    if searchvalue:
        products = Product.objects.filter(name__icontains=searchvalue)

    if category:
        products = Product.objects.filter(category=category)

    # Setup pagination
    paginator = Paginator(products, 2)  # Show 6 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    return render(request, 'store/product_list.html', context={'page_obj': page_obj,'products': products,'categories': categories,'searchvalue':searchvalue,'selected_category': category})

def product_details(request,id):
    product_instance = Product.objects.get(id=id)
    return render(request, 'store/product_details.html', context = {'product': product_instance})

def add_to_cart(request,product_id):
    cart = request.session.get('cart',{})
    
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    request.session['cart'] = cart
    return redirect('store:view_cart')

def view_cart(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        product_instance = Product.objects.get(id=product_id)
        total = product_instance.price * quantity
        total_price += total

        cart_items.append({
            'product': product_instance,
            'quantity': quantity,
            'total': total,
        })

    return render(request, 'store/cart.html', context={'cart_items': cart_items,'total_price': total_price})

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        request.session['cart'] = cart
    return redirect('store:view_cart')

def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = User.objects.create_user(username=email,email=email,first_name=name,is_active=False,password=password)
        user.save()
        request.session['user_id'] = user.id
        return render(request,'store/product_list.html')

    return render(request,'store/signup.html')

from django.contrib.auth import authenticate,login
def login_view(request):
    if request.method == 'POST':
        email =  request.POST['email']
        password = request.POST.get('password')
        #print("email:",email)
        #print("password:",password)
        user = authenticate(request,username=email,password=password)
        print("user:",user)
        #print("username:",user.first_name)
        if user is not None:
            login(request,user)
            return redirect('store:product_list')
        else:
            messages.error(request,"Invalid username or password / User account not registered")
            return redirect('store:login')
    return render(request,'store/login.html')

from django.contrib.auth import logout
def logout_view(request):
    logout(request)
    messages.success(request,"Successfully logged out from the account")
    return render(request,'store/login.html')

@login_required
def checkout(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        Order.objects.create(
            user=request.user,
            product=product,
            quantity=quantity
        )
        product.stock -= quantity
        print("stock",product.stock)
        product.save()

    request.session['cart'] = {}
    messages.success(request, "Order placed successfully!")
    return redirect('store:product_list')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-ordered_at')
    return render(request, 'store/order_history.html', {'orders': orders})

@csrf_exempt
@login_required
def create_checkout_session(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            messages.warning(request, "Your cart is empty.")
            return redirect('store:product_list')

        line_items = []
        for product_id, quantity in cart.items():
            product = Product.objects.get(id=product_id)
            line_items.append({
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product.name,
                    },
                    'unit_amount': int(product.price * 100),
                },
                'quantity': quantity,
            })

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri('/success/'),
            cancel_url=request.build_absolute_uri('/cancel/'),
        )

        return HttpResponseRedirect(checkout_session.url)


@login_required
def checkout_success(request):
    cart = request.session.get('cart', {})

    if not cart:
        messages.warning(request, "Your cart is empty.")
        return redirect('store:product_list')

    order_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        Order.objects.create(
            user=request.user,
            product=product,
            quantity=quantity
        )
        product.stock -= quantity
        product.save()

        subtotal = product.price * quantity
        order_items.append({
            'name': product.name,
            'price': product.price,
            'quantity': quantity,
            'subtotal': subtotal
        })
        total += subtotal

    request.session['cart'] = {}

    context = {
        'order_items': order_items,
        'total': total
    }

    return render(request, 'store/success.html', context)

def checkout_cancel(request):
    messages.info(request, "Payment was cancelled.")
    return redirect('store:cart')

