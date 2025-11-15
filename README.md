# IAM Project - Identity and Access Management Web App

## 🔹 Description

This is a full-stack **Identity and Access Management (IAM)** web application built using **Python Flask**.
It allows users to **register, login, and access dashboards** based on their roles (Admin/User).

Admins can **view, search, and delete users**, while normal users can view their **personal dashboard**.
The project is fully functional, responsive, and deployed online for free.

---

## 🔹 Features

* **User Management**

  * Register and login
  * Role-based access control (Admin/User)
  * Session management

* **Admin Panel**

  * View all registered users
  * Search users by username
  * Delete users (except admins)
  * Interactive, professional UI with Bootstrap

* **User Dashboard**

  * Personalized welcome message
  * View role and basic info
  * Go back home easily

* **Other Features**

  * Logout functionality with a friendly page
  * Responsive design using **Bootstrap**
  * Fully functional and free to deploy online

---

## 🔹 Tech Stack

* **Backend:** Python 3.10, Flask
* **Database:** SQLite (or Replit DB for deployment)
* **Frontend:** HTML, Bootstrap CSS
* **Version Control:** Git, GitHub
* **Deployment:** Replit (Free, no credit card required)

---

## 🔹 Project Structure

```
IAM_Project/
│
├─ app.py                  # Main Flask application
├─ requirements.txt        # Python dependencies
├─ templates/              # HTML templates
│   ├─ home.html
│   ├─ login.html
│   ├─ register.html
│   ├─ admin.html
│   └─ user.html
└─ static/
    └─ style.css           # Custom CSS (if any)
```

---

## 🔹 Live Demo

Check out the live version of the app here:
[https://iam-project.username.repl.co](https://iam-project.username.repl.co)

---

## 🔹 Installation (Local Setup)

1. Clone the repository:

```bash
git clone https://github.com/Panca2022/iam-project.git
cd iam-project
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

4. Open your browser at `http://127.0.0.1:3000` to access the app.

---

## 🔹 Screenshots

*(Add screenshots of your Home Page, Admin Dashboard, User Dashboard, and Logout Page here for better presentation.)*

---

## 🔹 Future Enhancements

* Add **password hashing** for security
* Implement **profile editing** for users
* Add **pagination** for admin user list
* Add **email verification** for registration

---

## 🔹 Author

**Lalanthika S** – B.Tech Cybersecurity Enthusiast
Portfolio-ready project for campus placements and internship demonstration.
