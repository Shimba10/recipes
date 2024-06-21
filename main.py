import json
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_mysqldb import MySQL

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import JSON



app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MYSQL_HOST'] = 'recipe.cf2g4o664v8l.ap-south-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'Admin123'
app.config['MYSQL_DB'] = 'recipe'

mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        
@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", [user_id])
    user = cur.fetchone()
    cur.close()
    if user:
        return User(user[0], user[1], user[2], user[3])
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)", (username, email, password_hash))
        mysql.connection.commit()
        cur.close()
        flash('You are now registered and can log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[3],password):
            login_user(User(user[0], user[1], user[2], user[3]))
            flash('You have been logged in.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/home')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recipes")
    recipes = cur.fetchall()
    cur.close()
    recipe_list = []
    for recipe in recipes:
        recipe_dict = {
            'id': recipe[0],
            'title': recipe[1],
            'description': recipe[2],
            'ingredients': json.loads(recipe[3]),  
            'instructions': recipe[4],
            'created_by': recipe[5]
        }
        recipe_list.append(recipe_dict)
    return render_template('index.html', recipes=recipe_list)

@app.route('/recipe/create', methods=['GET', 'POST'])
@login_required
def create_recipe():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form.getlist('ingredients')
        instructions = request.form['instructions']
        ingredients_json = json.dumps(ingredients)
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO recipes (title, description, ingredients, instructions, created_by) VALUES (%s, %s, %s, %s, %s)", 
                    (title, description, ingredients_json, instructions, current_user.id))
        mysql.connection.commit()
        cur.close()
        flash('Recipe created successfully.', 'success')
        return redirect(url_for('index'))
    return render_template('create_recipe.html')

@app.route('/recipe/<int:recipe_id>')
def view_recipe(recipe_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
    recipe = cur.fetchone()
    cur.close()    
    if recipe:
        recipe_dict = {
            'id': recipe[0],
            'title': recipe[1],
            'description': recipe[2],
            'ingredients': json.loads(recipe[3]),  
            'instructions': recipe[4],
            'created_by': recipe[5]
        }
    else:
        recipe_dict = None
    return render_template('view_recipe.html', recipe=recipe_dict)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
    recipe = cur.fetchone()
    cur.close()    
    if recipe is None or recipe[5] != current_user.id:
        flash('You are not authorized to edit this recipe.', 'danger')
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form.getlist('ingredients')
        instructions = request.form['instructions']
        ingredients_json = json.dumps(ingredients)
        cur = mysql.connection.cursor()
        cur.execute("UPDATE recipes SET title = %s, description = %s, ingredients = %s, instructions = %s WHERE id = %s",
                    (title, description, ingredients_json, instructions, recipe_id))
        mysql.connection.commit()
        cur.close()
        flash('Recipe updated successfully.', 'success')
        return redirect(url_for('view_recipe', recipe_id=recipe_id))
    return render_template('edit_recipe.html', recipe=recipe)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM recipes WHERE id = %s", [recipe_id])
    recipe = cur.fetchone()
    cur.close()
    if recipe is None or recipe[5] != current_user.id:
        flash('You are not authorized to delete this recipe.', 'danger')
        return redirect(url_for('index'))
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM recipes WHERE id = %s", [recipe_id])
    mysql.connection.commit()
    cur.close()
    flash('Recipe deleted successfully.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
