import constant
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
class InputController:

    changed = False
    def __init__(self):
        load_dotenv('.env')

    def load_data(self, path=constant.PATH):
        self.engine = create_engine(os.environ['DATABASE_URL'])
        try:
            self.df_asignacion = pd.read_csv(path+constant.ASIGNACIONES)
            self.df_asignacion.insert(0, 'id', range(0, 0 + len(self.df_asignacion)))
        except FileNotFoundError:
            print("Asignacion data not found.")
            return False

        try:
            self.df_disp_prof = pd.read_csv(path+constant.DISP_PROF)
        except FileNotFoundError:
            print("Disponibilidad Profesor data not found")
            return False
        
        try:
            self.df_disp_salon = pd.read_csv(path+constant.DISP_SALON)
        except FileNotFoundError:
            print("Disponibilidad Salon data not found")
            return False

        try:
            self.df_materias = pd.read_csv(path+constant.MATERIAS)
        except FileNotFoundError:
            print("Materias data not found")
            return False

        try:
            self.df_profesores = pd.read_csv(path+constant.PROFESORES)
        except FileNotFoundError:
            print("Profesores data not found")
            return False
        
        try:
            self.df_prof_materia = pd.read_csv(path+constant.PROF_MATERIA)
        except FileNotFoundError:
            print("Profesores Materia data not found")
            return False
        try:
            self.df_salon = pd.read_csv(path+constant.SALONES)
        except FileNotFoundError:
            print("Salones data not found")
            return False
        return True
    
    def get_load_info(self):
        info = {}
        info['teachers']=int(self.df_profesores.count(numeric_only=True)['id'])
        info['careers']= int(len(pd.unique(self.df_profesores['carrera'])))
        info['rooms']=int(self.df_salon.count(numeric_only=True)['id'])
        info['classes']=int(self.df_materias.count(numeric_only=True)['id'])
        info['sections']=int(self.df_asignacion.count(numeric_only=True)['id'])
        
        return info

    def save_all(self):
        self.df_profesores.to_sql('profesor', self.engine, if_exists='replace', index=False)
            
        self.df_salon.to_sql('salon', self.engine, if_exists='replace', index=False)
            
        self.df_materias.to_sql('materia', self.engine, if_exists='replace', index=False)

        self.df_asignacion.to_sql('asignacion', self.engine, if_exists='replace', index=False)
        self.df_disp_prof.to_sql('disp_profesor', self.engine, if_exists='replace', index=False)
        self.df_prof_materia.to_sql('prof_materia', self.engine, if_exists='replace', index=False)
        self.df_disp_salon.to_sql('disp_salon', self.engine, if_exists='replace', index=False)
        connection = self.engine.raw_connection()
        cursor = connection.cursor()
        cursor.execute(f'''ALTER TABLE materia ADD PRIMARY KEY (id)''')
        cursor.execute(f'''ALTER TABLE salon ADD PRIMARY KEY (id)''')
        cursor.execute(f'''ALTER TABLE profesor ADD PRIMARY KEY (id)''')
        max = cursor.execute(f'''SELECT MAX(id)+1 FROM profesor''')
        max=cursor.fetchone()
        cursor.execute(f'''CREATE SEQUENCE IF NOT EXISTS pro_a_seq START WITH %s'''%(max[0]))
        cursor.execute(f'''ALTER TABLE profesor ALTER COLUMN id SET DEFAULT nextval(\'pro_a_seq\');''')
        connection.commit()
    def delete_teacher(self, id):
        self.df_profesores=self.df_profesores.loc[self.df_profesores['id']!=int(id)]
        self.df_prof_materia=self.df_prof_materia.loc[self.df_prof_materia["id_profesor"] != int(id)]
        self.df_disp_prof=self.df_disp_prof.loc[self.df_disp_prof["id_profesor"] != int(id)]
        self.changed=True

    def insert_teacher(self,id, data):
        row={'id':id, 'nombre':data['name'], 'carrera':data['career']}
        self.df_profesores.loc[len(self.df_profesores)] =row
        row={'id_profesor':id,'inicio':"3:00",'fin':"3:00"}
        self.df_disp_prof.loc[len(self.df_disp_prof)]=row
        self.changed=True

    def delete_class(self, id):
        self.df_materias=self.df_materias.loc[self.df_materias['id']!=int(id)]
        self.df_asignacion=self.df_asignacion.loc[self.df_asignacion["id_materia"] != int(id)]
        self.df_prof_materia=self.df_prof_materia.loc[self.df_prof_materia["id_curso"] != int(id)]
        self.changed=True

    def delete_classroom(self, id):
        self.df_salon=self.df_salon.loc[self.df_salon['id']!=int(id)]
        self.df_disp_salon=self.df_disp_salon.loc[self.df_disp_salon["id_salon"] != int(id)]
        self.changed=True

    def teacher_exists(self, id):
        return (self.df_profesores['id']==int(id)).any()
    
    def class_exists(self, id):
        return (self.df_materias['id']==int(id)).any()
    
    def classroom_exists(self, id):
        return (self.df_salon['id']==int(id)).any()
    
    def hasChanged(self):
        return self.changed






