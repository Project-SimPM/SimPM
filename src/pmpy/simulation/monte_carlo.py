import numpy as np
'''
***************************************
******Monte Carlo**********************
***************************************
'''

def monte_carlo(function,runs=1000):
    results=None
    results=np.array([function()])
    for i in range(runs-1):
        results=np.append(results,[function()],axis=0)
    return results
        
