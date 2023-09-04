from datetime import datetime
from dateutil.relativedelta import relativedelta
import constant
from itertools import product

class SetGenerator:
    def __init__(self, df_salon, df_profesores, df_disp_salon, df_assignment, df_disp_prof):

        self.df_salon = df_salon
        self.df_profesores = df_profesores
        self.df_disp_salon = df_disp_salon
        self.df_assignment = df_assignment
        self.df_disp_prof = df_disp_prof
        self.period_range=None
        self.class_num_periods=None
        self.periods=None
        self.num_periodos=None

    def set_period_range(self, period_range):
        self.period_range = period_range

    def set_class_num_periods(self, class_num_periods):
        self.class_num_periods = class_num_periods

    
    def get_number_of_periods(self,periods):
        self.periods = periods
        start= self.df_disp_salon.min()['inicio']
        start_time = datetime.strptime(start.replace('"', ''), '%H:%M')
        end= self.df_disp_salon.max()['fin']
        end_time = datetime.strptime(end.replace('"', ''), '%H:%M')
        end_time= end_time - relativedelta(minutes=constant.TIEMPO_PERIODO)
       
        count=0
        while start_time<=end_time:
            count+=1
            periods[count]=start_time
            start_time= start_time + relativedelta(minutes=constant.TIEMPO_PERIODO)
        self.num_periodos=count
        return count
    
    def generate_class_durations(self):
        
        rooms = self.df_salon["id"].to_list()
        mas_period = max(self.period_range)
        disjunctions = []
        for index, row in self.df_assignment.iterrows():
            id =row['id']
            num_periods=self.class_num_periods[id]
            for i in range(1, num_periods):
                for (period, room) in product(self.period_range, rooms):
                    
                    if (period+i<=mas_period) and (id,i, period, room) not in disjunctions:
                        disjunctions.append((id, i, period, room))
        return disjunctions
    
    def generate_teacher_durations(self):
        teachers = self.df_profesores["id"].to_list()
        mas_period = max(self.period_range)
        disjunctions = []
        for index, row in self.df_assignment.iterrows():
            id =row['id']
            num_periods=self.class_num_periods[id]
            for i in range(1, num_periods):
                for (period, teacher) in product(self.period_range, teachers):
                    
                    if (period+i<=mas_period) and (id,i, period, teacher) not in disjunctions:
                        disjunctions.append((id, i, period, teacher))
        return disjunctions
    

    def generate_classroom_periods(self):
        
        rooms = self.df_salon["id"].to_list()
        disjunctions = []
        for index, row in self.df_assignment.iterrows():
            id =row['id']
            num_periods=self.class_num_periods[id]
            for i in range(0, num_periods):
                for (period, room) in product(self.period_range, rooms):
                    if (id,i, period, room) not in disjunctions:
                        disjunctions.append((id, i, period, room))
        return disjunctions
    
    def generate_teacher_periods_two(self):
        teachers = self.df_profesores["id"].to_list()
        disjunctions = []
        for index, row in self.df_assignment.iterrows():
            id =row['id']
            num_periods=self.class_num_periods[id]
            for i in range(0, num_periods):
                for (period, teacher) in product(self.period_range, teachers):
                    if (id,i, period, teacher) not in disjunctions:
                        disjunctions.append((id, i, period, teacher))
        return disjunctions
    
    def generate_teacher_class(self, class_materia, teacher_capable):
        classes = self.df_assignment["id"].to_list()
        teachers = self.df_profesores["id"].to_list()
        disjunctions = {}
        for (clasS,teacher) in product(classes,teachers):
            materia = class_materia[clasS]
            disjunctions[(clasS,teacher)]= ((materia,teacher) in teacher_capable)
        return disjunctions
    
    def generate_room_periods(self, max_periods):
        
        disjunctions = {}
        for index, row in self.df_disp_salon.iterrows():
            start= row['inicio']
            start_time = datetime.strptime(start.replace('"', ''), '%H:%M')
            end= row['fin']
            end_time = datetime.strptime(end.replace('"', ''), '%H:%M')
            for period in self.period_range:
                if(start_time<=self.periods[period] and (self.periods[period]+relativedelta(minutes=constant.TIEMPO_PERIODO))<=end_time):
                    disjunctions[row['id_salon'],period]=1
                elif (row['id_salon'],period) not in disjunctions:
                    disjunctions[row['id_salon'],period]=0
            for i in range(self.num_periodos+1, self.num_periodos+max_periods):
                disjunctions[row['id_salon'],i]=0
        return disjunctions
    
    def generate_teacher_periods(self, max_periods):
        disjunctions = {}
        for index, row in self.df_disp_prof.iterrows():
            start= row['inicio']
            start_time = datetime.strptime(start.replace('"', ''), '%H:%M')
            end= row['fin']
            end_time = datetime.strptime(end.replace('"', ''), '%H:%M')
            for period in self.period_range:
                if(start_time<=self.periods[period] and (self.periods[period]+relativedelta(minutes=constant.TIEMPO_PERIODO))<=end_time):
                    disjunctions[row['id_profesor'],period]=1
                elif (row['id_profesor'],period) not in disjunctions:
                    disjunctions[row['id_profesor'],period]=0
            for i in range(self.num_periodos+1, self.num_periodos+max_periods):
                disjunctions[row['id_profesor'],i]=0
        return disjunctions
    
    def generate_same_semester(self, same_semester_comun, class_semester, class_career, class_section, class_num_periods):
        classes = self.df_assignment["id"].to_list()
        dis_class=[]
        same_semester = []
        
        for (class1, class2) in product(classes,classes):
            if(class1!=class2):
                if (class_semester[class1] == class_semester[class2]):
                    aux_comun=False
                    if(class_career[class1] == class_career[class2]):
                        if(class_section[class1]!=class_section[class2]):
                            continue
                    elif (class_career[class1] == "Comun" or class_career[class2] == "Comun"):
                        aux_comun=True
                    else:
                        continue
                    num_period = class_num_periods[class1]
                    if (class2, class1) in dis_class and num_period<=1:
                        continue
                    dis_class.append((class1,class2))
                    for i in range(0, num_period):
                        for j in  range(1, self.num_periodos -i+1):
                            if aux_comun:
                                same_semester_comun.append((class1,class2,i,j))
                            else:
                                same_semester.append((class1,class2,i,j))
        return same_semester
    