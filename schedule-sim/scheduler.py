import constant
import pandas as pd
import pyomo.environ as pe

class Scheduler:
    
    def __init__(self):
        try:
            self.df_asignacion = pd.read_csv(constant.PATH+constant.ASIGNACIONES)
        except FileNotFoundError:
            print("Asignacion data not found.")

        try:
            self.df_disp_prof = pd.read_csv(constant.PATH+constant.DISP_PROF)
        except FileNotFoundError:
            print("Disponibilidad Profesor data not found")
        
        try:
            self.df_disp_salon = pd.read_csv(constant.PATH+constant.DISP_SALON)
        except FileNotFoundError:
            print("Disponibilidad Salon data not found")

        try:
            self.df_materias = pd.read_csv(constant.PATH+constant.MATERIAS)
        except FileNotFoundError:
            print("Materias data not found")

        try:
            self.df_profesores = pd.read_csv(constant.PATH+constant.PROFESORES)
        except FileNotFoundError:
            print("Profesores data not found")
        
        try:
            self.df_prof_materia = pd.read_csv(constant.PATH+constant.PROF_MATERIA)
        except FileNotFoundError:
            print("Profesores Materia data not found")

        try:
            self.df_salon = pd.read_csv(constant.PATH+constant.SALONES)
        except FileNotFoundError:
            print("Salones data not found")

    def create_model(self):
        model = pe.ConcreteModel()
        
        # Model Data

        
