'''
Defining distributions and their stats most common for project management.
'''
import numpy as np
import scipy.stats as st
import matplotlib.pyplot as plt

def fit(data,dist_type):
    '''
    Fit a distribution on data using maximum likelihood method

    '''
    try:
        data=np.concatenate(data).ravel()
    except:
        pass
    a=None
    if dist_type=='triang':
        dist_type='triang'
        params=st.triang.fit(data)
        dist=st.triang(params[0],loc=params[1],scale=params[2])
        a=triang(0,1,2)
        a.dist=dist
        
    elif dist_type=='norm' :
        dist_type='norm'
        params=st.norm.fit(data)
        dist=st.norm(loc=params[0],scale=params[1])
        a=norm(0,1)
        a.dist=dist
       
    elif dist_type=='beta' :
            dist_type='beta'
            params=st.beta.fit(data)
            dist=st.beta(params[0],params[1],loc=params[2],scale=params[3])
            a=beta(1,1,0,1)
            a.dist=dist
            
    elif dist_type=='trapz' :
            dist_type='trapz'
            params=st.trapz.fit(data)
            
            dist=st.trapz(params[0],params[1],loc=params[2],scale=params[3])
            a=trapz(1,2,3,4)
            a.dist=dist
    else:
        raise("Distribution type is not recognized!")
        return
    a.ks=st.kstest(a.dist.rvs,data)[0]
    return a
    
class distribution():
    '''
    Defines a distirbution. All distributins inherit from this class.

    ...
    Attributes:
    params: list of int
        the list of paramters of the distribution
    dist_type: str
        The type of distribution
    dist: scipy distribution
    '''
    def __init__(self):
        self.params=None
        self.dist_type=None
        self.dist=None
        self.ks=None

    def sample(self):
        '''

        Returns
        -------
        float
            A random sample of the distribution
        '''
        return self.dist.rvs()

    def pdf_xy(self,size=100):
        '''
        return x,y numpy array of the pdf function for plotting
        '''
        low=0.00001
        high=.99999
        if self.dist_type=='uniform' or self.dist_type=='triang' or self.dist_type=='trapz':
            low=0
            high=1
        x=np.linspace(self.dist.ppf(low),self.dist.ppf(high),size+1)
        y=self.dist.pdf(x)
        return x,y


    def plot_pdf(self):
        '''

        Returns
        -------
        matplotlib.pylot.plt
            A plot for the probability density function
        '''
        x,y=self.pdf_xy()
        plt.plot(x,y,'r')
        plt.show(block=True)
        return plt

    def cdf_xy(self,size):
        low=0.00001
        high=.99999
        if self.dist_type=='uniform' or self.dist_type=='triang' or self.dist_type=='trapz':
            low=0
            high=1
        x=np.linspace(self.dist.ppf(low),self.dist.ppf(high),size+1)
        y=self.dist.cdf(x)
        return x,y

    def plot_cdf(self):
        '''

        Returns
        -------
        matplotlib.pylot.plt
            A plot for the cummulative distribution function
        '''
        x,y=self.cdf_xy(100)
        plt.plot(x,y,'b')
        plt.show(block=True)
        return plt

    def percentile(self,q):
        '''

        Parameters
        ----------
        q: float
            The value to find its percentile in the inverse of commulative distribution function
        Returns
        -------
        float
            The percentile value
        '''
        return self.dist.ppf(q)

    def pdf(self,x):
        return self.dist.pdf(x)

    def cdf(self,x):
        return self.dist.cdf(x)
        
class uniform(distribution):
    def __init__(self,a,b):
        self.dist_type='uniform'
        Loc=a
        Scale=b-a
        self.params=[Loc,Scale]
        self.dist=st.uniform(loc=Loc,scale=Scale)
    
class norm(distribution):
    def __init__(self,mean,std):
        self.dist_type='norm'
        self.params=[mean,std]
        self.dist=st.norm(loc=mean,scale=std)
class triang(distribution): 
    def __init__(self,a,b,c):
        self.dist_type='triang'
        Loc=a
        Scale=c-a
        c=(b-a)/Scale
        self.params=[c,Loc,Scale]
        self.dist=st.triang(c,loc=Loc,scale=Scale)
    
class trapz(distribution): 
    def __init__(self,a,b,c,d):

        self.dist_type='trapz'
        Loc=a
        Scale=d-a
        C=(b-a)/(d-a)
        D=(c-a)/(d-a)
       
        self.params=[C,D,Loc,Scale]
        self.dist=st.trapz(C,D,loc=Loc,scale=Scale)   
class beta(distribution): 
    def __init__(self,a,b,minp,maxp):
        self.dist_type='beta'
        Loc=minp
        Scale=maxp-minp
        self.params=[a,b,Loc,Scale]
        self.dist=st.beta(a,b,loc=Loc,scale=Scale)  
class expon(distribution): 
    def __init__(self,mean):
        self.dist_type='expon'
        Scale=mean
        self.params=[Scale]
        self.dist=st.expon(scale=Scale)

class emperical(distribution):
    def __init__(self,data):
        try:
            data=np.concatenate(data).ravel()
        except:
            pass
        self.dist_type='emperical'
        self.params=None
        self.dist=None
        self.data=np.sort(data)
    def cdf_xy(self):
        '''
        returns x,y numpy array for plotting the cdf function
        '''

        unique, counts = np.unique(self.data, return_counts=True)
        c=np.cumsum(counts)
        
        c=c/c[-1]
        return unique,c

    def plot_cdf(self):
        x,y=self.cdf_xy()
        plt.step(x,y)
        plt.show()
    def pdf_xy(self):
        bins=int(2*len(self.data)**(1/3))
        value,BinList=np.histogram(self.data,bins)
        value=value/len(self.data)
        l=BinList[-1]-BinList[0]
        n=len(BinList)
        width=l/(n)
        value=value/width
        BinList=BinList[:-1]+np.diff(BinList)[1]/2
        return BinList,value

    def plot_pdf(self):
        bins=int(2*len(self.data)**(1/3))
        value,BinList=np.histogram(self.data,bins)
        value=value/len(self.data)
        l=BinList[-1]-BinList[0]
        n=len(BinList)
        width=l/(n)
        value=value/width
        BinList=BinList[:-1]+np.diff(BinList)[1]/2
        plt.bar(BinList,value,width)
        plt.show()

    def pdf(self,x):
        bins=int(2*len(self.data)**(1/3))
        value,BinList=np.histogram(self.data,bins)
        if x<BinList[0] or x>BinList[-1]:
            return 0
        i=0
        bl=len(BinList)
        while x>=BinList[i] and i<bl:
            i+=1
        r=value[i-1]/len(self.data)
        l=BinList[-1]-BinList[0]
        n=len(BinList)
        width=l/(n)
        r=r/width
        return r
       
    def cdf(self,x):
        if x>self.data[-1]:
            return 1
        i=0
        while x>=self.data[i]:
            i+=1
        return i/len(self.data)
 
    def percentile(self,q):
        return np.quantile(self.data,q)

    def sample(self):
        return np.quantile(self.data,np.random.random())
        
    def discrete_sample(self):
        return np.random.choice(self.data)
        
