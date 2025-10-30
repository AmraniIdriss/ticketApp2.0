from django.db import models



# --------- Campos base ---------
class TicketsCustomer(models.Model):
    name = models.CharField(unique=True, max_length=200)
    
    client = models.ForeignKey(
        'users.Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_customers'
    )

    
class TicketsReportedby(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_reportedby'

    def __str__(self):
        return self.name


class TicketsActivitytype(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_activitytype'

    def __str__(self):
        return self.name


class TicketsActivitytype2(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_activitytype2'

    def __str__(self):
        return self.name


class TicketsAnalystconsultant(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_analystconsultant'

    def __str__(self):
        return self.name


class TicketsCurrentstate(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_currentstate'

    def __str__(self):
        return self.name

class TicketsActivityimportance(models.Model):
    name = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.name


# --------- Novos campos ---------
class TicketsCurrentstate2(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_currentstate2'

    def __str__(self):
        return self.name


class TicketsPendingstate(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_pendingstate'

    def __str__(self):
        return self.name


class TicketsFinishstate(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_finishstate'

    def __str__(self):
        return self.name


class TicketsNextstate(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_nextstate'

    def __str__(self):
        return self.name


class TicketsSpecialstate(models.Model):
    name = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'tickets_specialstate'

    def __str__(self):
        return self.name
    
class TicketsSummary(models.Model):
    ticket_id = models.IntegerField()  
    customer = models.ForeignKey('TicketsCustomer', on_delete=models.SET_NULL, null=True)    




# --------- Ticket principal ---------
class TicketsActivityticket(models.Model):
    ticket_id = models.AutoField(db_column='ticket_ID', primary_key=True)
    
    sysdate = models.DateTimeField()
    
    customer = models.ForeignKey(
        TicketsCustomer,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activitytickets'
    )
    reported_user = models.CharField(max_length=100)
    
    activity_importance = models.CharField(max_length=100)
    
    activity_type = models.ForeignKey(TicketsActivitytype, on_delete=models.SET_NULL, null=True)
    
    activity_type_2 = models.ForeignKey(TicketsActivitytype2, on_delete=models.SET_NULL, blank=True, null=True)
    
    activity_title = models.CharField(max_length=100)
    
    analyst_consultant = models.ForeignKey(TicketsAnalystconsultant, on_delete=models.SET_NULL, null=True)
    
    activity_start = models.DateTimeField(blank=True, null=True)
    
    activity_end = models.DateTimeField(blank=True, null=True)
    
    activity_resolution_description = models.TextField()
    
    current_state = models.ForeignKey(TicketsCurrentstate, on_delete=models.SET_NULL, null=True, related_name='current_state')
    
    current_state2 = models.ForeignKey(TicketsCurrentstate2, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_state2')
    
    billing = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)
    
    reported_by = models.ForeignKey(TicketsReportedby, on_delete=models.SET_NULL, null=True)
    
    time_spent = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    next_state = models.ForeignKey(TicketsNextstate, on_delete=models.SET_NULL, blank=True, null=True)
    
    related_ticket = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_tickets'
    )

    first_email_sent = models.BooleanField(default=False)

    class Meta:
        db_table = 'tickets_activityticket'

    def __str__(self):
        return f"{self.ticket_id} - {self.activity_title}"
    

