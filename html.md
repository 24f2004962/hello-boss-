# HTML Templates Explanation (Detailed)

This document explains all the HTML files (which use the Jinja2 templating engine) in the **Trek App** project in simple terms, detailing what each page displays.

---

## 1. Base Framework Templates

### `templates/base.html`
* **Purpose:** The root HTML skeleton of every page on the site.
* **Explanation:**
  * Defines the `<head>` tag, loads Bootstrap 5 from a CDN, and includes our custom `style.css`.
  * Loads the Bootstrap JS bundle and our custom JavaScript file `main.js`.
  * Defines `{% block body %}` where child pages inject their layouts.

### `templates/layout.html`
* **Purpose:** Defines the dashboard structure (Sidebar + Main Content Area).
* **Explanation:**
  * **Flash Zone:** Displays dynamic messages (e.g. "Login successful") at the top right of the page.
  * **Sidebar (`<aside>`):** Displays the app name and sidebar navigation list. The navigation items change dynamically depending on the user's role.
  * **Header (`<header>`):** Shows the current page title and the logged-in user's name.

---

## 2. Authentication Pages (`templates/auth/`)

### `templates/auth/login.html`
* **Purpose:** The portal sign-in form.
* **Explanation:** Displays a clean login container with fields for **Email** and **Password**, and a button to register if the user doesn't have an account.

### `templates/auth/register.html`
* **Purpose:** Account registration form.
* **Explanation:** Contains form fields for **Name**, **Email**, **Contact**, **Password**, and **Confirm Password**. Includes a dropdown select menu to choose between registering as a **Trekker** (User) or **Trek Staff**.

---

## 3. Administrator Dashboard (`templates/admin/`)

* **`dashboard.html`:** The home screen for admins. Displays total treks, open treks, registered users, staff, bookings, pending approvals, and a table of the 8 most recent bookings.
* **`treks.html`:** Lists all treks. Includes filter inputs (by difficulty, status, or search query) and a table of existing treks with Edit/Delete buttons.
* **`trek_form.html`:** A shared form for adding a new trek or editing an existing one. Contains text fields for trek details and a dropdown to select a staff member to assign as a guide.
* **`trek_detail.html`:** Shows all bookings, details, and guides assigned to a specific trek.
* **`staff.html`:** Lists all registered staff members. Allows the administrator to approve pending staff registrations or suspend (blacklist) accounts.
* **`users.html`:** Lists all registered trekkers. Allows the admin to ban or restore user access.
* **`bookings.html`:** Lists all booking records in the system with status filters and page pagination.
* **`reports.html`:** Displays statistical tables showing popular treks and top active trekkers.
* **`search.html`:** Displays search results across treks, staff, and trekkers matching a search query.
* **`settings.html`:** Form allowing the administrator to update their password.

---

## 4. Staff Guide Portal (`templates/staff/`)

* **`dashboard.html`:** The home screen for assigned staff guides. Shows statistics for their treks and lists their assigned treks.
* **`manage_trek.html`:** Lets the guide update slot counts, change trek status, or mark a trek as 'Completed'.
* **`participants.html`:** Lists details and booking records for all trekkers registered for the guide's assigned treks.
* **`profile.html`:** Form for the guide to edit their contact details, bio, and password.

---

## 5. Trekker Portal (`templates/user/`)

* **`dashboard.html`:** Home screen for trekkers. Displays a list of open treks, their 5 most recent bookings, and completed trek statistics.
* **`browse.html`:** Allows trekkers to search, filter, and sort all open treks to find one to book.
* **`trek_detail.html`:** Shows detailed descriptions, price, highlights, and allows the trekker to click a **Book Trek** button.
* **`my_bookings.html`:** Displays a list of all treks currently booked or cancelled by the trekker.
* **`history.html`:** Lists all past completed treks and displays total trekking days accumulated.
* **`notifications.html`:** Lists all user alerts/notifications.
* **`profile.html`:** Form for trekkers to edit their contact details, address, and password.

---

## 6. Error Pages (`templates/errors/`)

* **`403.html`:** Shown when a user tries to access a page they don't have permission to see (e.g. a trekker trying to open the admin dashboard).
* **`404.html`:** Shown when a requested page URL doesn't exist.
* **`500.html`:** Shown when the server encounters an internal error.
