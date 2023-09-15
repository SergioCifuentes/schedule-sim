from sqlalchemy import create_engine, Table, Column, Integer, MetaData, JSON,DateTime
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.orm import sessionmaker
from psycopg2.extras import Json
from psycopg2.extensions import register_adapter
import pandas as pd
import datetime
import os
import json
import psycopg2
import AlchemyEncoder
class DB:
    metadata = MetaData()
    results = Table('results', metadata,
            Column('id', Integer, primary_key=True),
            Column('date', DateTime, default=datetime.datetime.utcnow),
            Column('data', JSONB),
            extend_existing=True
        )
    engine = create_engine(os.environ['DATABASE_URL'])
    
    Session = sessionmaker(bind = engine)

    def __init__(self):
        pass

    def insertResults(self, jsonResults):
        self.metadata.reflect(bind=self.engine)
        self.metadata.create_all(self.engine)

        #insert_stmt = insert(self.results).values(data=Json(jsonResults)).returning()

        connection = self.engine.raw_connection()
        cursor = connection.cursor()
        # sql ="insert into results (data) values ( %s )" % ( json.dumps(jsonResults))
        # print(sql)
        
        #result = conn.execute("insert into results (data) values ('"+ json.dumps(jsonResults) +"')")
        cursor.execute(f'''INSERT INTO results(data) VALUES('{json.dumps(jsonResults)}')''')
        
        connection.commit()
        cursor.execute(f'''SELECT MAX(id) FROM results''')
        connection.commit()
        connection.close()
        result=cursor.fetchone()
        
        return result[0]
    
    def getResult(self, id):
        session = self.Session()
        result =session.execute(self.results.select().where( self.results.columns.id == id))
        # if (not result.exists()):
        #     return False
        dic = [dict(r) for r in result.mappings().all()]
        print(dic[0])
        return json.dumps(dic[0], indent=4, sort_keys=True, default=str)