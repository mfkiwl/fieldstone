import FEbasis2D as FE
import FEquadrature as Q
import FEtools as Tools 
import numpy as np
import time as timing
import matplotlib.pyplot as plt
import sys as sys
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve
import dh

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

Lx=1
Ly=1

nelx=16
nely=16

left_bc  ='no_slip'
right_bc ='no_slip'
bottom_bc='no_slip'
top_bc   ='no_slip'

ndofV=2
ndofP=1

Vspace='P2+'
Pspace='P-1'

visu=1

# if quadrilateral nqpts is nqperdim
# if triangle nqpts is total nb of qpoints 

nqpts=7

#--------------------------------------------------------------------
# allowing for argument parsing through command line
#--------------------------------------------------------------------

if int(len(sys.argv) == 6):
   nelx = int(sys.argv[1])
   nely = int(sys.argv[2])
   Vspace = sys.argv[3]
   Pspace = sys.argv[4]
   nqpts = int(sys.argv[5])
   visu=0

#--------------------------------------------------------------------
# mesh: node layout and connectivity
#--------------------------------------------------------------------
start = timing.time()

mV=FE.NNN_m(Vspace)
mP=FE.NNN_m(Pspace)

nqel,qcoords_r,qcoords_s,qweights=Q.quadrature(Vspace,nqpts)

NV,nel,xV,yV,iconV=Tools.cartesian_mesh(Lx,Ly,nelx,nely,Vspace)
NP,nel,xP,yP,iconP=Tools.cartesian_mesh(Lx,Ly,nelx,nely,Pspace)

nq=nqel*nel
NfemV=NV*ndofV
NfemP=NP*ndofP
Nfem=NfemV+NfemP

print("*****************************")
print("           daSTONE           ")
print("*****************************")
print ('Vspace =',Vspace)
print ('Pspace =',Pspace)
print ('NV     =',NV)
print ('NP     =',NP)
print ('nel    =',nel)
print ('NfemV  =',NfemV)
print ('NfemP  =',NfemP)
print ('Nfem   =',Nfem)
print("*****************************")


print("mesh setup: %.3f s" % (timing.time() - start))

#--------------------------------------------------------------------
# boundary conditions setup 
#--------------------------------------------------------------------
start = timing.time()

bc_fix,bc_val=Tools.bc_setup(xV,yV,Lx,Ly,ndofV,left_bc,right_bc,bottom_bc,top_bc)

print("bc setup: %.3f s" % (timing.time() - start))

#--------------------------------------------------------------------
# compute area of elements 
# This is a good test because it uses the quadrature points and 
# weights as well as the shape functions. If any area comes out
# negative or zero, or if the sum does not equal to the area of the 
# whole domain then there is a major problem which needs to 
# be addressed before FE are set into motion.
#--------------------------------------------------------------------
start = timing.time()

area=np.zeros(nel,dtype=np.float64) 

for iel in range(0,nel):
    for iq in range(0,nqel):
        rq=qcoords_r[iq]
        sq=qcoords_s[iq]
        weightq=qweights[iq]
        NNNV=FE.NNN(rq,sq,Vspace)
        xq=NNNV.dot(xV[iconV[:,iel]]) 
        yq=NNNV.dot(yV[iconV[:,iel]]) 
        #uq=NNNV.dot(xV[iconV[:,iel]]**3) 
        #vq=NNNV.dot(yV[iconV[:,iel]]**3) 
        dNNNVdr=FE.dNNNdr(rq,sq,Vspace)
        dNNNVds=FE.dNNNds(rq,sq,Vspace)
        jcob,jcbi,dNNNVdx,dNNNVdy=Tools.J(mV,dNNNVdr,dNNNVds,xV[iconV[0:mV,iel]],yV[iconV[0:mV,iel]])
        #uq=dNNNVdx.dot(xV[iconV[:,iel]]**2) 
        #vq=dNNNVdx.dot(yV[iconV[:,iel]]**2) ; print(xq,yq,uq,vq)
        area[iel]+=jcob*weightq
    #end for
#end for
print("     -> area (m,M) %.6e %.6e " %(np.min(area),np.max(area)))
print("     -> total area meas %.8e " %(area.sum()))
print("     -> total area anal %.8e " %(Lx*Ly))

print("compute elements areas: %.3f s" % (timing.time() - start))

#--------------------------------------------------------------------
# build FE matrix
#--------------------------------------------------------------------
start = timing.time()

A_sparse = lil_matrix((Nfem,Nfem),dtype=np.float64)
rhs = np.zeros(Nfem,dtype=np.float64) 

b_mat = np.zeros((3,ndofV*mV),dtype=np.float64)
c_mat = np.array([[2,0,0],[0,2,0],[0,0,1]],dtype=np.float64)
N_mat = np.zeros((3,ndofP*mP),dtype=np.float64) 
    
xq = np.zeros(nq,dtype=np.float64)
yq = np.zeros(nq,dtype=np.float64)
uq = np.zeros(nq,dtype=np.float64)
vq = np.zeros(nq,dtype=np.float64)
pq = np.zeros(nq,dtype=np.float64)

counterq=0

for iel in range(0,nel):

    K_el = np.zeros((mV*ndofV,mV*ndofV),dtype=np.float64)
    G_el = np.zeros((mV*ndofV,mP*ndofP),dtype=np.float64)
    f_el = np.zeros(mV*ndofV,dtype=np.float64)
    h_el = np.zeros(mP*ndofP,dtype=np.float64)

    for iq in range(0,nqel):

        rq=qcoords_r[iq]
        sq=qcoords_s[iq]
        weightq=qweights[iq]

        NNNV=FE.NNN(rq,sq,Vspace)
        dNNNVdr=FE.dNNNdr(rq,sq,Vspace)
        dNNNVds=FE.dNNNds(rq,sq,Vspace)
        NNNP=FE.NNN(rq,sq,Pspace)
        xq[counterq]=NNNV.dot(xV[iconV[0:mV,iel]])
        yq[counterq]=NNNV.dot(yV[iconV[0:mV,iel]])

        jcob,jcbi,dNNNVdx,dNNNVdy=Tools.J(mV,dNNNVdr,dNNNVds,xV[iconV[0:mV,iel]],yV[iconV[0:mV,iel]])

        for k in range(0,mV): 
            b_mat[0:3,2*k:2*k+2] = [[dNNNVdx[k],0.        ],  
                                    [0.        ,dNNNVdy[k]],
                                    [dNNNVdy[k],dNNNVdx[k]]]

        K_el+=b_mat.T.dot(c_mat.dot(b_mat))*dh.eta(xq[counterq],yq[counterq])*weightq*jcob

        for k in range(0,mV): 
            f_el[2*k+0]+=NNNV[k]*jcob*weightq*dh.bx(xq[counterq],yq[counterq])
            f_el[2*k+1]+=NNNV[k]*jcob*weightq*dh.by(xq[counterq],yq[counterq])

        for k in range(0,mP):
            N_mat[0,k]=NNNP[k]
            N_mat[1,k]=NNNP[k]
            N_mat[2,k]=0.

        G_el-=b_mat.T.dot(N_mat)*weightq*jcob

        counterq+=1

    #end for iq

    # apply bc
    Tools.apply_bc(K_el,G_el,f_el,h_el,bc_val,bc_fix,iconV,mV,ndofV,iel)

    # assemble (missing h_el)
    Tools.assemble_K(K_el,A_sparse,iconV,mV,ndofV,iel)
    Tools.assemble_G(G_el,A_sparse,iconV,iconP,NfemV,mV,mP,ndofV,ndofP,iel)
    Tools.assemble_f(f_el,rhs,iconV,mV,ndofV,iel)

#end for iel

print("build FE matrix: %.3f s" % (timing.time() - start))

#plt.spy(A_sparse,markersize=1)
#plt.savefig('matrix_'+Vspace+'_'+Pspace+'.pdf', bbox_inches='tight')

#------------------------------------------------------------------------------
# solve system
#------------------------------------------------------------------------------
start = timing.time()

matrix=A_sparse.tocsr()
sol=spsolve(matrix,rhs)

print("solve time: %.3f s" % (timing.time() - start))

#------------------------------------------------------------------------------
# put solution into separate x,y velocity arrays
#------------------------------------------------------------------------------
start = timing.time()

u,v=np.reshape(sol[0:NfemV],(NV,2)).T
p=sol[NfemV:Nfem]

print("     -> u (m,M) %.4f %.4f " %(np.min(u),np.max(u)))
print("     -> v (m,M) %.4f %.4f " %(np.min(v),np.max(v)))
print("     -> p (m,M) %.4f %.4f " %(np.min(p),np.max(p)))

print("split vel into u,v: %.3f s" % (timing.time() - start))

#------------------------------------------------------------------------------
# normalise pressure 
#------------------------------------------------------------------------------
start = timing.time()

avrg_p=0
for iel in range(0,nel):
    for iq in range(0,nqel):

        rq=qcoords_r[iq]
        sq=qcoords_s[iq]
        weightq=qweights[iq]
        jcob,jcbi,dNNNVdx,dNNNVdy=Tools.J(mV,dNNNVdr,dNNNVds,xV[iconV[0:mV,iel]],yV[iconV[0:mV,iel]])
        NNNP=FE.NNN(rq,sq,Pspace)
        avrg_p+=NNNP.dot(p[iconP[0:mP,iel]])*jcob*weightq

print('     -> avrg_p=',avrg_p)

p-=avrg_p/Lx/Ly

print("     -> p (m,M) %.4f %.4f " %(np.min(p),np.max(p)))
            
print("pressure normalisation: %.3f s" % (timing.time() - start))

#------------------------------------------------------------------------------
# compute vrms and errors
#------------------------------------------------------------------------------
start = timing.time()

errv=0
errp=0
vrms=0
counterq=0
for iel in range(0,nel):
    for iq in range(0,nqel):
        rq=qcoords_r[iq]
        sq=qcoords_s[iq]
        weightq=qweights[iq]
        NNNV=FE.NNN(rq,sq,Vspace)
        dNNNVdr=FE.dNNNdr(rq,sq,Vspace)
        dNNNVds=FE.dNNNds(rq,sq,Vspace)
        NNNP=FE.NNN(rq,sq,Pspace)
        jcob,jcbi,dNNNVdx,dNNNVdy=Tools.J(mV,dNNNVdr,dNNNVds,xV[iconV[0:mV,iel]],yV[iconV[0:mV,iel]])
        uq[counterq]=NNNV.dot(u[iconV[0:mV,iel]])
        vq[counterq]=NNNV.dot(v[iconV[0:mV,iel]])
        pq[counterq]=NNNP.dot(p[iconP[0:mP,iel]])
        vrms+=(uq[counterq]**2+vq[counterq]**2)*weightq*jcob
        errv+=(uq[counterq]-dh.u_th(xq[counterq],yq[counterq]))**2*weightq*jcob+\
              (vq[counterq]-dh.v_th(xq[counterq],yq[counterq]))**2*weightq*jcob
        errp+=(pq[counterq]-dh.p_th(xq[counterq],yq[counterq]))**2*weightq*jcob
        counterq+=1
    #end for iq
#end for iq

vrms=np.sqrt(vrms/(Lx*Ly))
errv=np.sqrt(errv)
errp=np.sqrt(errp)

print("     -> nel= %6d ; vrms= %.8e | vrms_th= %.8e | %7d %7d" %(nel,vrms,dh.vrms_th(),NfemV,NfemP))
print("     -> nel= %6d ; errv= %.8e ; errp= %.8e | %7d %7d" %(nel,errv,errp,NfemV,NfemP))

print("compute vrms & errors: %.3f s" % (timing.time() - start))

#------------------------------------------------------------------------------

if visu:

   Tools.export_elements_to_vtu(xV,yV,iconV,Vspace,'mesh.vtu')

   Tools.export_swarm_to_ascii(xV,yV,'Vnodes.ascii')
   Tools.export_swarm_to_ascii(xP,yP,'Pnodes.ascii')
   Tools.export_swarm_to_vtu(xV,yV,'Vnodes.vtu')
   Tools.export_swarm_to_vtu(xP,yP,'Pnodes.vtu')

   Tools.export_swarm_to_ascii(xq,yq,'Qnodes.ascii')
   Tools.export_swarm_to_vtu(xq,yq,'Qnodes.vtu')
   Tools.export_swarm_vector_to_vtu(xq,yq,uq,vq,'Qnodes_vel.vtu')
   Tools.export_swarm_scalar_to_vtu(xq,yq,pq,'Qnodes_p.vtu')

   Tools.export_swarm_vector_to_vtu(xV,yV,u,v,'solution_velocity.vtu')
   Tools.export_swarm_scalar_to_vtu(xP,yP,p,'solution_pressure.vtu')
   Tools.export_swarm_vector_to_ascii(xV,yV,u,v,'solution_u.ascii')
   Tools.export_swarm_scalar_to_ascii(xP,yP,p,'solution_pressure.ascii')

   Tools.export_connectivity_array_to_ascii(xV,yV,iconV,'iconV.ascii')
   Tools.export_connectivity_array_to_ascii(xP,yP,iconP,'iconP.ascii')

print("*****************************")
print("*****************************")
