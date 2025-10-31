from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMultiAlternatives
from django.contrib import messages
from django.template.loader import render_to_string
from django.conf import settings
import re

from .forms import EmailTicketForm
from tickets.models import TicketsActivityticket


# ----------------------------
# Configuration for templates and fields by activity type
# ----------------------------
ACTIVITY_CONFIG = {
    "DEVELOPMENT": {
        "template": "development.html",
        "fields": ["target", "observations", "development_details", "details_evidences"]
    },
    "RELEASE_DEPLOYMENT": {
        "template": "release_deployment.html",
        "fields": ["target", "observations", "development_details", "details_evidences"]
    },
    "PROJECT": {
        "template": "project.html",
        "fields": ["target", "observations", "development_details", "details_evidences"]
    },
    "MAINTENANCE_ACTIVITY": {
        "template": "maintenance_activity.html",
        "fields": ["maintenance_details", "observations", "analysis_resolution_details", "details_evidences", "recommendations"]
    },
    "SOLICITATION": {
        "template": "solicitation.html",
        "fields": ["request_details", "observations", "resolution_details", "details_evidences", "recommendations"]
    },
    "INCIDENT": {
        "template": "incident.html",
        "fields": ["reported_issue", "observations", "analysis", "root cause", "resolution details", "details evidences", "recommendations"]
    },
    "TROUBLE_TICKET": {
        "template": "trouble_ticket.html",
        "fields": ["problem_details", "error_description", "resolution_investigation_details", "details_evidences", "recommendations"]
    },
    "SANITY_CHECK": {
        "template": "sanity_check.html",
        "fields": []
    },
}


def ticket_email_form(request, ticket_id):
    """View to handle the email form for sending ticket-related emails"""
    ticket = get_object_or_404(TicketsActivityticket, ticket_id=ticket_id)

    if request.method == 'POST':
        form = EmailTicketForm(request.POST, request.FILES)

        if form.is_valid():
            # Parse and clean email addresses (TO, CC, BCC)
            to_emails = [e.strip() for e in form.cleaned_data['to_email'].split(',') if e.strip()]
            cc_emails = [e.strip() for e in form.cleaned_data.get('cc_email', '').split(',') if e.strip()]
            bcc_emails = [e.strip() for e in form.cleaned_data.get('bcc_email', '').split(',') if e.strip()]
            
            # Check if this is the first email for the ticket
            first_email = not ticket.first_email_sent

            # Send the email
            result = send_ticket_email(
                ticket_id=ticket_id,
                recipient_emails=to_emails,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
                attachment=form.cleaned_data.get('attachment'),
                first_email=first_email  # 🔹 Pass this flag to handle first-email state
            )

            # Mark as first email sent if successful
            if first_email and result['success']:
                ticket.first_email_sent = True
                ticket.save()

            # Show feedback to the user
            if result['success']:
                messages.success(request, 'Email sent successfully!')
                return redirect('view_tickets')
            else:
                messages.error(request, f'Error: {result["message"]}')
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = EmailTicketForm()

    return render(request, 'emails/ticket_email_form.html', {'form': form, 'ticket': ticket})


def normalize_activity_type(name):
    """Normalize activity type name (remove special characters and spaces)"""
    return re.sub(r'[^A-Z0-9 ]', '', name.upper()).strip().replace(' ', '_')


def parse_resolution_description(description):
    """
    Extracts structured fields from 'activity_resolution_description'.
    Supports different newline formats for consistent parsing.
    """
    if not description:
        return {}
    
    data = {}
    
    # Normalize line breaks
    description = description.replace('\r\n', '\n').replace('\r', '\n')
    
    # Expected fields and regex patterns
    field_patterns = {
        'target': r'Target:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'observations': r'Observations:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'development_details': r'Development Details:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'details_evidences': r'Details Evidences:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'analysis_resolution_details': r'Analysis Aesolution Details:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'recommendations': r'Recommendations:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'reported_issue': r'Reported Issue:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'root cause': r'Root Cause:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'problem_details': r'Problem details:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'error_description': r'Error Description:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
        'resolution_investigation_details': r'Resolution Investigation Details:\s*(.+?)(?=\n\n|\n[A-Z][a-z]+:|$)',
    }
    
    # Extract data for each defined field
    for field, pattern in field_patterns.items():
        match = re.search(pattern, description, re.DOTALL | re.IGNORECASE)
        if match:
            data[field] = match.group(1).strip()
    
    print(f"🔍 Parsed data: {data}")
    return data


def build_ticket_context(ticket, activity_type_name, email_state_override=None):
    """
    Builds the base email context + specific fields depending on activity_type.
    Optionally overrides the current state for email content.
    """
    context = {
        'ticket_id': ticket.ticket_id,
        'customer': ticket.customer,
        'activity_title': ticket.activity_title,
        'analyst_consultant': ticket.analyst_consultant,
        'activity_type': ticket.activity_type,
        'activity_importance': ticket.activity_importance or 'Normal',
        'sysdate': ticket.sysdate,
        'current_state': email_state_override or ticket.current_state,
        'activity_resolution_description': ticket.activity_resolution_description or '',
        'time_spent': ticket.time_spent
    }
    
    # Get configuration for this activity type
    config = ACTIVITY_CONFIG.get(activity_type_name, {})
    
    # 🔹 Parse structured resolution description
    resolution_data = parse_resolution_description(ticket.activity_resolution_description)
    
    # Fill context fields dynamically
    for field in config.get('fields', []):
        # Try to get from ticket model first
        value = getattr(ticket, field, None)
        
        # If not found, check parsed resolution description
        if not value:
            value = resolution_data.get(field)
        
        # Default to 'N/A' if missing or empty
        context[field] = value if value and str(value).strip() else 'N/A'
    
    return context


def send_ticket_email(ticket_id, recipient_emails=None, cc_emails=None, bcc_emails=None, attachment=None, first_email=False):
    """Core function to build and send the email for a specific ticket."""
    if not recipient_emails:
        return {'success': False, 'message': 'At least one recipient is required'}

    try:
        ticket = TicketsActivityticket.objects.get(ticket_id=ticket_id)

        # Normalize activity type and get config
        activity_type_name = normalize_activity_type(ticket.activity_type.name)
        config = ACTIVITY_CONFIG.get(activity_type_name)
        
        if not config:
            return {'success': False, 'message': f'No template configured for: {ticket.activity_type.name}'}

        # Determine which ticket state should appear in the email
        email_state = ticket.current_state
        if first_email and ticket.current_state.name == "⇶ Inprogress | OnGoing":
            from tickets.models import TicketsCurrentstate
            email_state = get_object_or_404(TicketsCurrentstate, name="✎ Open")
        
        # Build email context dynamically
        context = build_ticket_context(ticket, activity_type_name, email_state_override=email_state)

        # Render HTML content
        html_content = render_to_string(f'emails/{config["template"]}', context)

        # Generate dynamic plain text fallback
        def generate_plain_text_from_context(ctx, cfg):
            lines = [
                f"Ticket {ctx['ticket_id']} - {ctx['customer'].name}",
                f"Activity: {ctx['activity_title']}",
                f"Analyst: {ctx['analyst_consultant'].name}",
                f"Importance: {ctx['activity_importance']}",
                f"Status: {ctx['current_state'].name}",
                f"Time Spent: {ctx.get('time_spent', 'N/A')}"
            ]
            for field in cfg.get('fields', []):
                value = ctx.get(field, None)
                if value and str(value).strip() != 'N/A':
                    lines.append(f"{field.replace('_', ' ').title()}: {value}")

            resolution_fields = getattr(ctx, 'activity_resolution_description', None)
            if resolution_fields:
                for key, value in resolution_fields.items():
                    if value and str(value).strip() != 'N/A':
                        lines.append(f"{key.replace('_', ' ').title()}: {value}")
                        
            return "\n".join(lines)

        text_content = generate_plain_text_from_context(context, config)

        # Create and send email
        email = EmailMultiAlternatives(
            subject=f"{activity_type_name}#{ticket.ticket_id} : {ticket.customer.name} | {ticket.activity_title}",
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipient_emails,
            cc=cc_emails or [],
            bcc=bcc_emails or []
        )
        email.attach_alternative(html_content, "text/html")

        # Attach file if provided
        if attachment:
            email.attach(attachment.name, attachment.read(), attachment.content_type)

        # Send email
        email.send()

        return {'success': True, 'message': f'Email sent to {len(recipient_emails)} recipient(s)'}

    except TicketsActivityticket.DoesNotExist:
        print(f"❌ Ticket #{ticket_id} not found")
        return {'success': False, 'message': f'Ticket #{ticket_id} not found'}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'message': f'Error: {str(e)}'}

