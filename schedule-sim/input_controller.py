import constant
import pandas as pd




df_asignacion = pd.read_csv(constant.PATH+constant.ASIGNACIONES)
df_disp_prof = pd.read_csv(constant.PATH+constant.DISP_PROF)
df_disp_salon = pd.read_csv(constant.PATH+constant.DISP_SALON)
df_materias = pd.read_csv(constant.PATH+constant.MATERIAS)
df_profesores = pd.read_csv(constant.PATH+constant.PROFESORES)
df_prof_materia = pd.read_csv(constant.PATH+constant.PROF_MATERIA)
df_salon = pd.read_csv(constant.PATH+constant.SALONES)

print(df_materias)



