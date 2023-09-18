
import json
def convert_to_Json(df_results, df_asignacion, df_materia, df_profesor,
                     df_room, periods, assigned, notAssigned):
    dict={}
    classes=[]
    dict['assigned']=assigned
    dict['notAssigned']=notAssigned
    maxmin=_get_max(df_results)
    dict['maxPeriodsForTeacher']=maxmin[0]
    dict['difference']=maxmin[0]-maxmin[1]
    
    for index, row in df_results.iterrows():
        new_class={}
        id=row['Class']
        assignment=  _get_asignment(df_asignacion, id)
        class_code=_get_class_by_assignment(df_asignacion, id)
        new_class['classId']=class_code
        materia=_get_class(df_materia, class_code)
        new_class['name']=materia['nombre'].item()
        new_class['section']=assignment['sec'].item()
        new_class['semester']=materia['semestre'].item()
        new_class['profesor']=_get_profesor_name(df_profesor,row['Teacher'])
        new_class['roomNumber']=int(row['Room'].item())
        new_class['room']=_get_room_name(df_room,row['Room'].item())
        new_class['time']=periods.get(row['Period']).strftime('%H:%M')
        new_class['career']=materia['carrera'].item()
        classes.append(new_class)
    dict['classes'] = classes
    return dict

def _get_class_by_assignment(df_asignacion, id):
    return df_asignacion[df_asignacion["id"] == id]["id_materia"].item()

def _get_room_name(df_room, id):
    return df_room[df_room["id"] == id]["nombre"].item()

def _get_profesor_name(df_profesor, id):
    return df_profesor[df_profesor["id"] == id]["nombre"].item()

def _get_class(df_materia, code):
    return df_materia[df_materia["id"] == code]

def _get_asignment(df_asignacion, id):
    return df_asignacion[df_asignacion["id"] == id]

def _get_max(df_results):
    dict={}
    for index, row in df_results.iterrows():
        if('Teacher'in row):
            id=row['Teacher']
            if(id in dict):
                dict[id]=dict[id]+1
            else:
                dict[id]=1
    maxNum=max(dict.values())
    minNum=min(dict.values())
    return[maxNum,minNum]
    


