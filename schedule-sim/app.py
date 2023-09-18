from flask import Flask, render_template, request, jsonify, Response, send_file
app = Flask(__name__)
from input_controller import InputController
from scheduler import Scheduler
from db import DB
import threading
import constant
from flask_cors import CORS
import json

input_controller = InputController()
scheduler = Scheduler()
solve_thread=threading.Thread()
db=DB()

CORS(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    app.run()

@app.route("/load_data", methods=['POST'])
def load_data():
    req_data = request.get_json()
    folder_path = req_data['folder_path'] 
    
    if(input_controller.load_data(folder_path)):
        input_controller.save_all()
        def long_running_task(**kwargs):
            scheduler.load_input_controller(input_controller)
        thread = threading.Thread(target=long_running_task, kwargs={
                        'post_data': req_data})
        thread.start()
        response = jsonify({
            'status': '202',
            'message': 'Accepted'
        })

        return response
    else:
        response = jsonify({
            'status': '404',
            'res': 'failure',
            'error': 'Invalid folder path'
        })
        return response
    
@app.route("/solve_model", methods=['POST'])
def solve_model():
    req_data = request.get_json()
    if(scheduler.get_input_controller()==None):
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'data not loaded'
        })
    else:
        def long_solve_task(**kwargs):
            seconds=kwargs.get('post_data',{})
            options = {"seconds": seconds}
            scheduler.solve(solver_name=constant.CBC, solver_path=constant.CBC_PATH, options=options)
        solve_thread = threading.Thread(target=long_solve_task,kwargs={
                        'post_data': req_data['seconds']})
        solve_thread.start()
        return {"message": "Accepted"}, 202
    
@app.route("/get_results", methods=['GET'])
def get_results():
    if (not scheduler.is_solved):
        return jsonify({
            'status': '503',
            'res': 'Server Error',
            'error': 'Not Ready Yet'
        })    
    else:
        json1=scheduler.get_results_json()
        id = db.insertResults(json1)
        scheduler.draw(id)
        return jsonify({
            'status': '200',
            'id': id
        })
    
@app.route("/get_results/<id>", methods=['GET'])
def get_result(id):
    result = db.getResult(id)
    if(result!=False):
        return result
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'result not found'
            })
    
@app.route("/reset_model", methods=['POST'])
def reset_model():

    scheduler=Scheduler()
    return jsonify({
            'res':'success',
            'status': '200',
            'msg': 'Model reset'
        })

@app.route("/teachers", methods=['POST'])
def post_teachers():
    req_data = request.get_json()
    if 'name' in req_data\
    and 'career' in req_data:
        id = db.insertTeacher(req_data)
        if hasattr(input_controller, "df_profesores"):
            input_controller.insert_teacher(id,req_data)
        return jsonify({
            'status': '200',
            'id': id
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers data not loaded'
        })
@app.route("/teachers/schedule", methods=['POST'])
def post_teachers_schedule():
    req_data = request.get_json()
    print(req_data)
    if 'start' in req_data and 'id' in req_data\
    and 'end' in req_data:
        id = db.insertTeacherSchedule(req_data)
        if hasattr(input_controller, "df_disp_prof"):
            input_controller.insert_teacher_schedule(req_data)
        return jsonify({
            'status': '200',
            'id': req_data['id']
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers schedule data not loaded'
        })
    
@app.route("/teachers/class", methods=['POST'])
def post_teachers_class():
    req_data = request.get_json()
    print(req_data)
    if 'class_id' in req_data and 'id' in req_data\
    and 'mandatory' in req_data:
        id = db.insertTeacherClass(req_data)
        if hasattr(input_controller, "df_prof_materia"):
            input_controller.insert_teacher_class(req_data)
        return jsonify({
            'status': '200',
            'id': req_data['id']
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers class data not loaded'
        })

@app.route("/teachers", methods=['GET'])
def get_teachers():
    if hasattr(input_controller, "df_profesores"):
        return Response(input_controller.df_profesores.to_json(orient="records"), mimetype='application/json')
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers data not loaded'
        })


@app.route("/teachers/<id>", methods=['DELETE'])
def delete_teachers(id):
    if hasattr(input_controller, "df_profesores") and input_controller.teacher_exists(id):
        input_controller.delete_teacher(id)
        db.deleteTeacher(id)
        return jsonify({
            'res':'success',
            'status': '200',
            'msg': 'Teacher deleted'
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers data not loaded'
        })

@app.route("/teachers/<id>", methods=['GET'])
def get_teacher(id):
    if hasattr(input_controller, "df_profesores") and input_controller.teacher_exists(id):
        result= input_controller.get_teacher(int(id))
        return result
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers data not loaded'
        })

    
@app.route("/classes", methods=['GET'])
def get_classes():
    if hasattr(input_controller, "df_materias"):
        return Response(input_controller.df_materias.to_json(orient="records"), mimetype='application/json')
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'class data not loaded'
        })
    
@app.route("/classes/<id>", methods=['GET'])
def get_class(id):
    if hasattr(input_controller, "df_materias") and input_controller.class_exists(id):
        result= input_controller.get_class(int(id))
        return result
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'class data not loaded'
        })
    
@app.route("/classes", methods=['POST'])
def post_class():
    req_data = request.get_json()
    if 'name' in req_data and 'periods' in req_data and 'id' in req_data\
    and 'semester' in req_data and 'mandatory' in req_data and 'career' in req_data:
        id = db.insertClass(req_data)
        if hasattr(input_controller, "df_materias"):
            input_controller.insert_class(id,req_data)
        return jsonify({
            'status': '200',
            'id': id
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'classroom data not loaded'
        })
    
@app.route("/classes/assignment", methods=['POST'])
def post_class_assignment():
    req_data = request.get_json()
    if 'id' in req_data and 'section' in req_data and 'students' in req_data:
        id=db.insertClassAsignment(req_data)
        if hasattr(input_controller, "df_asignacion"):
            input_controller.insert_class_asignment(id, req_data)
        return jsonify({
            'status': '200',
            'id': id
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'classroom data not loaded'
        })
    
@app.route("/classes/<id>", methods=['DELETE'])
def delete_classes(id):
    if hasattr(input_controller, "df_materias") and input_controller.class_exists(id):
        input_controller.delete_class(id)
        db.deleteClass(id)
        return jsonify({
            'res':'success',
            'status': '200',
            'msg': 'Class deleted'
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'Class data not loaded'
        })
    
@app.route("/classrooms", methods=['GET'])
def get_classrooms():
    if hasattr(input_controller, "df_materias"):
        return Response(input_controller.df_salon.to_json(orient="records"), mimetype='application/json')
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'classroom data not loaded'
        })
    
@app.route("/classrooms/<id>", methods=['DELETE'])
def delete_classrooms(id):
    if hasattr(input_controller, "df_salon") and input_controller.classroom_exists(id):
        input_controller.delete_classroom(id)
        db.deleteClassroom(id)
        return jsonify({
            'res':'success',
            'status': '200',
            'msg': 'Classroom deleted'
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'Classroom data not loaded'
        })

@app.route("/classrooms/<id>", methods=['GET'])
def get_classroom(id):
    if hasattr(input_controller, "df_salon") and input_controller.classroom_exists(id):
        result= input_controller.get_classroom(int(id))
        return result
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'classroom data not loaded'
        })
    
@app.route("/classrooms", methods=['POST'])
def post_classrooms():
    req_data = request.get_json()
    if 'name' in req_data\
    and 'capacity' in req_data and 'max_capacity' in req_data:
        id = db.insertRoom(req_data)
        if hasattr(input_controller, "df_salon"):
            input_controller.insert_classroom(id,req_data)
        return jsonify({
            'status': '200',
            'id': id
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'classroom data not loaded'
        })
    
@app.route("/classrooms/schedule", methods=['POST'])
def post_classrooms_schedule():
    req_data = request.get_json()
    if 'start' in req_data and 'id' in req_data\
    and 'end' in req_data:
        db.insertClassroomSchedule(req_data)
        if hasattr(input_controller, "df_disp_salon"):
            input_controller.insert_class_schedule(req_data)
        return jsonify({
            'status': '200',
            'id': req_data['id']
        })
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers schedule data not loaded'
        })
    
@app.route("/load_info", methods=['GET'])
def get_load_info():
    if hasattr(input_controller, "df_profesores"):
        if(input_controller.changed):
            def long_running_task(**kwargs):
                print("loading")
                scheduler.load_input_controller(input_controller)
                input_controller.changed=False
            thread = threading.Thread(target=long_running_task)
            thread.start()
        return json.dumps( input_controller.get_load_info())
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'teachers data not loaded'
        })
    
@app.route('/get_image/<id>', methods=['GET'])
def get_image(id):
    filename='../docs/results/Schedule'+id+'.png'

    return send_file(filename, mimetype='image/gif')

@app.route('/get_sim_history', methods=['GET'])
def get_history():
    
    return json.dumps(db.getSimHistory())

@app.route('/load_by_db', methods=['GET'])
def get_load_db():
    if(input_controller.load_data_db()):
        def long_running_task(**kwargs):
            scheduler.load_input_controller(input_controller)
        thread = threading.Thread(target=long_running_task)
        thread.start()
        return jsonify({
            'status': '202',
            'message': 'Accepted'
        })
        
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'Could not load data from database'
        })
    


        
