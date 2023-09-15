from flask import Flask, render_template, request, jsonify, Response
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
    print(req_data)
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
    
@app.route("/load_info", methods=['GET'])
def get_load_info():
    if hasattr(input_controller, "df_profesores"):
        return json.dumps( input_controller.get_load_info())
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
    
@app.route("/classrooms", methods=['GET'])
def get_classrooms():
    if hasattr(input_controller, "df_salon"):
        return Response(input_controller.df_salon.to_json(orient="records"), mimetype='application/json')
    else:
        return jsonify({
            'status': '400',
            'res': 'failure',
            'error': 'classroom data not loaded'
        })


        
