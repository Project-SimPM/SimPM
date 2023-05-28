import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import simpm.mcs as mcs
import simpm.dist as dist
import matplotlib.pyplot as plt
def f():
    dur=0
    x=dist.norm(3.4,0.307)
    for i in range(10):
        dur+=x.sample()
    return dur,dur+1

project_dur=mcs.monte_carlo(f,runs=1000)
print(project_dur[:,1].shape)
project_dur[:,1]=project_dur[:,1]
project_dist=dist.emperical(project_dur)
project_dist2=dist.fit(project_dur,'norm')
project_dist.plot_cdf()
project_dist.plot_pdf()

d1=project_dur[:,1]
d2=project_dur[:,0]
x1,y1=dist.emperical(d1).cdf_xy()
x2,y2=dist.emperical(d2).cdf_xy()
plt.plot(x1,y1,label='1')
plt.plot(x2,y2,label='2')
plt.legend()
plt.show()
result=project_dist.percentile(.8)
