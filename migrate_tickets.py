import os
import django
import pandas as pd
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from django.db import connection

# --- Initialize Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_project.settings')
django.setup()

from tickets.models import (
    TicketsActivityticket,
    TicketsCustomer,
    TicketsReportedby,
    TicketsAnalystconsultant,
    TicketsActivitytype,
    TicketsCurrentstate,
)

# --- Excel file path ---
file_path = r"C:\Users\franc\Desktop\tickets_app\teste1.xlsx"

try:
    # --- CLEANUP: Remove existing records ---
    print("=" * 60)
    print("CLEANUP: Removing existing tickets")
    print("=" * 60)
    
    TicketsActivityticket.objects.all().delete()
    print("✅ All tickets deleted\n")
    
    # Reset ID sequence (SQLite3)
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='tickets_activityticket'")
    print("✅ ID sequence reset to start from 1\n")

    df = pd.read_excel(file_path)
    print(f"📊 {len(df)} rows found in Excel\n")

    # Normalize columns
    df.columns = df.columns.str.strip().str.lower()
    column_map = {
        'pi#': 'ticket_id',
        'customer': 'customer',
        'reported user': 'reported_user',
        'reported by': 'reported_by',
        'related pi#': 'related_ticket',
        'activity importante': 'activity_importance',
        'activity title': 'activity_title',
        'analyst consultant': 'analyst_consultant',
        'activity type': 'activity_type',
        'activity start': 'activity_start',
        'activity end': 'activity_end',
        'effort timespent': 'time_spent',
        'current state': 'current_state',
        'billing': 'billing',
    }
    df = df.rename(columns=column_map)

    # Timezone-aware dates
    for col in ['activity_start', 'activity_end']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        df[col] = df[col].apply(
            lambda x: timezone.make_aware(x) if pd.notna(x) and not timezone.is_aware(x) else x
        )

    # Clean IDs
    df['ticket_id'] = df['ticket_id'].apply(
        lambda x: str(int(x)).strip() if pd.notna(x) and str(x).strip().lower() != 'nan' else None
    )
    df['related_ticket'] = df['related_ticket'].apply(
        lambda x: str(int(x)).strip() if pd.notna(x) and str(x).strip().lower() != 'nan' else None
    )

    # --- Foreign Key caches ---
    cache_customers = {c.name: c for c in TicketsCustomer.objects.all()}
    cache_reportedby = {r.name: r for r in TicketsReportedby.objects.all()}
    cache_analysts = {a.name: a for a in TicketsAnalystconsultant.objects.all()}
    cache_types = {t.name: t for t in TicketsActivitytype.objects.all()}
    cache_states = {s.name: s for s in TicketsCurrentstate.objects.all()}

    # --- Phase 1: Create tickets and map Excel IDs ---
    tickets_to_create = []
    excel_to_db_map = {}  # Map Excel ID -> DB object
    success = skip = errors = 0

    print("=" * 60)
    print("PHASE 1: Creating Tickets")
    print("=" * 60)

    for i, row in df.iterrows():
        try:
            # Mandatory fields
            if pd.isna(row['customer']):
                skip += 1
                print(f"⚠️  Row {i+2}: Skipped - missing 'customer'")
                continue
            if pd.isna(row['activity_title']):
                skip += 1
                print(f"⚠️  Row {i+2}: Skipped - missing 'activity_title'")
                continue
            if pd.isna(row['activity_start']):
                skip += 1
                print(f"⚠️  Row {i+2}: Skipped - missing 'activity_start'")
                continue

            # --- Foreign Keys ---
            cust_name = str(row['customer']).strip()
            if cust_name not in cache_customers:
                cache_customers[cust_name] = TicketsCustomer.objects.create(name=cust_name)
            customer = cache_customers[cust_name]

            rep_by_name = str(row['reported_by']).strip() if pd.notna(row['reported_by']) else 'N/A'
            if rep_by_name not in cache_reportedby:
                cache_reportedby[rep_by_name] = TicketsReportedby.objects.create(name=rep_by_name)
            reported_by = cache_reportedby[rep_by_name]

            analyst_name = str(row['analyst_consultant']).strip() if pd.notna(row['analyst_consultant']) else 'N/A'
            if analyst_name not in cache_analysts:
                cache_analysts[analyst_name] = TicketsAnalystconsultant.objects.create(name=analyst_name)
            analyst = cache_analysts[analyst_name]

            type_name = str(row['activity_type']).strip() if pd.notna(row['activity_type']) else 'Other'
            if type_name not in cache_types:
                cache_types[type_name], _ = TicketsActivitytype.objects.get_or_create(name=type_name)
            activity_type = cache_types[type_name]

            state_name = str(row['current_state']).strip() if pd.notna(row['current_state']) else 'Open'
            if state_name not in cache_states:
                cache_states[state_name], _ = TicketsCurrentstate.objects.get_or_create(name=state_name)
            current_state = cache_states[state_name]

            # Numeric fields
            try:
                billing = Decimal(str(row['billing'])) if pd.notna(row['billing']) else None
            except (InvalidOperation, ValueError):
                billing = None
            try:
                time_spent = Decimal(str(row['time_spent'])) if pd.notna(row['time_spent']) else None
            except (InvalidOperation, ValueError):
                time_spent = None

            ticket = TicketsActivityticket(
                sysdate=timezone.now(),
                customer=customer,
                reported_user=str(row['reported_user']).strip() if pd.notna(row['reported_user']) else '',
                reported_by=reported_by,
                activity_importance=str(row['activity_importance']).strip() if pd.notna(row['activity_importance']) else 'Normal',
                activity_type=activity_type,
                activity_title=str(row['activity_title']).strip(),
                analyst_consultant=analyst,
                activity_start=row['activity_start'],
                activity_end=row['activity_end'] if pd.notna(row['activity_end']) else None,
                activity_resolution_description='',
                current_state=current_state,
                billing=billing,
                time_spent=time_spent,
            )

            tickets_to_create.append(ticket)
            if row['ticket_id']:
                excel_to_db_map[row['ticket_id']] = (len(tickets_to_create) - 1, None)

            success += 1
            if (i + 1) % 500 == 0:
                print(f"📝 {i+1}/{len(df)} processed...")

        except Exception as e:
            errors += 1
            print(f"❌ Row {i+2}: {e}")

    # Bulk insert
    TicketsActivityticket.objects.bulk_create(tickets_to_create, batch_size=500)
    print(f"\n✅ {success} tickets created with bulk_create")
    print(f"⚠️  {skip} rows skipped | ❌ {errors} errors\n")

    # Reload from DB and build Excel ID -> DB mapping
    print("📚 Reloading tickets from database...")
    all_tickets = list(TicketsActivityticket.objects.all().order_by('ticket_id'))
    
    sorted_excel_ids = sorted(excel_to_db_map.keys(), 
                              key=lambda x: excel_to_db_map[x][0])
    
    for excel_id, db_ticket in zip(sorted_excel_ids, all_tickets[:len(sorted_excel_ids)]):
        excel_to_db_map[excel_id] = (excel_to_db_map[excel_id][0], db_ticket)
    
    print(f"✅ ID map built\n")

    # --- Phase 2: Associate related_ticket ---
    print("=" * 60)
    print("PHASE 2: Associate Related Tickets")
    print("=" * 60)

    updated = not_found = 0
    tickets_to_update = []

    for i, row in df.iterrows():
        try:
            excel_id = row['ticket_id']
            related_excel_id = row['related_ticket']
            
            if not excel_id or not related_excel_id:
                continue
            
            if excel_id not in excel_to_db_map or related_excel_id not in excel_to_db_map:
                not_found += 1
                if excel_id not in excel_to_db_map:
                    print(f"ℹ️  Excel ID {excel_id} not found in map")
                if related_excel_id not in excel_to_db_map:
                    print(f"ℹ️  Related Excel ID {related_excel_id} not found in map")
                continue
            
            db_ticket = excel_to_db_map[excel_id][1]
            related_db_ticket = excel_to_db_map[related_excel_id][1]
            
            if db_ticket and related_db_ticket:
                db_ticket.related_ticket = related_db_ticket
                tickets_to_update.append(db_ticket)
                updated += 1

        except Exception as e:
            print(f"❌ Row {i+2}: error associating related_ticket - {e}")

    # Bulk update
    if tickets_to_update:
        TicketsActivityticket.objects.bulk_update(tickets_to_update, ['related_ticket'], batch_size=500)

    print(f"\n🔗 {updated} tickets linked with related_ticket")
    print(f"ℹ️  {not_found} not found\n")

    # --- Final summary ---
    print("=" * 60)
    print("📈 FINAL SUMMARY")
    print("=" * 60)
    print(f"✅ Created: {success}")
    print(f"⚠️  Skipped: {skip}")
    print(f"❌ Errors: {errors}")
    print(f"🔗 Related: {updated}")
    print(f"ℹ️  Failed associations: {not_found}")
    print(f"📊 Total Excel rows: {len(df)}")
    total_db = TicketsActivityticket.objects.count()
    print(f"📊 Total in DB: {total_db}")
    print("=" * 60)
    print("\n🎉 Migration completed successfully!\n")

except FileNotFoundError:
    print(f"❌ File '{file_path}' not found.")
except Exception as e:
    print(f"❌ Critical error: {e}")
    import traceback
    traceback.print_exc()
