import  matplotlib.pyplot as plt
import matplotlib.cm as cm
import constant
from dateutil.relativedelta import relativedelta

class Drawer:

    def __init__(self, results , asignacion, materias, periods, numperiods):
        self.results = results
        self.df_asignacion = asignacion
        self.df_materias = materias
        self.periods = periods
        self.numperiods = numperiods

    def draw(self):
        num=[]
        time=[]
        for key,value in self.periods.items():
            num.append(key)
            time.append(value.strftime('%H:%M'))
        df = self.results
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
                        #xs = self.periods[df.loc[(c, s,t), 'Period']]
                        xs=df.loc[(c, s,t), 'Period']
                        idC=self._get_class_by_assignment(c)
                        sec=self._get_seccion_by_assignment(c)
                        # xf = (xs + relativedelta(minutes=(self.numperiods[c]*constant.TIEMPO_PERIODO))).time()
                        # xs=xs.time()
                        xf = xs +self.numperiods[c]
                        ax.plot([s]* 2,[xs, xf] , c=colors[self._get_color(idC)], **bar_style)
                        ax.text(s,(xs + xf) / 2, str(idC) +"\n\'"+sec+"\'\n"+ str(int(t)), **text_style)

        ax.set_title('Horario')
        ax.set_xlabel('Rooms')
        ax.set_ylabel('Periodo')
        
        #ax.invert_xaxis()
        
        ax.grid(True)
        plt.yticks(num,time)
        ax.invert_yaxis()
        
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