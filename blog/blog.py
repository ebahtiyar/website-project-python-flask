from flask import Flask , render_template , flash ,  redirect , url_for ,session , logging ,request 
from flask_mysqldb import MySQL
from wtforms import Form , StringField ,TextAreaField ,PasswordField ,validators
from wtforms.widgets import TextArea
from passlib.hash import sha256_crypt   
from functools import wraps

#Login Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
             return f(*args, **kwargs)
        else:
             flash("Bu sayfayı görüntülemek için giriş yapınız","danger")
             return redirect(url_for("login"))


    return decorated_function


#KULLANCI FORMU
class RegisterForm(Form):
    name = StringField("İsim Soyisim:",validators=[validators.Length(min = 4 , max=25)])
    username = StringField("Kullanıcı Adı:",validators=[validators.Length(min=5, max=25 , message= "Başka bir kullanıcı adı giriniz")])
    email = StringField("Email:",validators=[validators.Email(message="Geçersiz Email")])   
    confirm  =PasswordField("Şifre Doğrula:")
    password = PasswordField("Şifre:",validators=[
        validators.DataRequired(message="Lütfen şifreyi giriniz"),
        validators.EqualTo(fieldname="confirm",message="Şifreniz uyuşmuyor...")
    ])

class LoginForm(Form):
    username = StringField("Kullanıcı Adı:")
    password = PasswordField("Şifre:")
   
 




app = Flask(__name__)
app.secret_key = "myblog"
app.config["MYSQL_HOST"]  = "localhost"
app.config["MYSQL_USER"]  = "root"
app.config["MYSQL_PASSWORD"]  = ""
app.config["MYSQL_DB"] = "myblog"
app.config["MYSQL_CURSORCLASS"] ="DictCursor"

mysql  = MySQL(app)


@app.route("/")

def index():
   
    return render_template("index.html")

@app.route("/about")

def about():
    return render_template("about.html")

@app.route("/content/<string:id>")
def content(id):
    return "Content ID :" + id 

#Register
@app.route("/register", methods = ["GET" , "POST"])

def register(): 
    form  = RegisterForm(request.form)

    if request.method == "POST" and  form.validate():               
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)


        cursor  = mysql.connection.cursor()
        sorgu =  "Insert into users(name,email,username,password) VALUES (%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        
        cursor.close()

        flash(name +" başarıyla kayıt oldunuz...","success")
 

        return redirect(url_for("index"))

    else:
         return render_template("register.html" , form = form)


@app.route("/login",methods = ["GET","POST"])
#Login
def login():
    form = LoginForm(request.form)
    
    if request.method  == "POST":

        username  = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result=cursor.execute(sorgu,(username,))

        if result > 0 :
            data =cursor.fetchone()
            real_password = data["password"]
            session["name"] = data["name"]
            if sha256_crypt.verify(password,real_password):
                flash("Başarıyla giriş yaptınız...","success")
                session["logged_in"] = True
                session["username"] = username
                



                return redirect(url_for("index"))

            else:
                flash("Şifreniz ya da Kullancı Adınız Yanlış","danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullancı bulunmuyor...","danger")
            return redirect(url_for("login"))



    return render_template("login.html",form = form)

#Logout

@app.route("/logout")

def Logout():
    session.clear()
    return redirect(url_for("index"))


#Dashboard
@app.route("/dashboard")
@login_required
def Dashboard():
    cursor  = mysql.connection.cursor()

    sorgu  = "Select * From article where author = %s"

    result  = cursor.execute(sorgu,(session["username"],))

    if result > 0 :
         articles  = cursor.fetchall()
         return render_template("Dashboard.html",articles = articles)

    else :

        return render_template("Dashboard.html")



    return render_template("dashboard.html")

#Add Article
@app.route("/addarticle", methods = ["GET", "POST"])

def addArticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu =  "Insert into article(title,author,content) VALUES (%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("MAKALE BAŞARIYLA EKLENDİ","success")
        return redirect(url_for("Dashboard"))




    return render_template("addarticle.html",form = form )


@app.route("/article/<string:id>")

def article_detail(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from article where id = %s"

    result  =  cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article_detail.html",article = article)

    else:

        return render_template("article_detail.html")



#Delete Article
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor  = mysql.connection.cursor()

    sorgu = "Select * from article where author  = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "Delete from article where id = %s"

        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        flash("Makale Silindi...","success")
        return redirect(url_for("index"))
    else:
        flash("BU MAKALEYİ SİLEMEZSİNİZ","danger")
        return redirect(url_for("index"))
     


#MAKALE_EDİT
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required

def edit_article(id):
    if request.method =="GET":

        cursor = mysql.connection.cursor()

        sorgu = "Select * from article where id = %s and author = %s"
        
        result   = cursor.execute(sorgu,(id,session["username"]))

        if result == 0 :
            flash("Böyle bir makale bulunmamaktadır")
            return  redirect(url_for("index"))
        else:

            article  = cursor.fetchone()
            form  = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)



    else:
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update article Set title = %s , content = %s where id = %s"

        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("MAKALE BAŞARIYLA GÜNCELLENDİ","success")
        return redirect(url_for("Dashboard"))

  




#ARTİCLE FORM
class ArticleForm(Form):
      title = StringField("Makale Başlığı",validators=[validators.Length(min = 5 , max = 100)])
      content = TextAreaField("Makale İçerigi",validators=[validators.Length(min = 10)] ,widget=TextArea())


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu  = "Select * From article"

    result = cursor.execute(sorgu)
    if result > 0 :
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        
        return render_template("articles.html")


    return render_template("articles.html")

@app.route("/search",methods = ["GET","POST"])
def search():

    if request.method =="GET":
        return redirect(url_for("index"))

    else:

        keyword = request.form.get("keyword")

        cursor  = mysql.connection.cursor()
        sorgu = f"Select * from article where title like '%{keyword}%'"
        result=cursor.execute(sorgu)

        if result == 0: 
            flash("Aradığınız makale bulumamadı...","warning")
            return redirect(url_for("articles"))

        else:
            articles  = cursor.fetchall()
            return render_template("articles.html",articles = articles)

    
if __name__ == "__main__":
    app.run(debug=True)     