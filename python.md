# Python Backend Explanation (Detailed)

This document explains all Python files in the **Trek App** project in simple terms, detailing what each section of code does.

---

## 1. `database.py`
This is a small file that defines the database connection object.
* `db = SQLAlchemy()`: Creates a shared database object. We keep this in a separate file so other files can import `db` without causing circular import loops.

---

## 2. `config/settings.py`
This file stores settings and configuration constants for the Flask app.
* `SECRET_KEY`: Used by Flask to encrypt session cookies (identifying logged-in users).
* `SQLALCHEMY_DATABASE_URI`: Points to the SQLite database file (`sqlite:///trekking.db`), which will be created automatically in the `instance/` folder.
* `SQLALCHEMY_TRACK_MODIFICATIONS = False`: Disables a legacy feature in SQLAlchemy to save memory.
* `ITEMS_PER_PAGE = 10`: The default number of items shown per page in tables.

---

## 3. `models.py`
This file defines the tables (or "models") inside our SQLite database.

### `User` Table
Stores admins, staff guides, and regular trekkers (users).
* `role`: Determines what permissions a user has ('admin', 'staff', 'user').
* `status`: Accounts start as 'active' (or 'pending' for staff awaiting approval). If an admin bans someone, status becomes 'blacklisted'.
* `bookings`: Connects the user to their booking records.

### `Trek` Table
Stores information about the treks.
* `available_slots`: The number of remaining open spots. When a user books a trek, this number decreases by 1.
* `status`: 'Pending' (draft), 'Approved' (ready), 'Open' (open to book), 'Closed', or 'Completed'.
* `staff_id`: Connects the trek to a staff guide assigned to run it.

### `Booking` Table
Links a specific `User` (trekker) to a specific `Trek`.
* `status`: 'Booked' (active), 'Cancelled' (freed), or 'Completed' (trek finished).

### `Notification` Table
Stores simple alert messages for users (e.g. "Your booking is confirmed").

---

## 4. `helpers.py`
Contains utility functions and security checks used throughout the website.

* `@login_required`: A custom check placed before routes. If a user is not logged in (`user_id` not in session), it redirects them to the login page.
* `@role_required(*roles)`: Checks if the logged-in user matches the allowed roles (e.g., admin or staff). If not, it blocks them with an error.
* `get_current_user()`: Checks the active session to load the current logged-in user details from the database.
* `validate_password(password, confirm)`: Validates registration password requirements (at least 6 characters and matching confirmation).
* `validate_email_free(email)`: Ensures no duplicate accounts are created with the same email.

---

## 5. `app.py`
This is the starting point of the application.

* `create_app()`: Sets up Flask, registers the configuration settings, and links the database.
* `app.register_blueprint(...)`: Organizes different sections of the website (Admin, Staff, User, Auth, API) into separate files (Blueprints) for clean organization.
* `@app.context_processor`: Injects the unread notification count so it is displayed in the navigation bar on every single page automatically.
* `seed_admin()`: Creates a default administrator account (`admin@trek.com` with password `admin123`) on startup if it doesn't already exist.
* `seed_sample_data()`: Automatically seeds some initial treks (like Everest Base Camp and Roopkund) so the site isn't blank when you open it for the first time.

---

## 6. Route Blueprints (Inside the `routes/` Folder)

### `routes/auth.py`
Handles user accounts.
* `/login`: Verifies user email and password against database hashes using `check_password_hash`. Checks if accounts are blacklisted or pending staff approval.
* `/register`: Creates new user records. If registering as a staff member, sets status to `pending` (needs admin approval).
* `/logout`: Clears the session variables, logging the user out.

### `routes/admin.py`
Handles all administrator operations.
* `/dashboard`: Summarizes site statistics (total users, treks, bookings).
* `/treks`, `/treks/add`, `/treks/edit/<id>`, `/treks/delete/<id>`: Full CRUD (Create, Read, Update, Delete) management of treks.
* `/staff`, `/staff/approve/<id>`, `/staff/toggle/<id>`: Reviews and approves registering staff guides, or blacklists them.
* `/users`, `/users/toggle/<id>`: Manages regular trekkers and allows blacklisting/restoring them.
* `/reports`: Displays data reports (most active users, most popular treks).

### `routes/admin.py` (Continued)
* `/bookings`: Manages and lists all booked records.
* `/search`: Global search feature for finding treks, trekkers, and staff guides.
* `/settings`: Allows the administrator to change their login password.

### `routes/staff.py`
Handles the dashboard for assigned staff guides.
* `/dashboard`: Shows treks assigned to the logged-in guide.
* `/trek/<id>`: Lists participants booked for a trek.
* `/trek/<id>/update`: Allows updating slot availability or trek status.
* `/trek/<id>/complete`: Marks a trek as completed, which automatically updates all booked slots to 'Completed' and notifies the trekkers.

### `routes/user.py`
Handles operations for regular trekkers.
* `/browse`: Lets trekkers search treks by keyword, location, difficulty, and sort by price or date.
* `/trek/<id>`: Shows details, price, highlights, and a booking form.
* `/book/<id>`: Deducts 1 from available slots and creates a booking entry.
* `/cancel/<id>`: Cancels a booking, restoring the slot count.
* `/notifications`: Displays all alerts and marks them as read.

### `routes/api.py`
Exposes JSON endpoints for potential frontend dynamic components (e.g. chart statistics).
