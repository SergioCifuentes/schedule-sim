import constant
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
class InputController:

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
        print(info)
        return info

    def save_all(self):
        self.df_profesores.to_sql('profesor', self.engine, if_exists='replace', index=False)
        self.df_salon.to_sql('salon', self.engine, if_exists='replace', index=False)
        self.df_materias.to_sql('materia', self.engine, if_exists='replace', index=False)
        self.df_asignacion.to_sql('asignacion', self.engine, if_exists='replace', index=False)
        self.df_disp_prof.to_sql('disp_profesor', self.engine, if_exists='replace', index=False)
        self.df_prof_materia.to_sql('prof_materia', self.engine, if_exists='replace', index=False)
        self.df_disp_salon.to_sql('disp_salor', self.engine, if_exists='replace', index=False)








