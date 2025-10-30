# This file defines a custom filter for Django templates.
# Filters let us add new features to our HTML templates.
# We put this file in a folder called "templatetags" so Django knows where to find it.

from django import template

# This line sets up Django to recognize our custom filters.
register = template.Library()

# This filter lets us get the value of any field from a ticket using its name.
# For example, if we want to show the "observations" field, we can use this filter in the template.
# This is useful because the fields we show depend on the type of activity for each ticket.
@register.filter
def get_field(obj, field_name):
    # This gets the value of the field with the name we provide.
    # If the field doesn't exist, it returns an empty string.
    return getattr(obj, field_name, "")

# Why is this file in a separate folder?
# Django only looks for custom filters in files inside a folder called "templatetags" in your app.
# If you put this code in views.py or another file, Django won't find it and you can't use the filter in your templates.
# By keeping it here, you make sure your templates can use the filter to show dynamic fields for each ticket.