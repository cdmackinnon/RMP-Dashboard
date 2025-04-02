import json
from sqlalchemy.sql import text
import os

path = os.path.join(os.path.dirname(__file__), '../data/school_data.json')

def seed_schools_table(db_connection):
    with open(path, 'r') as file:
        school_data = json.load(file)
    
    with db_connection.begin():
        for id, name in school_data.items():
            db_connection.execute(text("""INSERT INTO Schools (school_id, school_name)
            VALUES (:school_id, :school_name)
            ON CONFLICT (school_id) DO NOTHING"""),
                        {"school_id": int(id), "school_name": name}
                    )