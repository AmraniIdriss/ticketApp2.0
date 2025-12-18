# TicketApp – Technical Documentation

## 🎯 Application Purpose

TicketApp is an internal web application designed for **ticket management focused on activity tracking, traceability, time measurement, and client communication**. It covers the full ticket lifecycle: creation, processing, time tracking, reporting, and email notifications.

The application is intentionally **centralized, explicit, and controlled**, avoiding opaque automations. Every critical action is deliberately triggered by the user.

---

## 🧱 Overall Architecture

* **Framework**: Django (MVT architecture)
* **Functional split**:

  * `users` → authentication & access control
  * `tickets` → core business logic (tickets, states, timers)
  * `reports` → statistics & visualizations
  * `emails` → external communication

Each app has a **clear responsibility**. There is no functional overlap.

---

## 1️⃣ Users App

### Role

Strictly handles authentication and access to the application. No business logic is implemented here.

---

### register_view(request)

**Responsibility**: User account creation.

* Checks username uniqueness
* Creates the user
* Redirects to the login page

📌 Design choice: no complex registration workflow (email validation, tokens, etc.). This is intentionally minimal.

---

### login_view(request)

**Responsibility**: User authentication.

* Authenticates via `username / password`
* Explicit error handling
* Redirects to the main dashboard

📌 Advantage: predictable and transparent behavior.
📌 Drawback: no advanced security features (MFA), acceptable for an internal tool.

---

### logout_view(request)

**Responsibility**: Clean user logout.

* Invalidates the session
* Redirects to login

---

### home_view(request)

**Responsibility**: Application entry point.

* Displays the main dashboard
* Acts as the navigation hub

---

## 2️⃣ Tickets App (Core Business Logic)

### Philosophy

A ticket represents **a traceable activity over time**, defined by:

* a state
* an activity type
* an assigned analyst
* a controlled lifecycle

State transitions are **explicit and constrained**, never implicit.

---

### create_ticket(request)

**Responsibility**: Initial ticket creation.

**Key behaviors**:

* Creates a `TicketsActivityticket`
* Self-references via `related_ticket`
* Automatically starts the timer if the state is *InProgress*
* Immediately redirects to the email form

📌 Advantage: no “silent” ticket creation.
📌 Drawback: strong dependency on the email step (intentional).

---

### view_tickets(request)

**Responsibility**: Global ticket visualization.

* Displays all tickets
* Clear chronological ordering

📌 Pagination is intentionally omitted for readability over performance.

---

### edit_ticket(request)

**Responsibility**: Ticket evolution and state changes.

**Critical points**:

* Fields are displayed dynamically based on activity type
* Builds `activity_resolution_description`
* Handles controlled state transitions
* Automatically creates a **new ticket** when a mapped next state exists

📌 Advantage: clean, non-destructive history.
📌 Drawback: more complex logic to maintain.

---

### start_timer(request)

**Responsibility**: Start activity time tracking.

* Strict state validation
* Protection against double starts
* JSON response for frontend integration

📌 Technical choice: simple API, easy to consume via JavaScript.

---

### stop_timer(request)

**Responsibility**: Stop the timer and compute elapsed time.

* Precise elapsed time calculation
* Cumulative update of `time_spent`

📌 Advantage: accuracy and auditability.
📌 Drawback: relies on timestamp integrity.

---

### Models (Tickets)

The models define:

* Clients
* Activity types
* States
* Transition mappings
* The main ticket entity

📌 The entire workflow is **data-driven**, not controlled by hidden logic.

---

## 3️⃣ Reports App

### Purpose

Provide a **high-level analytical view** of activity without modifying data.

---

### api_echarts_tickets_by_analyst(request)

**Responsibility**: Feed chart visualizations.

* Date range filtering
* Grouping by analyst
* JSON output ready for ECharts

📌 Design choice: dedicated API → frontend decoupling.

---

### home_reports(request)

**Responsibility**: Statistics dashboard.

* Daily ticket aggregation
* Plotly-generated charts

📌 Drawback: server-side rendering (less scalable).
📌 Advantage: simplicity and reliability.

---

## 4️⃣ Emails App

### Philosophy

Every email is **contextual, justified, and traceable**.

---

### ticket_email_form(request, ticket_id)

**Responsibility**: Email sending interface.

* Strict validation
* First-email tracking
* Clear user feedback

📌 No email is sent without explicit human confirmation.

---

### normalize_activity_type(name)

Standardizes activity type names.

---

### parse_resolution_description(description)

Transforms free text into structured data.

📌 Advantage: rich, dynamic email content.
📌 Drawback: strongly depends on text format consistency.

---

### build_ticket_context(...)

Builds the complete email rendering context.

---

### send_ticket_email(...)

**Critical function**.

* HTML and plain-text versions
* Attachment handling
* Email state management

📌 Centralization ensures full control.
📌 Watchpoint: function complexity.

---

### EmailTicketForm

Robust email validation.

* Multiple addresses supported
* Explicit error messages

📌 Clear design choice: UX clarity over permissiveness.

---

## ✅ Conclusion

TicketApp is a **deliberately structured** application focused on **control, auditability, and business clarity**.

It prioritizes:

* readability
* traceability
* user responsibility

at the expense of:

* excessive automation
* unnecessary complexity

This positioning is fully consistent with a **professional internal tool**.
