from flask import redirect, url_for, render_template, request, flash, jsonify, session
from program import app
import program.backend.articles as articles
import sqlite3

@app.route("/")
def home():
    titles, dates, urls, contents = [], [], [], []
    
    def fetch_articles():
        try:
            article_data = articles.scrape_45th_district_news()
            return articles.return_articles(article_data)
        except Exception as e:
            print(f"Error fetching news: {str(e)}")
            return [], [], [], []

    return render_template("home.html", logged_in=session.get('logged', False), 
                           titles=titles, dates=dates, urls=urls, contents=contents, 
                           zip=zip, fetch_articles=fetch_articles)
@app.route('/fetch_articles')
def fetch_articles():
    try:
        article_data = articles.scrape_45th_district_news()
        titles, dates, urls, contents = articles.return_articles(article_data)
        return jsonify({
            'titles': titles,
            'dates': dates,
            'urls': urls,
            'contents': contents
        })
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
        return jsonify({
            'error': 'An error occurred while fetching articles'
        }), 500

@app.route('/login.html')
def login_page():
    return render_template('login.html', logged_in=session.get('logged', False))

@app.route('/signup.html')
def signup_page():
    return render_template('signup.html', logged_in=session.get('logged', False))

@app.route('/logged_out.html')
def log_out():
    session['logged'], session['current_user'] =False, None
    return render_template('home.html', logged_in=False)

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    try:
        conn = sqlite3.connect('OC/program/backend/userdata.db')
    except:
        return render_template('db_error.html')
    c = conn.cursor()
    c.execute("SELECT * FROM userdata WHERE username=?", (username,))
    row = c.fetchone()

    if row is None:
        conn.close()
        return render_template('login.html', show_error=True, error_message='User does not exist')
    elif row[1] == password:
        conn.close()
        session['current_user'], session['logged'] = username, True
        return render_template('home.html', logged_in=True)  

    else:
        conn.close()
        return render_template('login.html', show_error=True, error_message='Password is incorrect')


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']
    password2 = request.form['confirm-pass']
    
    try:
        conn = sqlite3.connect('OC/program/backend/userdata.db')
    except:
        return render_template('db_error.html')
    c = conn.cursor()

    c.execute("SELECT * FROM userdata WHERE username=?", (username,))
    row = c.fetchone()

    if password != password2: 
        return render_template('signup.html', show_error=True, error_message='Passwords do not match')

    elif row is None: 
        c.execute(f"INSERT INTO userdata (username, password) VALUES ('{username}', '{password}');")
        session['current_user'], session['logged'] = username, True

        c.execute(f"""CREATE TABLE IF NOT EXISTS {naming_convention(username)} (
            abortion TEXT,
            gun_control TEXT,
            immigration TEXT,
            healthcare TEXT,
            taxes TEXT,
            climate_change TEXT,
            lgbtq_rights TEXT,
            voting_rights TEXT,
            marijuana TEXT,
            education TEXT
        );""")
        conn.commit()
        conn.close()
        
        return render_template('home.html', logged_in=True)  

    conn.close()
    return render_template('signup.html', show_error=True, error_message='Email already exists')

@app.route('/candidates')
def candidates():
    candidates = [
        {'name': 'John Doe', 'party': 'Party A', 'experience': '10 years in office', 'key_issues': 'Education, Healthcare'},
        {'name': 'Jane Smith', 'party': 'Party B', 'experience': '5 years as mayor', 'key_issues': 'Economy, Environment'}
    ]
    return render_template('candidates.html',  candidates=candidates, logged_in=session.get('logged', False))

@app.route('/political_profile', methods=['GET', 'POST'])
def political_profile():
    if not session.get('logged', False):
        return render_template('political_profile.html', logged_in=False)
    
    username = session.get('current_user')
    user_table = naming_convention(username)
    
    conn = sqlite3.connect('OC/program/backend/userdata.db')
    c = conn.cursor()
    
    c.execute(f"SELECT * FROM {user_table}")
    profile_data = c.fetchone()
    print(f"Retrieved profile data: {profile_data}")
    conn.close()
    
    if profile_data is None:
        return render_template('political_profile.html', logged_in=True)
    else:
        columns = ['abortion', 'gun_control', 'immigration', 'healthcare', 'taxes', 
                   'climate_change', 'lgbtq_rights', 'voting_rights', 'marijuana', 'education']
        profile_dict = {columns[i]: profile_data[i] for i in range(len(columns))}
        total_score = calculate_total_score(profile_dict)
        print(total_score)
        print(profile_dict)
        return render_template('political_profile2.html', logged_in=True, profile_dict=profile_dict, total_score=total_score)
@app.route('/retake')
def retake():
    return render_template('political_profile.html', logged_in=True)
@app.route('/president')
def president():
    return render_template('president.html', candidates=candidates, logged_in=session.get('logged', False))

@app.route('/senate')
def senate():
    return render_template('senate.html', candidates=candidates, logged_in=session.get('logged', False))

@app.route('/house')
def house():
    profile_dict = {}
    if session.get('logged', False):
        username = session.get('current_user')
        user_table = naming_convention(username)
        conn = sqlite3.connect('OC/program/backend/userdata.db')
        c = conn.cursor()
        
        c.execute(f"SELECT * FROM {user_table}")
        profile_data = c.fetchone()
        if profile_data:
            columns = ['abortion', 'gun_control', 'immigration', 'healthcare', 'taxes', 
                       'climate_change', 'lgbtq_rights', 'voting_rights', 'marijuana', 'education']
            profile_dict = {columns[i]: profile_data[i] for i in range(len(columns))}
        conn.close()
    return render_template('rep.html', candidates=candidates, logged_in=session.get('logged', False), profile_dict=profile_dict)

@app.route('/propositions')
def propositions():
    return render_template('proposition.html', propositions=propositions, logged_in=session.get('logged', False))


@app.route('/submit_political_profile', methods=['POST'])
def submit_political_profile():
    if 'current_user' not in session:
        flash('User not logged in', 'error')
        return redirect(url_for('login'))

    username = session['current_user']
    user_table = naming_convention(username)

    conn = sqlite3.connect('OC/program/backend/userdata.db')
    c = conn.cursor()

    try:
        c.execute(f"SELECT COUNT(*) FROM {user_table}")
        row_count = c.fetchone()
        
        form_data = {
            "abortion": request.form.get("abortion"),
            "gun_control": request.form.get("gun_control"),
            "immigration": request.form.get("immigration"),
            "healthcare": request.form.get("healthcare"),
            "taxes": request.form.get("taxes"),
            "climate_change": request.form.get("climate_change"),
            "lgbtq_rights": request.form.get("lgbtq_rights"),
            "voting_rights": request.form.get("voting_rights"),
            "marijuana": request.form.get("marijuana"),
            "education": request.form.get("education")
        }
        print(f"Received form_data: {form_data}")
        print(f"Type of form_data: {type(form_data)}")
        columns = ['abortion', 'gun_control', 'immigration', 'healthcare', 'taxes', 'climate_change', 'lgbtq_rights', 'voting_rights', 'marijuana', 'education']
        
        values = [form_data.get(column, '') for column in columns]
        print(values)
        if row_count is not None and row_count[0] == 0:
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO {user_table} ({', '.join(columns)}) VALUES ({placeholders})"
            c.execute(query, values)
        else:
            set_clause = ', '.join([f"{column} = ?" for column in columns])
            query = f"UPDATE {user_table} SET {set_clause} WHERE rowid = 1"
            c.execute(query, values)

        conn.commit()
        
        c.execute(f"SELECT * FROM {user_table} WHERE rowid = 1")
        inserted_data = c.fetchone()
        app.logger.info(f"Retrieved profile data: {inserted_data}")
        
        conn.close()
        flash('Political profile submitted successfully', 'success')
        return redirect(url_for('political_profile'))
    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        app.logger.error(f"Database error: {str(e)}")
        flash(f'Database error: {str(e)}', 'error')
        return redirect(url_for('political_profile'))
@app.template_filter('zip')
def zip_lists(a, b):
    return zip(a, b)

#backend stuff but too lazy to move it into seperate files
def calculate_total_score(profile_dict):
    """
    Calculate the total score based on the user's political profile.
    
    :param profile_dict: A dictionary containing the user's scores for each political issue.
    :return: The total score as an integer.
    """
    scoring_issues = [
        'abortion', 'gun_control', 'healthcare', 'taxes', 
        'climate_change', 'lgbtq_rights', 'voting_rights', 
        'marijuana', 'education'
    ]
    
    total_score = 0
    
    for issue in scoring_issues:
        if issue in profile_dict:
            total_score += int(profile_dict[issue])
    
    return total_score
def naming_convention(username):
    Userid = "User_" + username
    return Userid
