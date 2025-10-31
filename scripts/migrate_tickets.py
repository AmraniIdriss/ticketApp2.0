import django
import os
import pandas as pd
from datetime import datetime
from decimal import Decimal, InvalidOperation

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticket_project.settings')
django.setup()

from tickets.models import (
    TicketsActivityticket,
    TicketsCustomer,
    TicketsReportedby,
    TicketsAnalystconsultant,
    TicketsActivitytype,
    TicketsCurrentstate
)

file_path = 'tickets_empresa.xlsx'

try:
    df = pd.read_excel(file_path)
    print(f"📊 {len(df)} linhas encontradas no Excel\n")

    column_map = {
        'PI#': 'legacy_pi',
        'Customer': 'customer',
        'Reported User': 'reported_user',
        'Reported By': 'reported_by',
        'Related PI#': 'related_pi',
        'Activity Importante': 'activity_importance',
        'Activity Title': 'activity_title',
        'analyst consultant': 'analyst_consultant',
        'activity type': 'activity_type',
        'activity start': 'activity_start',
        'activity end': 'activity_end',
        'effort timespent': 'time_spent',
        'current state': 'current_state',
        'billing': 'billing'
    }

    df = df.rename(columns=column_map)
    
    # Converter datas
    df['activity_start'] = pd.to_datetime(df['activity_start'], errors='coerce')
    df['activity_end'] = pd.to_datetime(df['activity_end'], errors='coerce')
    
    # Limpar legacy_pi e related_pi (remover espaços e NaN)
    df['legacy_pi'] = df['legacy_pi'].apply(
        lambda x: str(x).strip() if pd.notna(x) and str(x).strip() != '' and str(x).lower() != 'nan' else None
    )
    df['related_pi'] = df['related_pi'].apply(
        lambda x: str(x).strip() if pd.notna(x) and str(x).strip() != '' and str(x).lower() != 'nan' else None
    )

    success = skip = errors = duplicates = 0
    tickets_map = {}  # Mapa temporário: {PI# do Excel: objeto ticket criado}

    print("=" * 60)
    print("FASE 1: Criar Tickets")
    print("=" * 60)

    for i, row in df.iterrows():
        try:
            # Validação de campos obrigatórios
            if pd.isna(row['customer']) or pd.isna(row['activity_title']):
                print(f"⚠️  Linha {i+2}: Cliente ou título ausente — ignorada")
                skip += 1
                continue

            if pd.isna(row['activity_start']):
                print(f"⚠️  Linha {i+2}: Data de início inválida — ignorada")
                skip += 1
                continue

            # Criar/obter Foreign Keys
            customer, _ = TicketsCustomer.objects.get_or_create(
                name=str(row['customer']).strip()
            )
            
            reported_by, _ = TicketsReportedby.objects.get_or_create(
                name=str(row['reported_by']).strip() if pd.notna(row['reported_by']) else 'N/A'
            )
            
            consultant, _ = TicketsAnalystconsultant.objects.get_or_create(
                name=str(row['analyst_consultant']).strip() if pd.notna(row['analyst_consultant']) else 'N/A'
            )
            
            activity_type, _ = TicketsActivitytype.objects.get_or_create(
                type=str(row['activity_type']).strip() if pd.notna(row['activity_type']) else 'Outro'
            )
            
            current_state, _ = TicketsCurrentstate.objects.get_or_create(
                state=str(row['current_state']).strip() if pd.notna(row['current_state']) else 'Aberto'
            )

            # Converter valores Decimal com tratamento de erro
            try:
                billing = Decimal(str(row['billing'])) if pd.notna(row['billing']) else None
            except (InvalidOperation, ValueError):
                billing = None
                
            try:
                time_spent = Decimal(str(row['time_spent'])) if pd.notna(row['time_spent']) else None
            except (InvalidOperation, ValueError):
                time_spent = None

            # Criar ticket
            ticket = TicketsActivityticket.objects.create(
                sysdate=datetime.now(),
                customer=customer,
                reported_user=str(row['reported_user']).strip() if pd.notna(row['reported_user']) else '',
                reported_by=reported_by,
                activity_importance=str(row['activity_importance']).strip() if pd.notna(row['activity_importance']) else 'Normal',
                activity_type=activity_type,
                activity_title=str(row['activity_title']).strip(),
                analyst_consultant=consultant,
                activity_start=row['activity_start'],
                activity_end=row['activity_end'] if pd.notna(row['activity_end']) else None,
                activity_resolution_description='',
                current_state=current_state,
                billing=billing,
                time_spent=time_spent,
            )

            # Guardar no mapa temporário APENAS se legacy_pi existir
            if row['legacy_pi']:
                tickets_map[row['legacy_pi']] = ticket
                
            success += 1
            
            if (i + 1) % 10 == 0:  # Progresso a cada 10 linhas
                print(f"📝 Processadas {i+1}/{len(df)} linhas...")

        except Exception as e:
            errors += 1
            print(f"❌ Linha {i+2}: {str(e)}")
            continue

    print(f"\n✅ Fase 1 concluída: {success} tickets criados")
    print(f"📋 {len(tickets_map)} tickets com PI# disponíveis para associação\n")

    print("=" * 60)
    print("FASE 2: Associar Related Tickets")
    print("=" * 60)

    updated = 0
    not_found = 0
    
    for i, row in df.iterrows():
        try:
            legacy_pi = row['legacy_pi']
            related_pi = row['related_pi']

            # Só processa se ambos existirem
            if not legacy_pi or not related_pi:
                continue

            # Verificar se ambos os tickets existem no mapa
            if legacy_pi not in tickets_map:
                # Não imprime porque o ticket pode ter falhado na fase 1
                not_found += 1
                continue
                
            if related_pi not in tickets_map:
                print(f"⚠️  Linha {i+2}: Related PI# '{related_pi}' não encontrado no mapa")
                not_found += 1
                continue

            # Associar related_ticket
            ticket = tickets_map[legacy_pi]
            ticket.related_ticket = tickets_map[related_pi]
            ticket.save(update_fields=['related_ticket'])
            updated += 1

        except Exception as e:
            print(f"❌ Linha {i+2}: erro ao ligar related_ticket - {e}")
            continue

    print(f"\n🔗 Fase 2 concluída: {updated} tickets associados")
    if not_found > 0:
        print(f"ℹ️  {not_found} associações não puderam ser criadas (PI# não encontrado)")

    # Resumo final
    print("\n" + "=" * 60)
    print("📈 RESUMO FINAL")
    print("=" * 60)
    print(f"✅ Tickets criados: {success}")
    print(f"🔗 Associações (related_ticket): {updated}")
    print(f"⚠️  Linhas ignoradas: {skip}")
    print(f"❌ Erros: {errors}")
    print(f"📊 Total de linhas: {len(df)}")
    print("=" * 60)
    print("\n🎉 Migração concluída com sucesso!\n")

except FileNotFoundError:
    print(f"❌ Ficheiro '{file_path}' não encontrado.")
    print(f"💡 Certifica-te que o ficheiro está na mesma pasta do script.")
except Exception as e:
    print(f"❌ Erro crítico: {e}")
    import traceback
    traceback.print_exc()