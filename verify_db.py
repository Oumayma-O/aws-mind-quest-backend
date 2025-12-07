"""Verify database tables"""
from sqlalchemy import inspect
from app.database.db import engine

inspector = inspect(engine)
tables = inspector.get_table_names()

print('✅ Tables in aws-mind-quest-db:')
print('-' * 50)

for table in sorted(tables):
    columns = inspector.get_columns(table)
    print(f'\n📋 {table}:')
    for col in columns:
        col_type = str(col['type'])
        nullable = 'YES' if col['nullable'] else 'NO'
        print(f'   {col["name"]:<30} {col_type:<20} (nullable={nullable})')

print('\n' + '-' * 50)
print(f'✅ Total tables created: {len(tables)}')
