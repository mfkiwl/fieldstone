import numpy as np
import time as timing
from scipy.sparse import lil_matrix
import random
import scipy.sparse as sps
from scipy.sparse.linalg.dsolve import linsolve

###############################################################################

def NNV(rq,sq):
    NV_0= 0.5*rq*(rq-1.) * 0.5*sq*(sq-1.)
    NV_1= 0.5*rq*(rq+1.) * 0.5*sq*(sq-1.)
    NV_2= 0.5*rq*(rq+1.) * 0.5*sq*(sq+1.)
    NV_3= 0.5*rq*(rq-1.) * 0.5*sq*(sq+1.)
    NV_4=     (1.-rq**2) * 0.5*sq*(sq-1.)
    NV_5= 0.5*rq*(rq+1.) *     (1.-sq**2)
    NV_6=     (1.-rq**2) * 0.5*sq*(sq+1.)
    NV_7= 0.5*rq*(rq-1.) *     (1.-sq**2)
    NV_8=     (1.-rq**2) *     (1.-sq**2)
    return NV_0,NV_1,NV_2,NV_3,NV_4,NV_5,NV_6,NV_7,NV_8

def dNNVdr(rq,sq):
    dNVdr_0= 0.5*(2.*rq-1.) * 0.5*sq*(sq-1)
    dNVdr_1= 0.5*(2.*rq+1.) * 0.5*sq*(sq-1)
    dNVdr_2= 0.5*(2.*rq+1.) * 0.5*sq*(sq+1)
    dNVdr_3= 0.5*(2.*rq-1.) * 0.5*sq*(sq+1)
    dNVdr_4=       (-2.*rq) * 0.5*sq*(sq-1)
    dNVdr_5= 0.5*(2.*rq+1.) *    (1.-sq**2)
    dNVdr_6=       (-2.*rq) * 0.5*sq*(sq+1)
    dNVdr_7= 0.5*(2.*rq-1.) *    (1.-sq**2)
    dNVdr_8=       (-2.*rq) *    (1.-sq**2)
    return dNVdr_0,dNVdr_1,dNVdr_2,dNVdr_3,dNVdr_4,dNVdr_5,dNVdr_6,dNVdr_7,dNVdr_8

def dNNVds(rq,sq):
    dNVds_0= 0.5*rq*(rq-1.) * 0.5*(2.*sq-1.)
    dNVds_1= 0.5*rq*(rq+1.) * 0.5*(2.*sq-1.)
    dNVds_2= 0.5*rq*(rq+1.) * 0.5*(2.*sq+1.)
    dNVds_3= 0.5*rq*(rq-1.) * 0.5*(2.*sq+1.)
    dNVds_4=     (1.-rq**2) * 0.5*(2.*sq-1.)
    dNVds_5= 0.5*rq*(rq+1.) *       (-2.*sq)
    dNVds_6=     (1.-rq**2) * 0.5*(2.*sq+1.)
    dNVds_7= 0.5*rq*(rq-1.) *       (-2.*sq)
    dNVds_8=     (1.-rq**2) *       (-2.*sq)
    return dNVds_0,dNVds_1,dNVds_2,dNVds_3,dNVds_4,dNVds_5,dNVds_6,dNVds_7,dNVds_8

###############################################################################

sqrt3=np.sqrt(3.)
sqrt2=np.sqrt(2.)
eps=1.e-10 
cm=0.01
year=365.25*24.*3600.

print("-----------------------------")
print("---------- stone 129 --------")
print("-----------------------------")

mV=9
ndof=2
ndim=2

experiment=1

if experiment==1:
   Lx=4
   Ly=1
   nelx=40
   nely=40
   #phase1: top layer
   #phase2: bottom layer
   #phase3: thin middle layer
   viscosity = np.array([1e18,1e18,1e20],dtype=np.float64)
   #viscosity = np.array([1e20,1e20,1e22],dtype=np.float64)
   nu=0.3 # Poisson ratio
   E=1e11 # Young's modulus
   mu= E/(2*(1+nu)) #shear modulus
   K= E/(3*(1-2*nu))  #bulk modulus
   gx=0
   gy=9.8
   rho=2700
   nstep=400
   dt=0.8*year

if experiment==2:
   Lx=50e3
   Ly=50e3
   nelx=40
   nely=40
   viscosity = np.array([1e21],dtype=np.float64)
   nu=0.3 
   mu=1e10
   E=2*mu*(1+nu)
   K= E/(3*(1-2*nu)) 
   nstep=200
   dt=100*year
   rho=0
   gx=0
   gy=0
    
every=1

nnx=2*nelx+1  # number of elements, x direction
nny=2*nely+1  # number of elements, y direction
NV=nnx*nny    # number of nodes
nel=nelx*nely # number of elements, total
Nfem=NV*ndof  # Total number of velocity dofs

stats_vel_file=open('stats_vel.ascii',"w")
stats_exx_file=open('stats_exx.ascii',"w")
stats_eyy_file=open('stats_eyy.ascii',"w")
stats_exy_file=open('stats_exy.ascii',"w")
stats_sxx_file=open('stats_sxx.ascii',"w")
stats_syy_file=open('stats_syy.ascii',"w")
stats_sxy_file=open('stats_sxy.ascii',"w")

#####################################################################

nqperdim=3
qcoords=[-np.sqrt(3./5.),0.,np.sqrt(3./5.)]
qweights=[5./9.,8./9.,5./9.]

nq=nel*nqperdim**ndim # total number of quadrature points

#####################################################################

print('nnx           =',nnx)
print('nny           =',nny)
print('NV            =',NV)
print('nel           =',nel)
print('dt(yr)        =',dt/year)
print('nstep         =',nstep)
print('Young modulus =',E)
print('shear modulus =',mu)
print('bulk modulus  =',K)
print('poisson ratio =',nu)
print("-----------------------------")

#####################################################################
# grid point setup 
#####################################################################
start = timing.time()

xV = np.empty(NV,dtype=np.float64)  # x coordinates
yV = np.empty(NV,dtype=np.float64)  # y coordinates

hx=Lx/float(nelx)
hy=Ly/float(nely)

counter = 0
for j in range(0,nny):
    for i in range(0,nnx):
        xV[counter]=i*hx/2
        yV[counter]=j*hy/2
        counter += 1
    #end for
#end for

print("mesh: %.3fs" % (timing.time() - start))

#####################################################################
# connectivity
#####################################################################
start = timing.time()

iconV=np.zeros((mV,nel),dtype=np.int32)

counter = 0
for j in range(0,nely):
    for i in range(0,nelx):
        iconV[0,counter]=(i)*2+1+(j)*2*nnx -1
        iconV[1,counter]=(i)*2+3+(j)*2*nnx -1
        iconV[2,counter]=(i)*2+3+(j)*2*nnx+nnx*2 -1
        iconV[3,counter]=(i)*2+1+(j)*2*nnx+nnx*2 -1
        iconV[4,counter]=(i)*2+2+(j)*2*nnx -1
        iconV[5,counter]=(i)*2+3+(j)*2*nnx+nnx -1
        iconV[6,counter]=(i)*2+2+(j)*2*nnx+nnx*2 -1
        iconV[7,counter]=(i)*2+1+(j)*2*nnx+nnx -1
        iconV[8,counter]=(i)*2+2+(j)*2*nnx+nnx -1
        counter += 1
    #end for
#end for

print("connectivity: %.3fs" % (timing.time() - start))

#####################################################################
# assigning material to elements 
#####################################################################
start = timing.time()

phase= np.zeros(nel,dtype=np.int32)
xc   = np.zeros(nel,dtype=np.float64) 
yc   = np.zeros(nel,dtype=np.float64) 
eta  = np.zeros(nel,dtype=np.float64)

if experiment==1:
   for iel in range(0,nel):
       xc[iel]=0.5*(xV[iconV[0,iel]]+xV[iconV[2,iel]])
       yc[iel]=0.5*(yV[iconV[0,iel]]+yV[iconV[2,iel]])
       if yc[iel]>0.55:
          phase[iel]=1
       elif yc[iel]>0.45:
          phase[iel]=3
       else:
          phase[iel]=2
       eta[iel]=viscosity[phase[iel]-1]

if experiment==2:
   for iel in range(0,nel):
       xc[iel]=0.5*(xV[iconV[0,iel]]+xV[iconV[2,iel]])
       yc[iel]=0.5*(yV[iconV[0,iel]]+yV[iconV[2,iel]])
       phase[iel]=1
       eta[iel]=viscosity[phase[iel]-1]

print("material layout: %.3f s" % (timing.time() - start))

#################################################################
# add random perturbation to central layer
#################################################################
start = timing.time()

if experiment==1:
   for i in range(0,NV):
       if abs(yV[i]-0.45)/Ly<eps:
          yV[i]+=hy*0.05*random.uniform(-1,1)
       if abs(yV[i]-0.55)/Ly<eps:
          yV[i]+=hy*0.05*random.uniform(-1,1)

print("add perturbation to layer: %.3f s" % (timing.time() - start))

#################################################################
# define boundary conditions
#################################################################
start = timing.time()

bc_fix=np.zeros(Nfem,dtype=np.bool)  # boundary condition, yes/no
bc_val=np.zeros(Nfem,dtype=np.float64)  # boundary condition, value

if experiment==1:
   for i in range(0, NV):
       if xV[i]/Lx<eps: #Left boundary  
          bc_fix[i*ndof  ] = True ; bc_val[i*ndof+1] = 0  
       if xV[i]/Lx>1-eps: #right boundary  
          bc_fix[i*ndof  ] = True ; bc_val[i*ndof  ] = -5e-3/year  
       if yV[i]/Ly<eps: #bottom boundary  
          bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0 

if experiment==2:
   for i in range(0, NV):
       if xV[i]/Lx<eps: #Left boundary  
          bc_fix[i*ndof  ] = True ; bc_val[i*ndof+1] = 0  
       if xV[i]/Lx>1-eps: #right boundary  
          bc_fix[i*ndof  ] = True ; bc_val[i*ndof  ] = 1*cm/year  
       if yV[i]/Ly<eps: #bottom boundary  
          bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0 
       if yV[i]/Ly>1-eps: #top boundary  
          bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = -1*cm/year

print("define boundary conditions: %.3f s" % (timing.time() - start))

#==============================================================================
# time stepping loop
#==============================================================================

model_time=0.
    
u = np.zeros(NV,dtype=np.float64) 
v = np.zeros(NV,dtype=np.float64) 
xq = np.zeros(nq,dtype=np.float64) 
yq = np.zeros(nq,dtype=np.float64) 
stress0_vector    = np.zeros((3,nq),dtype=np.float64) # stress vector memory
stress_vector     = np.zeros((3,nq),dtype=np.float64) # stress vector 
strainrate_vector = np.zeros((3,nq),dtype=np.float64) # strain rate vector

for istep in range(0,nstep):

    print("-----------------------------")
    print("istep= ", istep,'/',nstep-1)
    print("-----------------------------")

    A_sparse = lil_matrix((Nfem,Nfem),dtype=np.float64) # FE matrix
    rhs      = np.zeros(Nfem,dtype=np.float64)          # right hand side of Ax=b
    NNNV     = np.zeros(mV,dtype=np.float64)            # shape functions V
    dNNNVdr  = np.zeros(mV,dtype=np.float64)            # shape functions derivatives
    dNNNVds  = np.zeros(mV,dtype=np.float64)            # shape functions derivatives
    dNNNVdx  = np.zeros(mV,dtype=np.float64)            # shape functions derivatives
    dNNNVdy  = np.zeros(mV,dtype=np.float64)            # shape functions derivatives
    b_mat    = np.zeros((3,ndof*mV),dtype=np.float64)   # gradient matrix B 

    counterq=0
    for iel in range(0,nel):

        # set arrays to 0 every loop
        f_el =np.zeros((mV*ndof),dtype=np.float64)
        K_el =np.zeros((mV*ndof,mV*ndof),dtype=np.float64)

        #viscoelastic material matrix
        di=dt*(3*eta[iel]*K+3*dt*mu*K+4*mu*eta[iel])
        od=dt*(-2*mu*eta[iel]+3*eta[iel]*K+3*dt*mu*K)
        d=3*(eta[iel]+dt*mu)
        ed=eta[iel]*dt*mu/(eta[iel]+dt*mu)
        Dee = np.array([[di/d, od/d,  0],\
                        [od/d, di/d,  0],\
                        [0,       0, ed]],dtype=np.float64)

        #stress matrix for rhs
        di=3*eta[iel]+dt*mu
        od=dt*mu 
        ed=eta[iel]/(eta[iel]+dt*mu) 
        Dees = np.array([[di/d, od/d,  0],\
                         [od/d, di/d,  0],\
                         [0,       0, ed]],dtype=np.float64)

        # integrate viscous term at 4 quadrature points
        for iq in [0,1,2]:
            for jq in [0,1,2]:

                # position & weight of quad. point
                rq=qcoords[iq]
                sq=qcoords[jq]
                weightq=qweights[iq]*qweights[jq]

                NNNV[0:9]=NNV(rq,sq)
                dNNNVdr[0:9]=dNNVdr(rq,sq)
                dNNNVds[0:9]=dNNVds(rq,sq)

                # calculate jacobian matrix
                jcb=np.zeros((ndim,ndim),dtype=np.float64)
                for k in range(0,mV):
                    jcb[0,0]+=dNNNVdr[k]*xV[iconV[k,iel]]
                    jcb[0,1]+=dNNNVdr[k]*yV[iconV[k,iel]]
                    jcb[1,0]+=dNNNVds[k]*xV[iconV[k,iel]]
                    jcb[1,1]+=dNNNVds[k]*yV[iconV[k,iel]]
                jcob = np.linalg.det(jcb)
                jcbi = np.linalg.inv(jcb)

                # compute dNdx & dNdy
                xq[counterq]=0
                yq[counterq]=0
                exxq=0
                eyyq=0
                exyq=0
                for k in range(0,mV):
                    dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
                    dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]
                    xq[counterq]+=NNNV[k]*xV[iconV[k,iel]]
                    yq[counterq]+=NNNV[k]*yV[iconV[k,iel]]
                    exxq+=dNNNVdx[k]*u[iconV[k,iel]]
                    eyyq+=dNNNVdy[k]*v[iconV[k,iel]]
                    exyq+=dNNNVdy[k]*u[iconV[k,iel]]*0.5+\
                          dNNNVdx[k]*v[iconV[k,iel]]*0.5

                strainrate_vector[0,counterq]=exxq
                strainrate_vector[1,counterq]=eyyq
                strainrate_vector[2,counterq]=exyq

                stress_vector[:,counterq]=Dee.dot(strainrate_vector[:,counterq])+\
                                          Dees.dot(stress0_vector[:,counterq])

                # construct 3x8 b_mat matrix
                for i in range(0,mV):
                    b_mat[0:3, 2*i:2*i+2] = [[dNNNVdx[i],0.     ],
                                             [0.        ,dNNNVdy[i]],
                                             [dNNNVdy[i],dNNNVdx[i]]]

                # compute elemental a_mat matrix
                K_el+=b_mat.T.dot(Dee.dot(b_mat))*weightq*jcob

                # compute elemental rhs vector
                for i in range(0,mV):
                    f_el[ndof*i  ]-=NNNV[i]*jcob*weightq*gx*rho
                    f_el[ndof*i+1]-=NNNV[i]*jcob*weightq*gy*rho

                f_el-=b_mat.T.dot(stress_vector[:,counterq])*weightq*jcob

                counterq+=1
            #end for
        #end for

        # apply boundary conditions
        for k1 in range(0,mV):
            for i1 in range(0,ndof):
                ikk=ndof*k1          +i1
                m1 =ndof*iconV[k1,iel]+i1
                if bc_fix[m1]:
                   K_ref=K_el[ikk,ikk] 
                   for jkk in range(0,mV*ndof):
                       f_el[jkk]-=K_el[jkk,ikk]*bc_val[m1]
                       K_el[ikk,jkk]=0
                       K_el[jkk,ikk]=0
                   #end for 
                   K_el[ikk,ikk]=K_ref
                   f_el[ikk]=K_ref*bc_val[m1]
                #end if 
            #end for 
        #end for 

        # assemble matrix A_mat and right hand side rhs
        for k1 in range(0,mV):
             for i1 in range(0,ndof):
                 ikk=ndof*k1          +i1
                 m1 =ndof*iconV[k1,iel]+i1
                 for k2 in range(0,mV):
                     for i2 in range(0,ndof):
                         jkk=ndof*k2          +i2
                         m2 =ndof*iconV[k2,iel]+i2
                         A_sparse[m1,m2]+=K_el[ikk,jkk]
                     #end for 
                 #end for 
                 rhs[m1]+=f_el[ikk]
             #end for 
         #end for 

    #end for iel

    print("building temperature matrix and rhs: %.3f s" % (timing.time() - start))

    #################################################################
    # solve system
    #################################################################
    start = timing.time()

    sol = sps.linalg.spsolve(sps.csr_matrix(A_sparse),rhs)

    u,v=np.reshape(sol,(NV,2)).T

    print("     -> u (m,M) %e %e (cm/year)" %(np.min(u/cm*year),np.max(u/cm*year)))
    print("     -> v (m,M) %e %e (cm/year)" %(np.min(v/cm*year),np.max(v/cm*year)))

    #np.savetxt('velocity.ascii',np.array([xV,yV,u,v]).T,header='# x,y,u,v')

    print("solve FE system: %.3f s" % (timing.time() - start))

    #################################################################
    start = timing.time()

    stats_vel_file.write("%e %e %e %e %e\n" % (model_time,np.min(u),np.max(u),np.min(v),np.max(v)))
    stats_vel_file.flush()

    if istep>0:
       stats_exx_file.write("%e %e %e \n" % (model_time,np.min(strainrate_vector[0,:]),np.max(strainrate_vector[0,:])))
       stats_exx_file.flush()
       stats_eyy_file.write("%e %e %e \n" % (model_time,np.min(strainrate_vector[1,:]),np.max(strainrate_vector[1,:])))
       stats_eyy_file.flush()
       stats_exy_file.write("%e %e %e \n" % (model_time,np.min(strainrate_vector[2,:]),np.max(strainrate_vector[2,:])))
       stats_exy_file.flush()
       stats_sxx_file.write("%e %e %e \n" % (model_time,np.min(stress_vector[0,:]),np.max(stress_vector[0,:])))
       stats_sxx_file.flush()
       stats_syy_file.write("%e %e %e \n" % (model_time,np.min(stress_vector[1,:]),np.max(stress_vector[1,:])))
       stats_syy_file.flush()
       stats_sxy_file.write("%e %e %e \n" % (model_time,np.min(stress_vector[2,:]),np.max(stress_vector[2,:])))
       stats_sxy_file.flush()

    print("export stats in files: %.3f s" % (timing.time() - start))

    #################################################################
    # moving mesh nodes
    #################################################################
    start = timing.time()

    xV[:]+=u[:]*dt
    yV[:]+=v[:]*dt

    print("evolve mesh: %.3f s" % (timing.time() - start))

    #################################################################
    # visualisation
    # stress components are exported in the solution file by 
    # simply using the value for the quadrature point in the middle
    # of the element. 
    #################################################################
    start = timing.time()

    if istep%every==0:

       filename = 'solution_{:04d}.vtu'.format(istep) 
       vtufile=open(filename,"w")
       vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
       vtufile.write("<UnstructuredGrid> \n")
       vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(NV,nel))
       #####
       vtufile.write("<Points> \n")
       vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
       for i in range(0,NV):
           vtufile.write("%e %e %e \n" %(xV[i],yV[i],0.))
       vtufile.write("</DataArray>\n")
       vtufile.write("</Points> \n")
       #####
       vtufile.write("<CellData Scalars='scalars'>\n")
       vtufile.write("<DataArray type='Float32' Name='phase' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % phase[iel])
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='eta' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % eta[iel])
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='eta_eff' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % (eta[iel]*dt/(dt+eta[iel]/mu)))
       vtufile.write("</DataArray>\n")

       vtufile.write("<DataArray type='Float32' Name='sigma_xx' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % (stress_vector[0,iel*9+5]))
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='sigma_yy' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % (stress_vector[1,iel*9+5]))
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='sigma_xy' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % (stress_vector[2,iel*9+5]))
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='sigma_m' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%e \n" % (0.5*stress_vector[0,iel*9+5]+0.5*stress_vector[0,iel*9+5]))
       vtufile.write("</DataArray>\n")

       vtufile.write("</CellData>\n")
       #####
       vtufile.write("<PointData Scalars='scalars'>\n")
       #--
       vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='velocity (cm/year)' Format='ascii'> \n")
       for i in range(0,NV):
           vtufile.write("%e %e %e \n" %(u[i]/cm*year,v[i]/cm*year,0))
       vtufile.write("</DataArray>\n")
       #--
       #vtufile.write("<DataArray type='Float32' Name='fix_u' Format='ascii'> \n")
       #for i in range(0,NV):
       #    if bc_fix[i*2]:
       #       val=1
       #    else:
       #       val=0
       #    vtufile.write("%10e \n" %val)
       #vtufile.write("</DataArray>\n")
       #-- 
       #vtufile.write("<DataArray type='Float32' Name='fix_v' Format='ascii'> \n")
       #for i in range(0,NV):
       #    if bc_fix[i*2+1]:
       #       val=1
       #    else:
       #       val=0
       #    vtufile.write("%10e \n" %val)
       #vtufile.write("</DataArray>\n")
       vtufile.write("</PointData>\n")
       #####
       vtufile.write("<Cells>\n")
       #--
       vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%d %d %d %d %d %d %d %d\n" %(iconV[0,iel],iconV[1,iel],iconV[2,iel],iconV[3,iel],\
                                                       iconV[4,iel],iconV[5,iel],iconV[6,iel],iconV[7,iel]))
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%d \n" %((iel+1)*8))
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
       for iel in range (0,nel):
           vtufile.write("%d \n" %23)
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("</Cells>\n")
       #####
       vtufile.write("</Piece>\n")
       vtufile.write("</UnstructuredGrid>\n")
       vtufile.write("</VTKFile>\n")
       vtufile.close()

       filename = 'qpts_{:04d}.vtu'.format(istep) 
       vtufile=open(filename,"w")
       vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
       vtufile.write("<UnstructuredGrid> \n")
       vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(nq,nq))
       #####
       vtufile.write("<Points> \n")
       vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e %10e %10e \n" %(xq[iq],yq[iq],0.))
       vtufile.write("</DataArray>\n")
       vtufile.write("</Points> \n")
       #####
       vtufile.write("<PointData Scalars='scalars'>\n")
       vtufile.write("<DataArray type='Float32' Name='sigma_xx' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % stress_vector[0,iq])
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='sigma_yy' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % stress_vector[1,iq])
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='sigma_xy' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % stress_vector[2,iq])
       vtufile.write("</DataArray>\n")

       vtufile.write("<DataArray type='Float32' Name='sigma_m' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % (0.5*(stress_vector[0,iq]+stress_vector[1,iq])))
       vtufile.write("</DataArray>\n")

       vtufile.write("<DataArray type='Float32' Name='e_xx' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % strainrate_vector[0,iq])
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='e_yy' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % strainrate_vector[1,iq])
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Float32' Name='e_xy' Format='ascii'> \n")
       for iq in range(0,nq):
           vtufile.write("%10e \n" % strainrate_vector[2,iq])
       vtufile.write("</DataArray>\n")
       vtufile.write("</PointData>\n")
       #####
       vtufile.write("<Cells>\n")
       vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
       for iq in range (0,nq):
           vtufile.write("%d\n" % iq )
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
       for iq in range (0,nq):
           vtufile.write("%d \n" % (iq+1) )
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
       for iq in range (0,nq):
           vtufile.write("%d \n" % 1)
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("</Cells>\n")
       #####
       vtufile.write("</Piece>\n")
       vtufile.write("</UnstructuredGrid>\n")
       vtufile.write("</VTKFile>\n")
       vtufile.close()

       print("export to files: %.3f s" % (timing.time() - start))

    #end if

    model_time+=dt
    print ("model_time=",model_time/year,'yr')

    stress0_vector[:,:]=stress_vector[:,:]

    shortening=(1-max(xV)/Lx)*100

    print('max(x)=',max(xV),', Lx(t=0)=',Lx)
    print('shortening=',shortening,'%')
    
#end for istep

#==============================================================================
# end time stepping loop
#==============================================================================

print("-----------------------------")
print("------------the end----------")
print("-----------------------------")