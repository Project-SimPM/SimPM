import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

import pmpy.mcs as mcs
import pmpy.dist as dist

def f():
    dur=0
    x=dist.norm(3.4,0.307)
    for i in range(1000):
        dur+=x.sample()
    return dur

project_dur=mcs.monte_carlo(f,runs=100)
projec_dist=dist.emperical(project_dur)
project_dist2=dist.fit(project_dur,'norm')
project_dist2.plot_cdf()
project_dist2.plot_pdf()

result=projec_dist.percentile(.8)
