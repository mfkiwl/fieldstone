import numpy as np
import FEbasis2D as FE
import matplotlib.pyplot as plt

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def quadrature(space,nqperdim):

    if space=='Q1' or space=='Q2' or space=='Q3' or space=='Q4' or space=='Q1+':
       coords=qcoords_1D(nqperdim)
       weights=qweights_1D(nqperdim)
       nq=nqperdim**2 
       val_r = np.zeros(nq,dtype=np.float64) 
       val_s = np.zeros(nq,dtype=np.float64) 
       val_w = np.zeros(nq,dtype=np.float64) 
       counter=0
       for iq in range(0,nqperdim):
           for jq in range(0,nqperdim):
               val_r[counter]=coords[iq]
               val_s[counter]=coords[jq]
               val_w[counter]=weights[iq]*weights[jq]
               counter+=1

    elif space=='P1' or space=='P2' or space=='P1+' or space=='P2+' or space=='P3':

       nq=nqperdim
       val_r = np.zeros(nq,dtype=np.float64) 
       val_s = np.zeros(nq,dtype=np.float64) 
       val_w = np.zeros(nq,dtype=np.float64) 

       if nq==1:
          val_r[0]=1/3 ; val_s[0]=1/3 ; val_w[0]=1

       if nq==2:
          val_r[:]=0
          val_s[:]=0
          val_w[:]=0

       if nq==3:
          val_r[0]=1/6 ; val_s[0]=1/6 ; val_w[0]=1/3
          val_r[1]=2/3 ; val_s[1]=1/6 ; val_w[1]=1/3
          val_r[2]=1/6 ; val_s[2]=2/3 ; val_w[2]=1/3

       if nq==4:
          val_r[0]=1/3 ; val_r[0]=1/3 ; val_w[0]=-27/78
          val_r[1]=1/5 ; val_r[1]=3/5 ; val_w[1]= 25/48
          val_r[2]=1/5 ; val_r[2]=1/5 ; val_w[2]= 25/48
          val_r[3]=3/5 ; val_r[3]=1/5 ; val_w[3]= 25/48

       if nq==5:
          val_r[:]=0
          val_s[:]=0
          val_w[:]=0

       if nq==6:
          val_r[0]=0.091576213509771 ; val_s[0]=0.091576213509771 ; val_w[0]=0.109951743655322/2.0 
          val_r[1]=0.816847572980459 ; val_s[1]=0.091576213509771 ; val_w[1]=0.109951743655322/2.0 
          val_r[2]=0.091576213509771 ; val_s[2]=0.816847572980459 ; val_w[2]=0.109951743655322/2.0 
          val_r[3]=0.445948490915965 ; val_s[3]=0.445948490915965 ; val_w[3]=0.223381589678011/2.0 
          val_r[4]=0.108103018168070 ; val_s[4]=0.445948490915965 ; val_w[4]=0.223381589678011/2.0 
          val_r[5]=0.445948490915965 ; val_s[5]=0.108103018168070 ; val_w[5]=0.223381589678011/2.0 

       if nq==7:
          val_r[0]=0.1012865073235 ; val_s[0]=0.1012865073235 ; val_w[0]=0.0629695902724 
          val_r[1]=0.7974269853531 ; val_s[1]=0.1012865073235 ; val_w[1]=0.0629695902724 
          val_r[2]=0.1012865073235 ; val_s[2]=0.7974269853531 ; val_w[2]=0.0629695902724 
          val_r[3]=0.4701420641051 ; val_s[3]=0.0597158717898 ; val_w[3]=0.0661970763942 
          val_r[4]=0.4701420641051 ; val_s[4]=0.4701420641051 ; val_w[4]=0.0661970763942 
          val_r[5]=0.0597158717898 ; val_s[5]=0.4701420641051 ; val_w[5]=0.0661970763942 
          val_r[6]=0.3333333333333 ; val_s[6]=0.3333333333333 ; val_w[6]=0.1125000000000 

       if nq==8:
          val_r[:]=0
          val_s[:]=0
          val_w[:]=0

       if nq==9:
          val_r[:]=0
          val_s[:]=0
          val_w[:]=0

    else:
       exit('quadrature: unknown space')

    return nq,val_r,val_s,val_w

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def qcoords_1D(nqperdim):

    val = np.zeros(nqperdim,dtype=np.float64) 

    if nqperdim==1: 
       val[0]=0

    if nqperdim==2: 
       val=[-1./np.sqrt(3.),1./np.sqrt(3.)]

    if nqperdim==3: 
       val=[-np.sqrt(3/5),0.,np.sqrt(3/5)]

    if nqperdim==4: 
       qc4a=np.sqrt(3./7.+2./7.*np.sqrt(6./5.))
       qc4b=np.sqrt(3./7.-2./7.*np.sqrt(6./5.))
       val=[-qc4a,-qc4b,qc4b,qc4a]

    if nqperdim==5: 
       qc5a=np.sqrt(5.+2.*np.sqrt(10./7.))/3.
       qc5b=np.sqrt(5.-2.*np.sqrt(10./7.))/3.
       qc5c=0.
       val=[-qc5a,-qc5b,qc5c,qc5b,qc5a]

    if nqperdim==6:
       val=[-0.932469514203152,\
            -0.661209386466265,\
            -0.238619186083197,\
            +0.238619186083197,\
            +0.661209386466265,\
            +0.932469514203152]

    if nqperdim==7:
       val=[-0.9491079123427585,\
            -0.7415311855993945,\
            -0.4058451513773972,\
             0.0000000000000000,\
             0.4058451513773972,\
             0.7415311855993945,\
             0.9491079123427585]

    if nqperdim==8:
       val=[-0.9602898564975363,\
            -0.7966664774136267,\
            -0.5255324099163290,\
            -0.1834346424956498,\
             0.1834346424956498,\
             0.5255324099163290,\
             0.7966664774136267,\
             0.9602898564975363]

    if nqperdim==9:
       val=[-0.9681602395076261,\
            -0.8360311073266358,\
            -0.6133714327005904,\
            -0.3242534234038089,\
             0.0000000000000000,\
             0.3242534234038089,\
             0.6133714327005904,\
             0.8360311073266358,\
             0.9681602395076261]

    if nqperdim==10:
       val=[-0.973906528517172,\
            -0.865063366688985,\
            -0.679409568299024,\
            -0.433395394129247,\
            -0.148874338981631,\
             0.148874338981631,\
             0.433395394129247,\
             0.679409568299024,\
             0.865063366688985,\
             0.973906528517172]

    return val

#------------------------------------------------------------------------------

def qweights_1D(nqperdim):

    val = np.zeros(nqperdim,dtype=np.float64) 

    if nqperdim==1:
       val[0]=2

    if nqperdim==2:
       val=[1.,1.]

    if nqperdim==3:
       val=[5/9,8/9,5/9]

    if nqperdim==4:
       qw4a=(18-np.sqrt(30.))/36.
       qw4b=(18+np.sqrt(30.))/36
       val=[qw4a,qw4b,qw4b,qw4a]

    if nqperdim==5: 
       qw5a=(322.-13.*np.sqrt(70.))/900.
       qw5b=(322.+13.*np.sqrt(70.))/900.
       qw5c=128./225.
       val=[qw5a,qw5b,qw5c,qw5b,qw5a]

    if nqperdim==6:
       val=[0.171324492379170,\
            0.360761573048139,\
            0.467913934572691,\
            0.467913934572691,\
            0.360761573048139,\
            0.171324492379170]

    if nqperdim==7:
       val=[0.1294849661688697,\
            0.2797053914892766,\
            0.3818300505051189,\
            0.4179591836734694,\
            0.3818300505051189,\
            0.2797053914892766,\
            0.1294849661688697]

    if nqperdim==8:
       val=[0.1012285362903763,\
            0.2223810344533745,\
            0.3137066458778873,\
            0.3626837833783620,\
            0.3626837833783620,\
            0.3137066458778873,\
            0.2223810344533745,\
            0.1012285362903763]

    if nqperdim==9:
       val=[0.0812743883615744,\
            0.1806481606948574,\
            0.2606106964029354,\
            0.3123470770400029,\
            0.3302393550012598,\
            0.3123470770400029,\
            0.2606106964029354,\
            0.1806481606948574,\
            0.0812743883615744]

    if nqperdim==10:
       val=[0.066671344308688,\
            0.149451349150581,\
            0.219086362515982,\
            0.269266719309996,\
            0.295524224714753,\
            0.295524224714753,\
            0.269266719309996,\
            0.219086362515982,\
            0.149451349150581,\
            0.066671344308688]

    return val

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def visualise_quadrature_points(space,nqpts):
    r=FE.NNN_r(space)
    s=FE.NNN_s(space)

    nq,rq,sq,wq=quadrature(space,nqpts)
    plt.figure()
    plt.scatter(rq,sq,s=50,color='orange',marker='+')
    plt.scatter(r,s,color='teal',s=10)
    plt.grid(color = 'gray', linestyle = '--', linewidth = 0.25)
    plt.xlabel('r')
    plt.xlabel('s')
    plt.title(space)

    if space=='Q1' or space=='Q2' or space=='Q3' or space=='Q4' or space=='Q1+':
       plt.xlim([-1.1,+1.1])
       plt.ylim([-1.1,+1.1])
       plt.plot([-1,1,1,-1,-1],[-1,-1,1,1,-1],color='teal',linewidth=2)
    elif space=='P1' or space=='P2' or space=='P1+' or space=='P2+' or space=='P3':
       plt.xlim([-0.1,+1.1])
       plt.ylim([-0.1,+1.1])
       plt.plot([0,0,1,0],[0,1,0,0],color='teal',linewidth=2)
    else:
       exit('visualise_quadrature_points: unknown space')
    plt.savefig(space+'_quadrature_points'+str(nqpts)+'.pdf',bbox_inches='tight')
    print('     -> generated '+space+'_quadrature_points'+str(nqpts)+'.pdf')
    plt.close()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
