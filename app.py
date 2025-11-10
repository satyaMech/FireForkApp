from flask import Flask, render_template, request, redirect, url_for, session, g
import pymssql
import os
from flask import flash
from flask import make_response


app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'default_key_for_dev')

def get_db():
    sqlconn = pymssql.connect(
        server =r'DESKTOP-9AHMAG7\SQLEXPRESS',
        user = 'Automation',
        password = 'Automation',
        database= 'App'
    )
    return sqlconn

def nocache(view):
    def no_cache_wrapper(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response
    no_cache_wrapper.__name__ = view.__name__
    return no_cache_wrapper


@app.route('/login', methods = ['GET', 'POST'])

def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    

        sqlconn = get_db()
        cursor = sqlconn.cursor(as_dict=True)
        cursor.execute("SELECT username, secretCode FROM loginForm WHERE username = %s AND secretCode = %s", (username, password) )
        user = cursor.fetchone()
        sqlconn.close()
        print(user)

        if user:
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        elif user == "None":
            error = "Username and password Mismatch"
        else:
            error =  "Please enter a valid username or password."

    return render_template('login.html', error=error)

@app.route('/dashboard')

def dashboard():
    if 'username' in session:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))
        error =  "Invalid username or password"

@app.route('/register', methods = ['GET', 'POST'])

def register():
    error = None
    success = None
    if request.method    == "POST":
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        sqlconn = get_db()
        cursor = sqlconn.cursor(as_dict=True)
        cursor.execute("select * from loginform where username = %s", (username))
        existing_user = cursor.fetchone()
        print(existing_user)
        if existing_user:
            error = "Username already exists. Please choose another one"
        elif existing_user == "None":
            error = "Please fill all the details"
        else:
            cursor.execute("insert into loginform (firstname, lastname, username, secretCode, email) values(%s, %s, %s, %s, %s)", (firstname, lastname, username, password, email))
            sqlconn.commit()
            success = "Account created successfully! You can now log in."
        sqlconn.close
    return render_template('register.html', error = error, success=success)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/veg-starters')
@nocache
def veg_starters():
    return render_template('veg_starters.html')

@app.route('/nonveg-starters')
def nonveg_starters():
    return render_template('nonveg_starters.html')

@app.route('/seafood')
def seafood():
    return render_template('seafood.html')

@app.route('/maincourse')
def maincourse():
    return render_template('maincourse.html')

@app.route('/desserts')
def desserts():
    return render_template('desserts.html')

@app.route("/add_to_cart", methods=['POST'])
def add_to_cart():
    # Initialize session cart if not already
    if 'cart' not in session:
        session['cart'] = []

    item_name = request.form.get('item_name')
    item_price = request.form.get('item_price')
    quantity = int(request.form.get('quantity', 1))
    current_page = request.form.get('current_page')

    cart = session['cart']

    # ✅ Check if this item already exists
    existing_item = next((item for item in cart if item['name'] == item_name), None)

    if existing_item:
        # If exists → update quantity
        existing_item['quantity'] += quantity
    else:
        # If new → add as a new item
        cart.append({
            'name': item_name,
            'price': item_price,
            'quantity': quantity
        })

    session['cart'] = cart
    session.modified = True

    total_items = len(cart)

    flash(f"{total_items} item(s) added", "success")

    return redirect(request.referrer, code=303)


@app.route("/cart")
def cart():
    cart_items = session.get('cart', [])
    print(cart_items) 
    total = sum(int(item['price']) * int(item['quantity']) for item in cart_items)
    gst = round(total*(5/100), 2)
    restaruant_charges = round(total*(2/100), 2)
    return render_template('cart.html', cart_items=cart_items, total=total, gst=gst, restaruant_charges=restaruant_charges)

@app.route("/update_quantity", methods=["POST"])

def update_quantity():
    item_name = request.form.get("item_name")
    action = request.form.get("action")
    cart = session.get("cart", [])

    for item in cart:
        if item["name"] == item_name:
            if action == "increase":
                item["quantity"] = int(item["quantity"]) + 1
            elif action == "decrease":
                if int(item["quantity"]>1):
                    item["quantity"] = int(item["quantity"]) - 1
                else:
                    cart.remove(item)


    session["cart"] = cart
    session.modified = True
    return redirect(url_for("cart"))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        return render_template('checkout.html')

    total = sum(int(item['price']) * int(item['quantity']) for item in cart_items)
    gst = total * 0.05
    restaurant_charges = total * 0.02
    final_amount = total + gst + restaurant_charges

    # Optionally save order here...

    # Clear cart after order
    session.pop('cart', None)

    return render_template(
        'checkout.html',
        total=total,
        gst=gst,
        restaurant_charges=restaurant_charges,
        final_amount=final_amount
    )


if __name__ == '__main__':
    app.run(debug=True)     