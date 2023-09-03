import pickle
import cv2
import cvzone
import numpy as np
from flask import Flask, render_template, request, redirect, flash, url_for
from flask_login import UserMixin, logout_user, current_user, login_user, LoginManager, login_required
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:yourPassword@localhost/dbname'  # Database connection
app.config['SECRET_KEY'] = "my-Secret_key"

# Create a Bcrypt instance for password hashing.
bcrypt = Bcrypt(app)
# Initialize the database using SQLAlchemy.
db = SQLAlchemy(app)
login_manager = LoginManager()  # To manage Login
login_manager.init_app(app)
login_manager.login_view = "login"


class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return f'<User {self.email}>'


# Function to load the User object using user_id.
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))


@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out!")
    return redirect(url_for('login'))


@app.route("/")
def home():
    return render_template("index.html", current_user=current_user)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    current_year = datetime.now().year
    if request.method == 'POST':
            email = request.form['email']
            user = Users.query.filter_by(email=email).first()
            if user:
                if user.password == request.form["psw"]:
                    login_user(user)
                    flash('Logged in successfully.')
                    return redirect(url_for('home', current_year=current_year))
                else:
                    flash("You had entered wrong Password!")
                    return render_template("login.html", current_year=current_year)
            else:
                flash("Their is no account found on the given email!")
                return render_template("login.html", current_year=current_year)
        return render_template('login.html', current_year=current_year)



@app.route("/signup", methods=['GET', 'POST'])
def signup():
    current_year = datetime.now().year
    if request.method == 'POST':
        if 'name' in request.form and 'Dob' in request.form and 'Gender' in request.form and \
                'email' in request.form and 'phone' in request.form:
            email = request.form['email']
            user = Users.query.filter_by(email=email).first()
            if user:
                flash("You already having the account on this email!")
                return render_template("login.html", current_year=current_year)
            else:
                if request.form['retype'] == request.form['psw']:

                    User = Users(name=request.form['name'], password=request.form["psw"],
                                email=request.form['email'])
                    db.session.add(User)
                    db.session.commit()
                    return redirect(url_for("login", current_year=current_year))
                else:
                    flash("Both password doesn't matches!")
                    return render_template("signup.html", current_year=current_year)
        else:
            flash("Fill all the field!")
            return render_template("signup.html", current_year=current_year)
    return render_template('signup.html', current_year=current_year)


@app.route('/liv_pred')
def liv_pred():
    cap = cv2.VideoCapture('carParkingInput.mp4')
    with open('parkingSlotPosition', 'rb') as f:
        posList = pickle.load(f)

    width, height = 107, 48

    # Set the title of the window
    cv2.setWindowTitle("Parking Slots", "Parking Slots Detection(press q to exit)")

    def checkParkingSpace(imgPro):
        spaceCounter = 0
        for pos in posList:
            x, y = pos
            imgCrop = imgPro[y:y + height, x:x + width]
            count = cv2.countNonZero(imgCrop)
            if count < 900:
                color = (0, 255, 0)
                thickness = 5
                spaceCounter += 1
            else:
                color = (0, 0, 255)
                thickness = 2

            cv2.rectangle(img, pos, (pos[0] + width, pos[1] + height), color, thickness)

        cvzone.putTextRect(img, f'Free: {spaceCounter}/{len(posList)}', (100, 50), scale=3, thickness=5, offset=20,
                           colorR=(0, 200, 0))

    while True:
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        success, img = cap.read()
        imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        imgBlur = cv2.GaussianBlur(imgGray, (3, 3), 1)
        imgThreshold = cv2.adaptiveThreshold(imgBlur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25,
                                             16)
        imgMedian = cv2.medianBlur(imgThreshold, 5)
        kernel = np.ones((3, 3), np.uint8)
        imgDilate = cv2.dilate(imgMedian, kernel, iterations=1)
        checkParkingSpace(imgDilate)
        cv2.imshow("Parking Slots", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
