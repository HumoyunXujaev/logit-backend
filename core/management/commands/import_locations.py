import os
import re
import psycopg2
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import transaction, connection
from core.models import Location

# Настройка логгера
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import locations from world.sql into Location model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to world.sql file',
            default='world.sql'
        )
        parser.add_argument(
            '--batch-size',
            type=int, 
            help='Batch size for inserting data', 
            default=1000
        )
        parser.add_argument(
            '--countries-only',
            action='store_true',
            help='Import only countries'
        )
        parser.add_argument(
            '--states-only',
            action='store_true',
            help='Import only states'
        )
        parser.add_argument(
            '--cities-only',
            action='store_true',
            help='Import only cities'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip import if data already exists'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        batch_size = options['batch_size']
        countries_only = options['countries_only']
        states_only = options['states_only']
        cities_only = options['cities_only']
        skip_existing = options['skip_existing']
        
        if not os.path.exists(file_path):
            raise CommandError(f'File {file_path} does not exist')

        # Проверка наличия данных
        if skip_existing and Location.objects.exists():
            self.stdout.write('Locations already exist, skipping import.')
            return

        self.stdout.write('Starting import...')
        
        conn = None
        try:
            conn = psycopg2.connect(
                dbname=settings.DATABASES['default']['NAME'],
                user=settings.DATABASES['default']['USER'],
                password=settings.DATABASES['default']['PASSWORD'],
                host=settings.DATABASES['default']['HOST'],
                port=settings.DATABASES['default']['PORT'],
            )
            
            conn.autocommit = False  # Отключаем автоматические транзакции
            cursor = conn.cursor()
            
            # Импорт стран
            if not states_only and not cities_only:
                self._import_countries(cursor, file_path, batch_size)
                conn.commit()
                
            # Импорт штатов/регионов
            if not countries_only and not cities_only:
                self._import_states(cursor, file_path, batch_size)
                conn.commit()
                
            # Импорт городов
            if not countries_only and not states_only:
                self._import_cities(cursor, file_path, batch_size)
                conn.commit()
                
            self.stdout.write(self.style.SUCCESS('Successfully imported locations'))

        except Exception as e:
            if conn:
                conn.rollback()
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            logger.exception("Import failed")
            raise CommandError(f'Import failed: {str(e)}')
        
        finally:
            if conn:
                conn.close()

    def _import_countries(self, cursor, file_path, batch_size):
        """Import countries from SQL file"""
        self.stdout.write('Importing countries...')
        
        try:
            # Создаем временную таблицу с ПРАВИЛЬНЫМ типом для iso2 - varchar вместо char
            cursor.execute("""
                DROP TABLE IF EXISTS temp_countries;
                CREATE TEMP TABLE temp_countries (
                    id bigint PRIMARY KEY,
                    name varchar(100) NOT NULL,
                    iso2 varchar(10),  -- Изменено с char(2) на varchar(10)
                    latitude numeric(10,8),
                    longitude numeric(11,8),
                    capital varchar(255),
                    currency_name varchar(255),
                    region varchar(255),
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            # Читаем и извлекаем данные о странах
            country_data = self._extract_data_from_sql(file_path, 'countries')
            
            # Вставляем данные пакетами
            for i in range(0, len(country_data), batch_size):
                batch = country_data[i:i+batch_size]
                self._insert_countries(cursor, batch)
                self.stdout.write(f"Inserted countries batch {i//batch_size + 1}, {len(batch)} rows")
            
            # Копируем данные из временной таблицы в Location
            cursor.execute("""
                INSERT INTO core_location (id, name, level, code, latitude, longitude, additional_data, created_at, updated_at)
                SELECT 
                    id, 
                    name, 
                    1 as level, 
                    SUBSTRING(iso2, 1, 10) as code,  -- Убедимся, что код не превышает 10 символов
                    latitude, 
                    longitude, 
                    json_build_object('capital', capital, 'currency', currency_name, 'region', region),
                    COALESCE(created_at, NOW()),
                    COALESCE(updated_at, NOW())
                FROM temp_countries
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """)
            
            inserted = cursor.rowcount
            self.stdout.write(f"Imported {inserted} countries")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing countries: {str(e)}"))
            logger.exception("Error importing countries")
            raise

    def _import_states(self, cursor, file_path, batch_size):
        """Import states/regions from SQL file"""
        self.stdout.write('Importing states/regions...')
        
        try:
            # Создаем временную таблицу
            cursor.execute("""
                DROP TABLE IF EXISTS temp_states;
                CREATE TEMP TABLE temp_states (
                    id bigint PRIMARY KEY,
                    name varchar(255) NOT NULL,
                    country_id bigint NOT NULL,
                    state_code varchar(255),
                    latitude numeric(10,8),
                    longitude numeric(11,8),
                    type varchar(191),
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            # Читаем и извлекаем данные о штатах
            state_data = self._extract_data_from_sql(file_path, 'states')
            
            # Вставляем данные пакетами
            total_inserted = 0
            for i in range(0, len(state_data), batch_size):
                try:
                    batch = state_data[i:i+batch_size]
                    inserted = self._insert_states(cursor, batch)
                    total_inserted += inserted
                    self.stdout.write(f"Inserted states batch {i//batch_size + 1}, {inserted} rows")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error in states batch {i//batch_size + 1}: {str(e)}"))
                    # Продолжаем со следующего пакета
                    cursor.execute("ROLLBACK")
            
            # Копируем данные из временной таблицы в Location
            cursor.execute("""
                INSERT INTO core_location (id, name, parent_id, country_id, level, code, latitude, longitude, additional_data, created_at, updated_at)
                SELECT 
                    s.id, 
                    s.name, 
                    s.country_id as parent_id, 
                    s.country_id as country_id, 
                    2 as level, 
                    s.state_code as code, 
                    s.latitude, 
                    s.longitude, 
                    json_build_object('type', s.type),
                    COALESCE(s.created_at, NOW()),
                    COALESCE(s.updated_at, NOW())
                FROM temp_states s
                JOIN core_location c ON s.country_id = c.id
                WHERE c.level = 1
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """)
            
            inserted = cursor.rowcount
            self.stdout.write(f"Imported {inserted} states/regions")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing states: {str(e)}"))
            logger.exception("Error importing states")
            raise

    def _import_cities(self, cursor, file_path, batch_size):
        """Import cities from SQL file"""
        self.stdout.write('Importing cities...')
        
        try:
            # Создаем временную таблицу
            cursor.execute("""
                DROP TABLE IF EXISTS temp_cities;
                CREATE TEMP TABLE temp_cities (
                    id bigint PRIMARY KEY,
                    name varchar(255) NOT NULL,
                    state_id bigint,
                    country_id bigint NOT NULL,
                    latitude numeric(10,8),
                    longitude numeric(11,8),
                    created_at timestamp,
                    updated_at timestamp
                )
            """)
            
            # Читаем и извлекаем данные о городах
            city_data = self._extract_data_from_sql(file_path, 'cities')
            
            # Вставляем данные пакетами
            total_inserted = 0
            for i in range(0, len(city_data), batch_size):
                try:
                    batch = city_data[i:i+batch_size]
                    inserted = self._insert_cities(cursor, batch)
                    total_inserted += inserted
                    self.stdout.write(f"Inserted cities batch {i//batch_size + 1}, {inserted} rows")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Error in cities batch {i//batch_size + 1}: {str(e)}"))
                    # Продолжаем со следующего пакета
                    cursor.execute("ROLLBACK")
            
            # Импорт городов с привязкой к штатам
            cursor.execute("""
                INSERT INTO core_location (name, parent_id, country_id, level, latitude, longitude, created_at, updated_at)
                SELECT 
                    c.name, 
                    c.state_id as parent_id, 
                    c.country_id, 
                    3 as level,
                    c.latitude, 
                    c.longitude, 
                    COALESCE(c.created_at, NOW()),
                    COALESCE(c.updated_at, NOW())
                FROM temp_cities c
                JOIN core_location s ON c.state_id = s.id
                WHERE s.level = 2
                ON CONFLICT DO NOTHING
                RETURNING id
            """)
            
            inserted_with_state = cursor.rowcount
            self.stdout.write(f"Imported {inserted_with_state} cities with state reference")
            
            # Импорт городов без штатов, напрямую к странам
            cursor.execute("""
                INSERT INTO core_location (name, parent_id, country_id, level, latitude, longitude, created_at, updated_at)
                SELECT 
                    c.name, 
                    c.country_id as parent_id, 
                    c.country_id, 
                    3 as level,
                    c.latitude, 
                    c.longitude, 
                    COALESCE(c.created_at, NOW()),
                    COALESCE(c.updated_at, NOW())
                FROM temp_cities c
                LEFT JOIN core_location s ON c.state_id = s.id
                WHERE s.id IS NULL AND c.state_id IS NULL
                ON CONFLICT DO NOTHING
                RETURNING id
            """)
            
            inserted_without_state = cursor.rowcount
            self.stdout.write(f"Imported {inserted_without_state} cities without state reference")
            
            total_cities = inserted_with_state + inserted_without_state
            self.stdout.write(f"Total imported cities: {total_cities}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing cities: {str(e)}"))
            logger.exception("Error importing cities")
            raise

    def _extract_data_from_sql(self, file_path, table_name):
        """Extract data from SQL file for the specified table"""
        result = []
        pattern = r"INSERT INTO public\.{}\s+VALUES\s*\((.*?)\);".format(table_name)
        
        # Чтение файла построчно с объединением строк
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Находим все вставки для указанной таблицы
            matches = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
            
            for match in matches:
                # Разделяем несколько значений INSERT
                values = match.split('), (')
                for value in values:
                    # Очищаем значение
                    value = value.strip()
                    if not value.startswith('('):
                        value = '(' + value
                    if not value.endswith(')'):
                        value = value + ')'
                    result.append(value)
        
        self.stdout.write(f"Extracted {len(result)} {table_name} from SQL file")
        return result

    def _insert_countries(self, cursor, countries_batch):
        """Insert batch of countries into temp table"""
        if not countries_batch:
            return 0
            
        values = []
        for country in countries_batch:
            # Преобразуем строку значений в кортеж
            try:
                # Примерная позиция нужных нам полей:
                # 0=id, 1=name, 4=iso2, 19=latitude, 20=longitude, 6=capital, 8=currency_name, 12=region, 23=created_at, 24=updated_at
                # Извлекаем из строки "VALUES (1, 'name', ...)"
                fields = self._split_sql_values(country)
                
                # Проверяем минимальное количество полей
                if len(fields) < 21:
                    continue
                
                country_values = [
                    fields[0],  # id
                    fields[1],  # name
                    fields[4] if fields[4] != 'NULL' else None,  # iso2
                    fields[19] if fields[19] != 'NULL' else None,  # latitude
                    fields[20] if fields[20] != 'NULL' else None,  # longitude
                    fields[6] if fields[6] != 'NULL' else None,  # capital
                    fields[8] if fields[8] != 'NULL' else None,  # currency_name
                    fields[12] if fields[12] != 'NULL' else None,  # region
                    fields[23] if len(fields) > 23 and fields[23] != 'NULL' else None,  # created_at
                    fields[24] if len(fields) > 24 and fields[24] != 'NULL' else None  # updated_at
                ]
                
                values.append(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", country_values).decode('utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing country: {str(e)}"))
        
        if not values:
            return 0
            
        # Вставляем все значения одним запросом
        query = """
            INSERT INTO temp_countries 
            (id, name, iso2, latitude, longitude, capital, currency_name, region, created_at, updated_at)
            VALUES {} 
            ON CONFLICT (id) DO NOTHING
        """.format(','.join(values))
        
        cursor.execute(query)
        return cursor.rowcount

    def _insert_states(self, cursor, states_batch):
        """Insert batch of states into temp table"""
        if not states_batch:
            return 0
            
        values = []
        for state in states_batch:
            try:
                # Примерная позиция нужных нам полей:
                # 0=id, 1=name, 2=country_id, 4=state_code, 7=latitude, 8=longitude, 6=type, 9=created_at, 10=updated_at
                fields = self._split_sql_values(state)
                
                # Проверяем минимальное количество полей
                if len(fields) < 9:
                    continue
                
                state_values = [
                    fields[0],  # id
                    fields[1],  # name
                    fields[2],  # country_id
                    fields[4] if fields[4] != 'NULL' else None,  # state_code
                    fields[7] if fields[7] != 'NULL' else None,  # latitude
                    fields[8] if fields[8] != 'NULL' else None,  # longitude
                    fields[6] if fields[6] != 'NULL' else None,  # type
                    fields[9] if len(fields) > 9 and fields[9] != 'NULL' else None,  # created_at
                    fields[10] if len(fields) > 10 and fields[10] != 'NULL' else None  # updated_at
                ]
                
                values.append(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s,%s)", state_values).decode('utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing state: {str(e)}"))
        
        if not values:
            return 0
            
        # Вставляем все значения одним запросом
        query = """
            INSERT INTO temp_states 
            (id, name, country_id, state_code, latitude, longitude, type, created_at, updated_at)
            VALUES {} 
            ON CONFLICT (id) DO NOTHING
        """.format(','.join(values))
        
        cursor.execute(query)
        return cursor.rowcount

    def _insert_cities(self, cursor, cities_batch):
        """Insert batch of cities into temp table"""
        if not cities_batch:
            return 0
            
        values = []
        for city in cities_batch:
            try:
                # Примерная позиция нужных нам полей:
                # 0=id, 1=name, 2=state_id, 4=country_id, 6=latitude, 7=longitude, 8=created_at, 9=updated_at
                fields = self._split_sql_values(city)
                
                # Проверяем минимальное количество полей
                if len(fields) < 8:
                    continue
                
                city_values = [
                    fields[0],  # id
                    fields[1],  # name
                    fields[2] if fields[2] != 'NULL' else None,  # state_id
                    fields[4],  # country_id
                    fields[6] if fields[6] != 'NULL' else None,  # latitude
                    fields[7] if fields[7] != 'NULL' else None,  # longitude
                    fields[8] if len(fields) > 8 and fields[8] != 'NULL' else None,  # created_at
                    fields[9] if len(fields) > 9 and fields[9] != 'NULL' else None,  # updated_at
                ]
                
                values.append(cursor.mogrify("(%s,%s,%s,%s,%s,%s,%s,%s)", city_values).decode('utf-8'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error processing city: {str(e)}"))
        
        if not values:
            return 0
            
        # Вставляем все значения одним запросом
        query = """
            INSERT INTO temp_cities 
            (id, name, state_id, country_id, latitude, longitude, created_at, updated_at)
            VALUES {} 
            ON CONFLICT (id) DO NOTHING
        """.format(','.join(values))
        
        cursor.execute(query)
        return cursor.rowcount

    def _split_sql_values(self, values_line):
        """
        Split SQL values line respecting quotes and nested parentheses
        Example: "1, 'text with, comma', NULL, (1,2,3)"
        """
        result = []
        current_value = ""
        in_quotes = False
        paren_level = 0
        
        # Удаляем внешние скобки
        values_line = values_line.strip('()')
        
        for char in values_line:
            if char == "'" and (len(current_value) == 0 or current_value[-1] != '\\'):
                in_quotes = not in_quotes
                current_value += char
            elif char == '(' and not in_quotes:
                paren_level += 1
                current_value += char
            elif char == ')' and not in_quotes:
                paren_level -= 1
                current_value += char
            elif char == ',' and not in_quotes and paren_level == 0:
                result.append(current_value.strip())
                current_value = ""
            else:
                current_value += char
                
        # Добавляем последнее значение
        if current_value:
            result.append(current_value.strip())
            
        return result