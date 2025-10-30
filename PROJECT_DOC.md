# Project Documentation

## 📑 Table of Contents
- [1. Users App](#1-users-app)  
  - [register_view(request)](#register_viewrequest)  
  - [login_view(request)](#login_viewrequest)  
  - [logout_view(request)](#logout_viewrequest)  
  - [home_view(request)](#home_viewrequest)  
- [2. Tickets App](#2-tickets-app)
  - [create_ticket(request)](#create_ticketrequest)  
  - [view_tickets(request)](#view_ticketsrequest)  
  - [edit_ticket(request)](#edit_ticketrequest)  
  - [start_timer(request)](#start_timerrequest)  
  - [stop_timer(request)](#stop_timerrequest)  
  - [Models](#models)  
- [3. Reports App](#3-reports-app)
  - [api_echarts_tickets_by_analyst(request)](#api_echarts_tickets_by_analystrequest)  
  - [home_reports(request)](#home_reportsrequest)  
- [4. Emails App](#4-emails-app)
  - [ticket_email_form(request, ticket_id)](#ticket_email_formrequest-ticket_id)  
  - [normalize_activity_type(name)](#normalize_activity_typename)  
  - [parse_resolution_description(description)](#parse_resolution_descriptiondescription)  
  - [build_ticket_context(ticket, activity_type_name, email_state_override=None)](#build_ticket_contextticket-activity_type_name-email_state_overridenone)  
  - [send_ticket_email(ticket_id, recipient_emails, cc_emails, bcc_emails, attachment=None, first_email=False)](#send_ticket_emailticket_id-recipient_emails-cc_emails-bcc_emails-attachmentnone-first_emailfalse)  
  - [Forms](#forms)  
    - [EmailTicketForm](#emailticketform)  
    - [_validate_emails(emails_string, required=False)](#_validate_emailsemails_string-requiredfalse)

---

## 1️⃣ Users App
### Views
#### register_view(request)
**Purpose:** Handles user registration.  
**Behaviour:**  
- Checks if username exists.  
- Creates a new user.  
- Redirects to the login page.  
- Renders registration template (`users/register.html`).

#### login_view(request)
**Purpose:** Handles user login.  
**Behaviour:**  
- Checks if the request method is `POST`.  
- Retrieves `'username'` and `'password'` from request data.  
- If authentication succeeds:  
  - Logs in the user using `login()`.  
  - Redirects to the home page (`/`).  
- If authentication fails:  
  - Displays an error message (`messages.error`).  
- If request method is not `POST` or login fails:  
  - Renders the login template (`users/login.html`).

#### logout_view(request)
**Purpose:** Handles user logout.  
**Behaviour:**  
- Logs out the current user using `logout()`.  
- Redirects to the login page (`users/login.html`).  
- Displays a confirmation message (`messages.success`).

#### home_view(request)
**Purpose:** Displays the main dashboard for authenticated users.  
**Behaviour:**  
- Fetches tickets or other dashboard data.  
- Renders the dashboard template (`users/home.html`).

---

## 2️⃣ Tickets App
### Views

#### create_ticket(request)
**Purpose:** Handles the creation of a new ticket and redirects to the email form.  
**Behaviour:**  
- Checks if request method is `POST`.  
- Retrieves form data.  
- Fetches related model objects using `get_object_or_404`.  
- Creates a new `TicketsActivityticket` record.  
- Sets `related_ticket` to itself.  
- If state is `"⇶ Inprogress | OnGoing"`, starts the timer automatically.  
- Redirects to email form (`ticket_email_form`) after creation.  
- If request method is `GET`, renders ticket creation form with dropdown lists.  

**Template rendered:** `tickets/create_ticket.html`.

#### view_tickets(request)
**Purpose:** Displays a list of all existing tickets.  
**Behaviour:**  
- Retrieves all tickets ordered by `ticket_id`.  
- Renders the ticket list page.  

**Template rendered:** `tickets/view_tickets.html`.

#### edit_ticket(request)
**Purpose:** Allows editing an existing ticket and may create a new ticket depending on state transitions.  
**Behaviour:**  
- Checks if the ticket is in a non-editable state.  
- Dynamically determines which fields to show based on `activity_type`.  
- On `POST`:  
  - Validates new consultant and state.  
  - Updates ticket fields and builds `activity_resolution_description`.  
  - Updates analyst consultant and current state.  
  - Creates a new ticket if state has a mapped next state (`STATE_MAPPING`).  
  - Redirects to email form if state triggers an email (`EMAIL_TRIGGER_STATES`).  
- On `GET`:  
  - Renders edit form with relevant fields and available states.  

**Template rendered:** `tickets/edit_ticket.html`.

#### start_timer(request)
**Purpose:** Starts the activity timer for a ticket.  
**Behaviour:**  
- Validates that the ticket exists and is not already finished or running.  
- Ensures ticket state allows starting timer.  
- Sets `activity_start` to current time and clears `activity_end`.  
- Returns JSON response with status and timestamp.  

#### stop_timer(request)
**Purpose:** Stops the activity timer for a ticket.  
**Behaviour:**  
- Validates that the ticket exists and timer was started.  
- Optionally updates ticket state.  
- Sets `activity_end` to current time.  
- Calculates elapsed time and updates `time_spent`.  
- Returns JSON response with status, timestamps, and total time spent.

### Models
**Purpose:** The tickets app contains the models that define the core structure of the ticket system, including clients, activity types, states, transitions, and the main ticket table. It serves as the foundation for creating, editing, listing, and managing the lifecycle of each ticket.

---

## 3️⃣ Reports App
### Views

#### api_echarts_tickets_by_analyst(request)
**Purpose:** Provides JSON data for ECharts visualizations, showing the number of tickets per analyst.  
**Behaviour:** 
- Accepts optional GET parameters: `start_date`, `end_date`, `current_state`.  
- Filters tickets based on provided parameters.  
- Aggregates ticket counts grouped by analyst.  
- Returns a JSON response in the format `[{name, value}, ...]` suitable for charts.

#### home_reports(request)
**Purpose:** Displays ticket statistics and charts for the web dashboard.  
**Behaviour:** 
- Accepts optional GET parameters: `start_date`, `end_date`, `current_state`, `analyst_consultant`.  
- Filters tickets according to the provided parameters.  
- Aggregates daily ticket counts.  
- Generates a Plotly bar chart for tickets per day.  
- Renders the `reports/home_reports.html` template with chart HTML.

---

## 4️⃣ Emails App
### Views

#### ticket_email_form(request, ticket_id)
**Purpose:** Handles the email form for sending ticket-related emails.  
**Behaviour:**  
- Accepts POST and GET requests.  
- On POST:
    - Validates the form (`EmailTicketForm`).  
    - Cleans and parses email addresses (TO, CC, BCC).  
    - Determines if it is the first email for the ticket.  
    - Sends the email using `send_ticket_email()`.  
    - Marks the ticket as having its first email sent if successful.  
    - Displays success or error messages via `messages`.  
- On GET:
    - Renders the email form template.  

**Template rendered:** `emails/ticket_email_form.html`.

### Utility Functions

#### normalize_activity_type(name)
**Purpose:** Standardizes activity type names by removing special characters and spaces.

#### parse_resolution_description(description)
**Purpose:** Extracts structured fields from `activity_resolution_description` for use in email templates.

#### build_ticket_context(ticket, activity_type_name, email_state_override=None)
**Purpose:** Builds the context dictionary for rendering email templates, combining ticket data and parsed resolution fields.

#### send_ticket_email(ticket_id, recipient_emails, cc_emails, bcc_emails, attachment=None, first_email=False)
**Purpose:** Core function that builds and sends the email for a specific ticket, including HTML and plain-text versions, attachments, and dynamic state handling.

### Forms

#### EmailTicketForm
**Purpose:** Handles user input for sending emails related to tickets.  
**Behaviour:**  
- Provides fields for To, CC, BCC, and optional attachment.  
- Validates all email fields individually using Django’s `validate_email`.  
- Ensures the To field is mandatory, while CC and BCC are optional.  
- Supports multiple emails separated by commas.  
- Provides user-friendly error messages for invalid or missing emails.

**Fields:**  
- `to_email` – Required; comma-separated list of recipient emails.  
- `cc_email` – Optional; comma-separated list of CC emails.  
- `bcc_email` – Optional; comma-separated list of BCC emails.  
- `attachment` – Optional file upload.

#### _validate_emails(emails_string, required=False)
**Purpose:** Internal function to split, clean, and validate multiple email addresses.
