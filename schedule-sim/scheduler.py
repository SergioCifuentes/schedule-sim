
import pandas as pd
import pyomo.environ as pe
from pyomo.environ import value

from gantt_drawer import Drawer
from input_controller import InputController
from set_generator import SetGenerator
from json_builder import convert_to_Json
import pyutilib
class Scheduler:
    
    def __init__(self):
        self.input_controller =None
        self.is_solved = False
        
        #self.model = self.create_model()      
    def load_input_controller(self,input_controller):
        self.input_controller = input_controller
        self.df_asignacion = input_controller.df_asignacion
        self.df_disp_prof = input_controller.df_disp_prof
        self.df_disp_salon = input_controller.df_disp_salon
        self.df_materias = input_controller.df_materias
        self.df_profesores = input_controller.df_profesores
        self.df_prof_materia = input_controller.df_prof_materia
        self.df_salon = input_controller.df_salon
        self.set_generator= SetGenerator(self.df_salon,self.df_profesores,self.df_disp_salon,
                                         self.df_asignacion, self.df_disp_prof)
        self.model = self.create_model() 

    def get_input_controller(self):
        return self.input_controller

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

    def _generate_class_info(self):
        self.class_num_periods={}
        self.class_semester={}
        self.class_career={}
        self.class_mandatory=[]
        self.class_section={}
        self.class_materia={}
        for index, row in self.df_asignacion.iterrows():
            id= row['id']
            materia=self.df_materias.loc[self.df_materias['id']==row['id_materia']]
            self.class_materia[id]= row['id_materia']
            self.class_num_periods[id]=materia['no_periodos'].item()
            self.class_semester[id]=materia['semestre'].item()
            self.class_career[id]=materia['carrera'].item()
            if(materia['obli'].item()==True):
                self.class_mandatory.append(id)
            self.class_section[id]=row['sec']
    
    def _generate_teacher_info(self):
        self.teacher_mandatory={}
        self.teacher_capable={}
        for index, row in self.df_prof_materia.iterrows():
            id_teacher = row['id_profesor']
            id_curso = row['id_curso']
            mandatory = row['fijo']
            self.teacher_capable[(id_curso,id_teacher)]=1
            if mandatory==True:
                self.teacher_mandatory[(id_curso,id_teacher)]=1


    def create_model(self):
        model = pe.ConcreteModel()
        # List of classes IDs
        model.CLASSES = pe.Set(initialize=self.df_asignacion["id"].tolist())
        # List of teachers IDs
        model.TEACHERS = pe.Set(initialize=self.df_profesores["id"].tolist())
        # List of rooms IDs
        model.ROOMS = pe.Set(initialize=self.df_salon["id"].tolist())

        self._generate_class_info()
        self._generate_teacher_info()
        self.periods={}
        self.num_periodos = self.set_generator.get_number_of_periods(self.periods)
        self.rooms={}
        self.set_generator.get_rooms(self.rooms)
        self.period_range=range(1,self.num_periodos+1)
        self.max_periods= self._get_max_period_num()

        model.PERIODS = pe.Set(initialize=self.period_range)

        self.set_generator.set_class_num_periods(self.class_num_periods)
        self.set_generator.set_period_range(self.period_range)

        model.ASSIGNMENTS= pe.Set(initialize=model.CLASSES* model.PERIODS, dimen=2)

        model.ROOM_MAX_CAPACITY = pe.Param(model.ROOMS, initialize=self._generate_room_maximum())  
        model.CLASS_STUDENTS = pe.Param(model.CLASSES, initialize=self._generate_class_students())

        model.CLASS_DURATION = pe.Set(initialize=self.set_generator.generate_class_durations(), dimen=4)
        model.TEACHER_DURATION = pe.Set(initialize=self.set_generator.generate_teacher_durations(), dimen=4)
        model.CLASS_DURATION_TWO = pe.Set(initialize=self.set_generator.generate_classroom_periods(), dimen=4)
        model.TEACHER_DURATION_TWO = pe.Set(initialize=self.set_generator.generate_teacher_periods_two(), dimen=4)
        
        model.DISJUNCTIONS_ROOM_CAPACITY = pe.Set(initialize=model.CLASSES*model.PERIODS*model.ROOMS, dimen=3)
        model.ALL_PERIODS = pe.Set(initialize=range(1,self.num_periodos+self.max_periods))
        model.ROOM_PERIOD = pe.Set(initialize=model.ROOMS*model.ALL_PERIODS)
        model.TEACHER_PERIOD = pe.Set(initialize=model.TEACHERS*model.ALL_PERIODS)
        model.TEACHER_CLASS = pe.Set(initialize=model.CLASSES*model.TEACHERS, dimen=2)
        
        model.PARAM_ROOM_PERIOD = pe.Param(model.ROOM_PERIOD,initialize=self.set_generator.generate_room_periods( self.max_periods))
        model.PARAM_TEACHER_PERIOD = pe.Param(model.TEACHER_PERIOD,initialize=self.set_generator.generate_teacher_periods( self.max_periods))
        model.PARAM_TEACHER_CLASS = pe.Param(model.TEACHER_CLASS,initialize=self.set_generator.generate_teacher_class(self.class_materia, self.teacher_capable))
        
        model.DISJUNCTIONS_ROOM = pe.Set(initialize=model.PERIODS*model.ROOMS, dimen=2)

        model.DISJUNCTIONS_TEACHER = pe.Set(initialize=model.PERIODS*model.TEACHERS, dimen=2)
        self.same_semester_comun = []
        model.DISJUNCTIONS_SAME_SEMESTER = pe.Set(initialize=self.set_generator.generate_same_semester(self.same_semester_comun, self.class_semester, 
                                                                                                       self.class_career, self.class_section, self.class_num_periods), dimen=4)

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

        #Only one period assigned to each class
        def period_assignment(model, clasS):
            return sum([model.PERIOD_ASSIGNED[(clasS, period)] for period in model.PERIODS]) <= 1
        model.PERIOD_ASSIGNMENT = pe.Constraint(model.CLASSES, rule=period_assignment)

        #Classes from the same semester and career can't overlap
        def same_semester(model, class1, class2, num_period, period):
            return model.PERIOD_ASSIGNED[(class1, period)] + model.PERIOD_ASSIGNED[(class2, period+num_period)] <=1
        model.SAME_SEMESTER = pe.Constraint(model.DISJUNCTIONS_SAME_SEMESTER, rule=same_semester)

        #Mandatory classes MUST be assigned before non mandatory classes
        def mandatory_classes(model, clasS):
            return sum([model.PERIOD_ASSIGNED[(clasS, period)] for period in model.PERIODS]) >=1
        model.MANDATORY_CLASSES = pe.Constraint(model.DISJUNCTIONS_MANDATORY_CLASSES, rule=mandatory_classes)
        
        #Teachers assigned to classes with more than one period can't be assigned to a class within the periods
        def no_teacher_overlap_multiple_period(model, clasS, num_period, period, teacher ):
            return sum([model.TEACHER_ASSIGNED[( class1, period+num_period, teacher)] for class1 in model.CLASSES]) <= 0 + ((1 - model.TEACHER_ASSIGNED[clasS,period,teacher])*model.M)
        model.OVERLAP_PERIOD_TEACHER_RULE = pe.Constraint(model.TEACHER_DURATION, rule=no_teacher_overlap_multiple_period)

        #Teacher can only teach one class at a time
        def no_teacher_overlap(model, period, teacher):
            return sum([model.TEACHER_ASSIGNED[( class1, period, teacher)] for class1 in model.CLASSES]) <=1
        model.TEACHER_OVERLAP = pe.Constraint(model.DISJUNCTIONS_TEACHER, rule=no_teacher_overlap)
 
        #Teachers assigned to classes must be capable of teaching
        def teacher_capacity(model, clasS, teacher):
            return sum([model.TEACHER_ASSIGNED[( clasS, period, teacher)] for period in model.PERIODS]) <=model.PARAM_TEACHER_CLASS[clasS,teacher]
        model.TEACHER_CAPACITY = pe.Constraint(model.TEACHER_CLASS, rule=teacher_capacity)
 
        #Classes assigned to a teacher must be within the room schedule
        def teacher_schedule(model, clasS, num_period, period, teacher):
            return model.TEACHER_ASSIGNED[( clasS, period, teacher)]  <= model.PARAM_TEACHER_PERIOD[teacher,period+num_period]
        model.DISJUNCTIONS_PERIOD_TEACHER_RULE = pe.Constraint(model.TEACHER_DURATION_TWO, rule=teacher_schedule) 
       
       #Room can only be used by one clas at a time
        def no_room_overlap(model, period, room):
            return sum([model.ROOM_ASSIGNED[( class1, period, room)] for class1 in model.CLASSES]) <=1
        model.DISJUNCTIONS_ROOM_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM, rule=no_room_overlap)

        #Students assigned to a class must not surpass the room capacity
        def room_capacity(model, clasS, period, room):
            return model.CLASS_STUDENTS[clasS] <= model.ROOM_MAX_CAPACITY[room] + ((1 - model.ROOM_ASSIGNED[clasS, period,room])*model.M)
        model.ROOM_CAPACITY_RULE = pe.Constraint(model.DISJUNCTIONS_ROOM_CAPACITY, rule=room_capacity)

        #Room can be used by within all periods needed for one class
        def no_room_overlap_multiple_period(model, clasS, num_period, period, room ):
            return sum([model.ROOM_ASSIGNED[( class1, period+num_period, room)] for class1 in model.CLASSES]) <= 0 + ((1 - model.ROOM_ASSIGNED[clasS,period,room])*model.M)
        model.OVERLAP_PERIOD_ROOM_RULE = pe.Constraint(model.CLASS_DURATION, rule=no_room_overlap_multiple_period)

        #Classes assigned to a room must be within the room schedule
        def room_schedule(model, clasS, num_period, period, room ):
            return model.ROOM_ASSIGNED[( clasS, period, room)]  <= model.PARAM_ROOM_PERIOD[room,period+num_period]
        model.DISJUNCTIONS_PERIOD_ROOM_RULE = pe.Constraint(model.CLASS_DURATION_TWO, rule=room_schedule)

        #A class can only be assigned to one teacher
        def teacher_per_class(model, clasS, period):
            return model.PERIOD_ASSIGNED[(clasS, period)] == sum([model.TEACHER_ASSIGNED[(clasS, period, teachers)] for teachers in model.TEACHERS])
        model.TEACHER_PER_CLASS = pe.Constraint(model.ASSIGNMENTS, rule=teacher_per_class)

        #A class can only be assgned to one room
        def room_per_class(model, clasS, period):
            return model.PERIOD_ASSIGNED[(clasS, period)] == sum([model.ROOM_ASSIGNED[(clasS, period, room)] for room in model.ROOMS])
        model.ROOM_PER_CLASS = pe.Constraint(model.ASSIGNMENTS, rule=room_per_class)
        # pe.TransformationFactory("gdp.bigm").apply_to(model)

        return model

    def solve(self, solver_name, options=None, solver_path=None, local=True):
        print("Starting solver")
        pyutilib.subprocess.GlobalData.DEFINE_SIGNAL_HANDLERS_DEFAULT = False
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
        self.dict={}
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
        self.classes_assigned = []
        for (clasS, period) in self.model.PERIOD_ASSIGNED:

            if value(self.model.PERIOD_ASSIGNED[clasS, period]) == 1:
                self.classes_assigned.append(clasS)

        self.classes_missed = list(set(all_classes).difference(self.classes_assigned))
        self.is_solved=True
        print("Finish solver")
        # print("Number of classes assigned = {} out of {}:".format(len(self.classes_assigned), len(all_classes)))
        # print("Classes assigned: ", self.classes_assigned)
        # print("Number of Classes missed = {} out of {}:".format(len(self.classes_missed ), len(all_classes)))
        # print("Classes missed: ", self.classes_missed )
        # print("Number of constraints = {}".format(solver_results["Problem"].__getitem__(0)["Number of constraints"]))
        
    
    def draw(self, id):
        drawer = Drawer(self.df_times, self.df_asignacion, self.df_materias, self.periods,self.class_num_periods, self.rooms, self.df_profesores)
        drawer.draw(id)

    def get_results_json(self):
        return convert_to_Json(self.df_times, self.df_asignacion, self.df_materias, self.df_profesores,
                     self.df_salon, self.periods, len(self.classes_assigned), len(self.classes_missed ))


if __name__ == "__main__":
    cbc_path = "C:\\Users\\sergi\\Documents\\Coding\\Python\\solvers\\Cbc-2.7.5-win64-intel11.1\\bin\\cbc.exe"
    ipopt_path = "C:\\Users\\sergi\\Documents\\Coding\\Python\\solvers\\Ipopt-3.14.12-win64-msvs2019-md\\bin"
    cbc_name = "cbc"
    ipopt_name = "ipopt"
    input_controller = InputController()
    path="C:\\Users\\sergi\\Documents\\Coding\\Python\\schedule-sim\\schedule-sim\\resources\\scripts\\2\\"
    input_controller.load_data(path)
    
    options = {"seconds": 100}
    scheduler = Scheduler()
    scheduler.load_input_controller(input_controller)
    scheduler.solve(solver_name=cbc_name, solver_path=cbc_path, options=options)
    scheduler.draw(5)
