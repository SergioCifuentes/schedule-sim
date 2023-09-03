import constant
import pandas as pd
import pyomo.environ as pe
import pyomo.gdp as pyogdp
from pyomo.environ import value

from gantt_drawer import Drawer


from itertools import product
from datetime import datetime
from dateutil.relativedelta import relativedelta

class Scheduler:
    
    def __init__(self):
        try:
            self.df_asignacion = pd.read_csv(constant.PATH+constant.ASIGNACIONES)
            self.df_asignacion.insert(0, 'id', range(0, 0 + len(self.df_asignacion)))
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
        
        self.model = self.create_model()

    def _generate_room_maximum(self):
      
        return pd.Series(self.df_salon["capacidad_maxima"].values, index=self.df_salon["id"]).to_dict()
    
    def _generate_class_students(self):
      
        return pd.Series(self.df_asignacion["numero_estudiantes"].values, index=self.df_asignacion["id"]).to_dict()

    def _generate_class_room_assignment(self, model):
        return set(filter(lambda x: self._get_assigned_students(x[0]) <= self._get_maximum_capacity(x[1]), 
                       set(model.CLASSES * model.ROOMS)))
    
    def _get_assigned_students(self, id):
        df =self.df_asignacion.loc[self.df_asignacion['id'] == id]
        return df['numero_estudiantes'].item()
    
    def _get_max_period_num(self):
        max =self.df_materias.max()['no_periodos']
        return max

    def _get_maximum_capacity(self, id):
        df=self.df_salon.loc[self.df_salon['id'] == id]
        return df['capacidad_maxima'].item()   

    def _get_number_of_periods(self):
        start= self.df_disp_salon.min()['inicio']
        start_time = datetime.strptime(start.replace('"', ''), '%H:%M')
        end= self.df_disp_salon.max()['fin']
        end_time = datetime.strptime(end.replace('"', ''), '%H:%M')
        end_time= end_time - relativedelta(minutes=constant.TIEMPO_PERIODO)
       
        count=0
        self.periods= {}
        while start_time<=end_time:
            count+=1
            self.periods[count]=start_time
            start_time= start_time + relativedelta(minutes=constant.TIEMPO_PERIODO)
        return count
    
    def _generate_room_disjunctions(self):
        classes = self.df_asignacion["id"].to_list()
        disjunctions = []
        for (class1, class2) in product(classes, classes):
            if (class1 != class2) and (class1, class2) not in disjunctions:

                disjunctions.append((class1, class2))
        return disjunctions
    
    def _generate_class_durations(self):
        periods = self.period_range
        rooms = self.df_salon["id"].to_list()
        mas_period = max(periods)
        disjunctions = []
        for index, row in self.df_asignacion.iterrows():
            id =row['id']
            num_periods=self.class_num_periods[id]
            for i in range(1, num_periods):
                for (period, room) in product(periods, rooms):
                    
                    if (period+i<=mas_period) and (id,i, period, room) not in disjunctions:
                        disjunctions.append((id, i, period, room))
        return disjunctions
    
    def _generate_classroom_periods(self):
        periods = self.period_range
        rooms = self.df_salon["id"].to_list()
        disjunctions = []
        for index, row in self.df_asignacion.iterrows():
            id =row['id']
            num_periods=self.class_num_periods[id]
            for i in range(0, num_periods):
                for (period, room) in product(periods, rooms):
                    if (id,i, period, room) not in disjunctions:
                        disjunctions.append((id, i, period, room))
        return disjunctions
    
    def _generate_room_periods(self):
        periods = self.period_range
        disjunctions = {}
        for index, row in self.df_disp_salon.iterrows():
            start= row['inicio']
            start_time = datetime.strptime(start.replace('"', ''), '%H:%M')
            end= row['fin']
            end_time = datetime.strptime(end.replace('"', ''), '%H:%M')
            for period in periods:
                if(start_time<=self.periods[period] and (self.periods[period]+relativedelta(minutes=constant.TIEMPO_PERIODO))<=end_time):
                    disjunctions[row['id_salon'],period]=1
                elif (row['id_salon'],period) not in disjunctions:
                    disjunctions[row['id_salon'],period]=0
            for i in range(self.num_periodos+1, self.num_periodos+self.max_periods):
                disjunctions[row['id_salon'],i]=0
        return disjunctions
    
    def _generate_same_semester(self):
        classes = self.df_asignacion["id"].to_list()
        periods = self.period_range
        dis_class=[]
        same_semester = []
        self.same_semester_comun = []
        for (class1, class2) in product(classes,classes):
            if(class1!=class2):
                if (self.class_semester[class1] == self.class_semester[class2]):
                    aux_comun=False
                    if(self.class_career[class1] == self.class_career[class2]):
                        if(self.class_section[class1]!=self.class_section[class2]):
                            continue
                    elif (self.class_career[class1] == "Comun" or self.class_career[class2] == "Comun"):
                        aux_comun=True
                    else:
                        continue
                    num_period = self.class_num_periods[class1]
                    if (class2, class1) in dis_class and num_period<=1:
                        continue
                    dis_class.append((class1,class2))
                    for i in range(0, num_period):
                        for j in  range(1, self.num_periodos -i+1):
                            if aux_comun:
                                self.same_semester_comun.append((class1,class2,i,j))
                            else:
                                same_semester.append((class1,class2,i,j))
        return same_semester

    def generate_class_info(self):
        self.class_num_periods={}
        self.class_semester={}
        self.class_career={}
        self.class_mandatory=[]
        self.class_section={}
        for index, row in self.df_asignacion.iterrows():
            id= row['id']
            materia=self.df_materias.loc[self.df_materias['id']==row['id_materia']]
            self.class_num_periods[id]=materia['no_periodos'].item()
            self.class_semester[id]=materia['semestre'].item()
            self.class_career[id]=materia['carrera'].item()
            if(materia['obli'].item()==True):
                self.class_mandatory.append(id)
            self.class_section[id]=row['sec']



    def create_model(self):
        model = pe.ConcreteModel()
        # List of classes IDs
        model.CLASSES = pe.Set(initialize=self.df_asignacion["id"].tolist())
        # List of teachers IDs
        model.TEACHERS = pe.Set(initialize=self.df_profesores["id"].tolist())
        # List of rooms IDs
        model.ROOMS = pe.Set(initialize=self.df_salon["id"].tolist())
        self.generate_class_info()
        self.num_periodos = self._get_number_of_periods()
        self.period_range=range(1,self.num_periodos+1)
        self.max_periods= self._get_max_period_num()
        model.PERIODS = pe.Set(initialize=self.period_range)

        model.ASSIGNMENTS= pe.Set(initialize=model.CLASSES* model.PERIODS, dimen=2)

        model.ROOM_MAX_CAPACITY = pe.Param(model.ROOMS, initialize=self._generate_room_maximum())
        
        model.CLASS_STUDENTS = pe.Param(model.CLASSES, initialize=self._generate_class_students())

        model.CLASS_DURATION = pe.Set(initialize=self._generate_class_durations(), dimen=4)
        model.CLASS_DURATION_TWO = pe.Set(initialize=self._generate_classroom_periods(), dimen=4)
        
        model.DISJUNCTIONS_ROOM_CAPACITY = pe.Set(initialize=model.CLASSES*model.PERIODS*model.ROOMS, dimen=3)
        model.ALL_PERIODS = pe.Set(initialize=range(1,self.num_periodos+self.max_periods))
        model.ROOM_PERIOD = pe.Set(initialize=model.ROOMS*model.ALL_PERIODS)
        model.PARAM_ROOM_PERIOD = pe.Param(model.ROOM_PERIOD,initialize=self._generate_room_periods())
        model.DISJUNCTIONS_ROOM = pe.Set(initialize=model.PERIODS*model.ROOMS, dimen=2)

        model.DISJUNCTIONS_TEACHER = pe.Set(initialize=model.PERIODS*model.TEACHERS, dimen=2)

        model.DISJUNCTIONS_SAME_SEMESTER = pe.Set(initialize=self._generate_same_semester(), dimen=4)

        model.DISJUNCTIONS_MANDATORY_CLASSES = pe.Set(initialize=self.class_mandatory, dimen=1)

        model.M = pe.Param(initialize=1e3*1400)  # big M
        
        #Decision Variables
        model.PERIOD_ASSIGNED = pe.Var(model.ASSIGNMENTS, domain=pe.Binary)

        model.TEACHER_ASSIGNED = pe.Var(model.ASSIGNMENTS*model.TEACHERS, domain=pe.Binary)
        
        model.ROOM_ASSIGNED = pe.Var(model.ASSIGNMENTS*model.ROOMS, domain=pe.Binary)

        #Objective
        def objective_function(model):
            return sum([model.PERIOD_ASSIGNED[clasS, period] for clasS in model.CLASSES for period in model.PERIODS])
        model.OBJECTIVE = pe.Objective(rule=objective_function, sense=pe.maximize)
        #Constraints

        def period_assignment(model, clasS):
            return sum([model.PERIOD_ASSIGNED[(clasS, period)] for period in model.PERIODS]) <= 1
        model.PERIOD_ASSIGNMENT = pe.Constraint(model.CLASSES, rule=period_assignment)

        def same_semester(model, class1, class2, num_period, period):
            return model.PERIOD_ASSIGNED[(class1, period)] + model.PERIOD_ASSIGNED[(class2, period+num_period)] <=1
        model.SAME_SEMESTER = pe.Constraint(model.DISJUNCTIONS_SAME_SEMESTER, rule=same_semester)

        def mandatory_classes(model, clasS):
            return sum([model.PERIOD_ASSIGNED[(clasS, period)] for period in model.PERIODS]) >=1
        model.MANDATORY_CLASSES = pe.Constraint(model.DISJUNCTIONS_MANDATORY_CLASSES, rule=mandatory_classes)


        def teacher_per_class(model, clasS, period):
            return model.PERIOD_ASSIGNED[(clasS, period)] == sum([model.TEACHER_ASSIGNED[(clasS, period, teachers)] for teachers in model.TEACHERS])
        model.TEACHER_PER_CLASS = pe.Constraint(model.ASSIGNMENTS, rule=teacher_per_class)

        #ROOM CONSTRAINTS

        def room_per_class(model, clasS, period):
            return model.PERIOD_ASSIGNED[(clasS, period)] == sum([model.ROOM_ASSIGNED[(clasS, period, room)] for room in model.ROOMS])
        model.ROOM_PER_CLASS = pe.Constraint(model.ASSIGNMENTS, rule=room_per_class)

        
        def no_teacher_overlap(model, period, teacher ):
            return sum([model.TEACHER_ASSIGNED[( class1, period, teacher)] for class1 in model.CLASSES]) <=1
        model.TEACHER_OVERLAP = pe.Constraint(model.DISJUNCTIONS_TEACHER, rule=no_teacher_overlap)
        
        def no_room_overlap(model, period, room ):
            return sum([model.ROOM_ASSIGNED[( class1, period, room)] for class1 in model.CLASSES]) <=1
        model.DISJUNCTIONS_ROOM_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM, rule=no_room_overlap)

        def room_capacity(model, clasS, period, room):
            return model.CLASS_STUDENTS[clasS] <= model.ROOM_MAX_CAPACITY[room] + ((1 - model.ROOM_ASSIGNED[clasS, period,room])*model.M)
        model.ROOM_CAPACITY_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM_CAPACITY, rule=room_capacity)

        def no_room_overlap_period(model, clasS, num_period, period, room ):
            return sum([model.ROOM_ASSIGNED[( class1, period+num_period, room)] for class1 in model.CLASSES]) <= 0 + ((1 - model.ROOM_ASSIGNED[clasS,period,room])*model.M)
        model.OVERLAP_PERIOD_ROOM_RULE = pe.Constraint(model.CLASS_DURATION, rule=no_room_overlap_period)

        def no_room_schedule(model, clasS, num_period, period, room ):
            return model.ROOM_ASSIGNED[( clasS, period, room)]  <= model.PARAM_ROOM_PERIOD[room,period+num_period]
        model.DISJUNCTIONS_PERIOD_ROOM_RULE = pe.Constraint(model.CLASS_DURATION_TWO, rule=no_room_schedule)

        #TEACHER CONSTRAINTS




        # pe.TransformationFactory("gdp.bigm").apply_to(model)

        return model

    def solve(self, solver_name, options=None, solver_path=None, local=True):

        if solver_path is not None:
            solver = pe.SolverFactory(solver_name, executable=solver_path)
        else:
            solver = pe.SolverFactory(solver_name)

        # TODO remove - too similar to alstom
        if options is not None:
            for key, value1 in options.items():
                solver.options[key] = value1

        if local:
            solver_results = solver.solve(self.model, tee=True)
        else:
            solver_manager = pe.SolverManagerFactory("neos")
            solver_results = solver_manager.solve(self.model, opt=solver)
        results=[]
        for (clasS, period, room) in self.model.ROOM_ASSIGNED:
            if value(self.model.ROOM_ASSIGNED[clasS, period,room]) == 1:
                results.append({"Class": clasS,
                    "Period": period,
                    "Room": room})
        self.df_times = pd.DataFrame(results)        
        for(clasS, period, teacher) in self.model.TEACHER_ASSIGNED:
            if value(self.model.TEACHER_ASSIGNED[clasS, period,teacher]) ==1:
                self.df_times.loc[self.df_times['Class'] == clasS, 'Teacher']=teacher


        all_classes = self.model.CLASSES.value_list
        classes_assigned = []
        for (clasS, period) in self.model.PERIOD_ASSIGNED:

            if value(self.model.PERIOD_ASSIGNED[clasS, period]) == 1:
                classes_assigned.append(clasS)

        classes_missed = list(set(all_classes).difference(classes_assigned))
        print("Number of cases assigned = {} out of {}:".format(len(classes_assigned), len(all_classes)))
        print("Cases assigned: ", classes_assigned)
        print("Number of cases missed = {} out of {}:".format(len(classes_missed), len(all_classes)))
        print("Cases missed: ", classes_missed)
        print("Number of constraints = {}".format(solver_results["Problem"].__getitem__(0)["Number of constraints"]))
        #self.model.SESSION_ASSIGNED.pprint()
        # print(self.df_times[self.df_times["Assignment"] == 1].to_string())
        drawer = Drawer(self.df_times, self.df_asignacion, self.df_materias, self.periods,self.class_num_periods    )
        drawer.draw()

if __name__ == "__main__":
    cbc_path = "C:\\Users\\sergi\\Documents\\Coding\\Python\\solvers\\Cbc-2.7.5-win64-intel11.1\\bin\\cbc.exe"
    ipopt_path = "C:\\Users\\sergi\\Documents\\Coding\\Python\\solvers\\Ipopt-3.14.12-win64-msvs2019-md\\bin"
    cbc_name = "cbc"
    ipopt_name = "ipopt"

    options = {"seconds": 100}
    scheduler = Scheduler()
    scheduler.solve(solver_name=cbc_name, solver_path=cbc_path, options=options)
