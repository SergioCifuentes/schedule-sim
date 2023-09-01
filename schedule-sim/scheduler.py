import constant
import pandas as pd
import pyomo.environ as pe
import pyomo.gdp as pyogdp
from pyomo.environ import value
import matplotlib.pyplot as plt
import matplotlib.cm as cm

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
    
    # def _generate_class_durations(self):
    #     dict ={}
    #     for index, row in self.df_asignacion.iterrows():
    #         num_periods=(self.df_materias.loc[self.df_materias['id']==row['id_materia']])['no_periodos'].item()
    #         for i in range(1, num_periods):
    #             dict[row['id']]= i 
    #     return dict

    def _get_number_of_periods(self):
        start= self.df_disp_salon.min()['inicio']
        start_time = datetime.strptime(start.replace('"', ''), '%H:%M')
        end= self.df_disp_salon.max()['fin']
        end_time = datetime.strptime(end.replace('"', ''), '%H:%M')
        end_time= end_time - relativedelta(minutes=constant.TIEMPO_PERIODO)
       
        count=0
        self.periods= []
        while start_time<=end_time:
            count+=1
            self.periods.append([count, start_time])
            start_time= start_time + relativedelta(minutes=constant.TIEMPO_PERIODO)
        return count
    
    def _genereate_teacher_periods(self):
        for period in self.periods:
            pass
    
    # def _generate_disjunctions(self):
    #     classes = self.df_asignacion["id"].to_list()
    #     rooms = self.df_salon["id"].to_list()
    #     teachers =self.df_profesores["id"].to_list()
    #     disjunctions = []
    #     for (class1, class2, room, teacher1, teacher2) in product(classes, classes, rooms, teachers, teachers):
    #         if (class1 != class2) and (teacher1!=teacher2) and (class1, class2, room, teacher1, teacher2) not in disjunctions:
    #             disjunctions.append((class1, class2, room, teacher1, teacher2))

    #     return disjunctions

    # def _generate_room_disjunctions(self, max_periods):
    #     classes = self.df_asignacion["id"].to_list()
    #     periods = self.period_range
    #     rooms = self.df_salon["id"].to_list()
    #     disjunctions = []
    #     disjunctions2 = []
    #     for (class1, class2, period1, period2) in product(classes, classes, periods, periods):
    #         if (class1 != class2) and (abs(period1 - period2) < max_periods) and (class1, class2, period1, period2) not in disjunctions:
    #             for room in rooms:
    #                 print("help")
    #                 disjunctions2.append((class1, class2, period1, period2,room))
    #             disjunctions.append((class1, class2, period1, period2))
    #     return disjunctions2
    
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
            num_periods=(self.df_materias.loc[self.df_materias['id']==row['id_materia']])['no_periodos'].item()
            for i in range(1, num_periods):
                for (period, room) in product(periods, rooms):
                    id =row['id']
                    if (period+i<=mas_period) and (id,i, period, room) not in disjunctions:
                        disjunctions.append((id, i, period, room))
        return disjunctions
    
    def create_model(self):
        model = pe.ConcreteModel()
        # List of classes IDs
        model.CLASSES = pe.Set(initialize=self.df_asignacion["id"].tolist())
        # List of teachers IDs
        model.TEACHERS = pe.Set(initialize=self.df_profesores["id"].tolist())
        # List of rooms IDs
        model.ROOMS = pe.Set(initialize=self.df_salon["id"].tolist())

        num_periodos = self._get_number_of_periods()
        self.period_range=range(1,num_periodos)
        model.PERIODS = pe.Set(initialize=self.period_range)

        model.ASSIGNMENTS= pe.Set(initialize=model.CLASSES* model.PERIODS, dimen=2)
        # List of class with rooms - all possible combinations of classes and rooms (classID, roomID)
        #model.CLASSROOMS = pe.Set(initialize=model.CLASSES * model.ROOMS, dimen=2)
        # The capacity of each room
        model.ROOM_MAX_CAPACITY = pe.Param(model.ROOMS, initialize=self._generate_room_maximum())
        
        model.CLASS_STUDENTS = pe.Param(model.CLASSES, initialize=self._generate_class_students())

        model.CLASS_DURATION = pe.Set(initialize=self._generate_class_durations(), dimen=4)
        
        #model.TEACHER_SCHEDULE = pe.Param(model.TEACHERS, initialize=self._genereate_teacher_periods())
        
        model.DISJUNCTIONS_ROOM_CAPACITY = pe.Set(initialize=model.CLASSES*model.PERIODS*model.ROOMS, dimen=3)

        

        
        # List of class with rooms and teachers- all possible combinations of classes and rooms (classID, roomID, techerID)
        #model.ASSIGNMENTS= pe.Set(initialize=self._generate_class_room_assignment(model) * model.TEACHERS, dimen=3)

        #model.ASSIGNMENTS= pe.Set(initialize=model.CLASSES* model.ROOMS * model.TEACHERS, dimen=3)

        

        max_periods= self._get_max_period_num()

        model.M = pe.Param(initialize=1e3*1400)  # big M

        
        #Decision Variables
        model.PERIOD_ASSIGNED = pe.Var(model.ASSIGNMENTS, domain=pe.Binary)

        model.TEACHER_ASSIGNED = pe.Var(model.ASSIGNMENTS*model.TEACHERS, domain=pe.Binary)
        
        model.ROOM_ASSIGNED = pe.Var(model.ASSIGNMENTS*model.ROOMS, domain=pe.Binary)
        # model.ROOM_ASSIGNED = pe.Var(model.ASSIGNMENTS, domain=pe.IntegerSet(set(self.df_profesores["id"])))
        model.DISJUNCTIONS_ROOM = pe.Set(initialize=model.PERIODS*model.ROOMS, dimen=2)

       

        
        #Objective
        def objective_function(model):
            return sum([model.PERIOD_ASSIGNED[clasS, period] for clasS in model.CLASSES for period in model.PERIODS])
        model.OBJECTIVE = pe.Objective(rule=objective_function, sense=pe.maximize)

        #Constraints

        # Constraint 3: Cases can be assigned to a maximum of one session


        def period_assignment(model, clasS):
            return sum([model.PERIOD_ASSIGNED[(clasS, period)] for period in model.PERIODS]) <= 1
        model.PERIOD_ASSIGNMENT = pe.Constraint(model.CLASSES, rule=period_assignment)

        def room_per_class(model, clasS, period):
            return model.PERIOD_ASSIGNED[(clasS, period)] == sum([model.ROOM_ASSIGNED[(clasS, period, room)] for room in model.ROOMS])
        model.ROOM_PER_CLASS = pe.Constraint(model.ASSIGNMENTS, rule=room_per_class)

        def teacher_per_class(model, clasS, period):
            return model.PERIOD_ASSIGNED[(clasS, period)] == sum([model.TEACHER_ASSIGNED[(clasS, period, teachers)] for teachers in model.TEACHERS])
        model.TEACHER_PER_CLASS = pe.Constraint(model.ASSIGNMENTS, rule=teacher_per_class)


        def room_capacity(model, clasS, period, room):
            return model.CLASS_STUDENTS[clasS] <= model.ROOM_MAX_CAPACITY[room] + ((1 - model.ROOM_ASSIGNED[clasS, period,room])*model.M)

        model.ROOM_CAPACITY_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM_CAPACITY, rule=room_capacity)
        
        def no_room_overlap(model, period, room ):
            return sum([model.ROOM_ASSIGNED[( class1, period, room)] for class1 in model.CLASSES]) <=1

        # model.DISJUNCTIONS_ROOM_RULE = pyogdp.Disjunction(model.DISJUNCTIONS_ROOM, rule=no_room_overlap)        
        # def no_room_overlap(model, class1, class2, period1, period2, room):
        #     return [period1 +model.CLASS_DURATION[class1] <= period2 + \
        #             ((2 - model.ROOM_ASSIGNED[class1, period1,room] - model.ROOM_ASSIGNED[class2, period2,room])*model.M),
        #             period2 +model.CLASS_DURATION[class2] <= period1 + \
        #             ((2 - model.ROOM_ASSIGNED[class1, period1,room] - model.ROOM_ASSIGNED[class2, period2,room])*model.M)]

        model.DISJUNCTIONS_ROOM_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM, rule=no_room_overlap)


        def no_room_overlap_period(model, clasS, num_period, period, room ):
            return sum([model.ROOM_ASSIGNED[( class1, period+num_period, room)] for class1 in model.CLASSES]) <= 0 + ((1 - model.ROOM_ASSIGNED[clasS,period,room])*model.M)
        model.DISJUNCTIONS_PERIOD_ROOM_RULE = pe.Constraint(model.CLASS_DURATION, rule=no_room_overlap_period)



        # def no_teacher_overlap(model, class1, class2, period1, period2):
        #     return model.TEACHER_ASSIGNED[class1, period1] <= model.TEACHER_ASSIGNED[class2, period2] + \
        #             ((2 - model.PERIOD_ASSIGNED[class1, period1] - model.PERIOD_ASSIGNED[class2, period2])*model.M)

        # model.TEACHER_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM, rule=no_teacher_overlap)

        # def no_room_overlap(model, class1, class2, room, teacher1, teacher2):
        #     return [model.CLASS_START_TIME[class1, room, teacher1] + model.CLASS_DURATION[class1] <= model.CLASS_START_TIME[class2, room, teacher2] + \
        #             ((2 - model.CLASS_ASSIGNED[class1, room, teacher1] - model.CLASS_ASSIGNED[class2, room, teacher2])*model.M),
        #             model.CLASS_START_TIME[class2, room, teacher2] + model.CLASS_DURATION[class2] <= model.CLASS_START_TIME[class1, room, teacher1] + \
        #             ((2 - model.CLASS_ASSIGNED[class1, room, teacher1] - model.CLASS_ASSIGNED[class2, room, teacher2])*model.M)]

        # model.DISJUNCTIONS_RULE = pyogdp.Disjunction(model.DISJUNCTIONS, rule=no_room_overlap)

        pe.TransformationFactory("gdp.bigm").apply_to(model)

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
        self.draw_gantt()

    def draw_gantt(self):

        df = self.df_times
        classes = sorted(list(df['Class'].unique()))
        rooms = sorted(list(df['Room'].unique()))
        teacher = sorted(list(df['Teacher'].unique()))

        bar_style = {'alpha': 1.0, 'lw': 25, 'solid_capstyle': 'butt',}
        text_style = {'color': 'white', 'weight': 'bold', 'ha': 'center', 'va': 'center', 'size': '6'}
        colors = cm.Dark2.colors

        df.sort_values(by=['Class', 'Room','Teacher'])
        df.set_index(['Class', 'Room','Teacher'], inplace=True)
        fig, ax = plt.subplots(1,1)
        for c_ix, c in enumerate(classes, 1):
            for s_ix, s in enumerate(rooms, 1):
                for t_ix, t in enumerate(teacher, 1):
                    if (c, s,t) in df.index:
                        xs = df.loc[(c, s,t), 'Period']
                        idC=self._get_class_by_assignment(c)
                        sec=self._get_seccion_by_assignment(c)
                        xf = df.loc[(c, s,t), 'Period'] + \
                            self.df_materias[self.df_materias["id"] == idC]["no_periodos"]
                        ax.plot([s]* 2,[xs, xf] , c=colors[self._get_color(idC)], **bar_style)
                        ax.text(s,(xs + xf) / 2, str(idC) +"\n\'"+sec+"\'\n"+ str(t), **text_style)

        ax.set_title('Horario')
        ax.set_xlabel('Rooms')
        ax.set_ylabel('Periodo')
        ax.grid(True)

        fig.tight_layout()
        plt.show()
    def _get_class_by_assignment(self, id):
        return self.df_asignacion[self.df_asignacion["id"] == id]["id_materia"].item()
    def _get_seccion_by_assignment(self, id):
        return self.df_asignacion[self.df_asignacion["id"] == id]["sec"].item()

    def _get_color(self, id):
        career=(self.df_materias.loc[self.df_materias['id']==id])['carrera'].item()
        if(career=="Comun"):
            return 0
        if(career=="Sistemas"):
            return 1
        if(career=="Civil"):
            return 3

if __name__ == "__main__":
    cbc_path = "C:\\Users\\sergi\\Documents\\Coding\\Python\\solvers\\Cbc-2.7.5-win64-intel11.1\\bin\\cbc.exe"
    ipopt_path = "C:\\Users\\sergi\\Documents\\Coding\\Python\\solvers\\Ipopt-3.14.12-win64-msvs2019-md\\bin"
    cbc_name = "cbc"
    ipopt_name = "ipopt"

    options = {"seconds": 300}
    scheduler = Scheduler()
    scheduler.solve(solver_name=cbc_name, solver_path=cbc_path, options=options)
