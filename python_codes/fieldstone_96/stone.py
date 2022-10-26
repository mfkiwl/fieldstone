import numpy as np
import numpy.ma as ma
import sys as sys
import scipy
import math as math
import scipy.sparse as sps
from scipy.sparse.linalg.dsolve import linsolve
import time as timing
from scipy.sparse import lil_matrix
import triangle as tr
import os 
import matplotlib.pyplot as plt

###############################################################################

use_numba=True

if use_numba:
    from tools_numba import *
    from compute_gravity_at_point_numba import *
    from basis_functions_numba import *
    from material_model_numba import *
else:
    from tools import *
    from compute_gravity_at_point import *
    from basis_functions import *
    from material_model import *

###############################################################################
# Equatorial radius (km) 3396.2
# Polar radius (km)      3376.2 
# Volumetric mean radius (km) 3389.5

Ggrav = 6.67430e-11
year=365.25*3600*24
cm=0.01
km=1000
R_outer=3389.5e3 

###############################################################################
###############################################################################
###############################################################################

print("-----------------------------")
print("----------fieldstone---------")
print("-----------------------------")

CR=False

if CR:
   mV=7     # number of velocity nodes making up an element
else:
   mV=6

mP=3     # number of pressure nodes making up an element
ndofV=2  # number of velocity degrees of freedom per node
ndofP=1  # number of pressure degrees of freedom 

###############################################################################
############# Parameters ######################################################
###############################################################################

eta_ref=1e22 # numerical parameter for FEM

nstep=1 # number of time steps
dt_user=1*year

hhh=40e3 # element size at the surface

#-------------------------------------
# blob setup 
#-------------------------------------
R_blob=300e3            #radius of blob
z_blob=R_outer-1000e3   #starting depth
rho_blob=3200
eta_blob=1e21
np_blob=int(2*np.pi*R_blob/hhh)

#-------------------------------------
#0: 3 layer model
#1: steinberger et al 2010
#2: samuel et al 2021

radial_model=-1

#---------------------------------
if radial_model==-1: 
   nstep=1
   dt_user=0
   R_inner=R_outer-1500e3 
   R_disc1 = R_outer-25e3 
   R_disc2 = R_outer-50e3 
   R_disc3 = R_outer-75e3 
   R_blob=300e3            #radius of blob
   z_blob=R_outer-1000e3   #starting depth
   eta0=1e22
   eta_blob=eta0
   #constant density hollow sphere, no blob
   test=1
   rho0=4000
   rho_blob=rho0
   #zero density hollow sphere + blob
   test=2
   rho0=0
   rho_blob=4000

#---------------------------------
if radial_model==0: # 4layer model 

   R_inner=R_outer-1830e3 #insight

   R_disc1 = R_outer-60e3   #crust
   R_disc2 = R_outer-450e3  # lith
   R_disc3 = R_inner+50e3   #arbitrary layer

   rho_crust=3300
   eta_crust=1e25

   rho_lith=3400
   eta_lith=1e21

   rho_mantle=3500
   eta_mantle=6e20

   rho_layer=4300
   eta_layer=6e20

#---------------------------------
if radial_model==1: # steinberger 
   R_inner=R_outer-1638.5e3

   R_disc1 = R_outer-0e3 
   R_disc2 = R_outer-0e3 
   R_disc3 = R_outer-0e3 

   eta_max=1e25

#---------------------------------
if radial_model==2: #samuel

   R_inner=R_outer-1700e3

   R_disc1 = R_outer-0e3 
   R_disc2 = R_outer-0e3 
   R_disc3 = R_outer-0e3 

   eta_max=1e25

#-------------------------------------

nnt=int(np.pi*R_outer/hhh) 
nnr=int((R_outer-R_inner)/hhh)+1 

#-------------------------------------
#boundary conditions at planet surface
#-------------------------------------
#0: no-slip
#1: free-slip
#2: free (only top surface)

surface_bc=1

cmb_bc=1

#-------------------------------------
# gravity acceleration
#-------------------------------------

use_isog=True
g0=3.72076 #https://en.wikipedia.org/wiki/Mars

#-------------------------------------
#gravity calculation parameters
#-------------------------------------
# gravity_method: 0 -> none
# gravity_method: 1 -> 1 point quad
# gravity_method: 2 -> 6 point quad

gravity_method=2
np_grav=100
nel_phi=int(10*np.pi*R_outer/hhh) 
height=10e3

###############################################################################

print('R_inner=',R_inner)
print('R_outer=',R_outer)
print('Volume=',4*np.pi/3*(R_outer**3-R_inner**3))
print('CR=',CR)
print('height=',height)
print('gravity_method=',gravity_method)
print('height=',height)
print('np_blob=',np_blob)
print('R_blob=',R_blob)
print('z_blob=',z_blob)
print('nnt=',nnt)
print('nnr=',nnr)
print('nel_phi=',nel_phi)
print("-----------------------------")

###############################################################################
# 6 point integration coeffs and weights 
###############################################################################

nqel=6

nb1=0.816847572980459
nb2=0.091576213509771
nb3=0.108103018168070
nb4=0.445948490915965
nb5=0.109951743655322/2.
nb6=0.223381589678011/2.

qcoords_r=np.array([nb1,nb2,nb2,nb4,nb3,nb4],dtype=np.float64) 
qcoords_s=np.array([nb2,nb1,nb2,nb3,nb4,nb4],dtype=np.float64) 
qweights =np.array([nb5,nb5,nb5,nb6,nb6,nb6],dtype=np.float64) 

###############################################################################
#############  Defining the nodes and vertices ################################
###############################################################################
start = timing.time()

#------------------------------------------------------------------------------
# inner boundary counterclockwise
#------------------------------------------------------------------------------
theta = np.linspace(-np.pi*0.5, 0.5*np.pi,nnt, endpoint=False)          #half inner sphere in the x-positive domain
pts_ib = np.stack([np.cos(theta), np.sin(theta)], axis=1) * R_inner     #nnt-points on inner boundary
seg_ib = np.stack([np.arange(nnt), np.arange(nnt) + 1], axis=1)         #vertices on innerboundary (and the last vertices to the upper wall)
for i in range(0,nnt):                                                  #first point must be exactly on the y-axis
    if i==0:
       pts_ib[i,0]=0

#------------------------------------------------------------------------------
# top vertical (left) wall 
#------------------------------------------------------------------------------
topw_z = np.linspace(R_inner,R_outer,nnr,endpoint=False)                #vertical boundary wall from inner to outer boundary sphere
pts_topw = np.stack([np.zeros(nnr),topw_z],axis=1)                      #nnr-points on vertical wall
seg_topw = np.stack([nnt+np.arange(nnr),nnt+np.arange(nnr)+1], axis=1)  #vertices on vertical wall

#------------------------------------------------------------------------------
# outer boundary clockwise
#------------------------------------------------------------------------------
theta = np.linspace(np.pi/2,-np.pi/2,num=nnt,endpoint=False)            #half outer sphere in the x-positive domain
pts_ob = np.stack([np.cos(theta),np.sin(theta)], axis=1)*R_outer        #nnt-points on outer boundary
seg_ob = np.stack([nnr+nnt+np.arange(nnt), nnr+nnt+np.arange(nnt)+1], axis=1) #vertices on outerboundary
for i in range(0,nnt):                                                  #first point must be exactly on the y-axis
    if i==0:
       pts_ob[i,0]=0

#------------------------------------------------------------------------------
# bottom vertical wall
#------------------------------------------------------------------------------
botw_z = np.linspace(-R_outer,-R_inner,nnr,endpoint=False)              #vertical boundary wall from outer to inner boundary sphere
pts_botw = np.stack([np.zeros(nnr),botw_z],axis=1)                      #nnr-points on vertical wall
seg_botw = np.stack([2*nnt+nnr+np.arange(nnr),2*nnt+nnr+np.arange(nnr)+1], axis=1) #vertices on bottem vertical wall
seg_botw[-1,1]=0                                                        #stitch last point to first point with last vertice

#------------------------------------------------------------------------------
# blob 
#------------------------------------------------------------------------------
theta_bl = np.linspace(-np.pi/2,np.pi-np.pi/2,num=np_blob,endpoint=True,dtype=np.float64) #half-sphere in the x and y positive domain
pts_bl = np.stack([R_blob*np.cos(theta_bl),z_blob+R_blob*np.sin(theta_bl)], axis=1) #points on blob outersurface 
seg_bl = np.stack([2*nnt+2*nnr+np.arange(np_blob-1), 2*nnt+2*nnr+np.arange(np_blob-1)+1], axis=1) #vertices on outersurface blob
for i in range(0,np_blob):                                              #first and last point must be exactly on the y-axis.
    if i==0 or i==np_blob-1:
       pts_bl[i,0]=0

#------------------------------------------------------------------------------
# discontinuity #1
#------------------------------------------------------------------------------
theta = np.linspace(np.pi/2,-np.pi/2,num=nnt,endpoint=True)            #half outer sphere in the x-positive domain
pts_mo1 = np.stack([np.cos(theta),np.sin(theta)], axis=1)*R_disc1        #nnt-points on outer boundary
seg_mo1 = np.stack([2*nnt+2*nnr+np_blob+np.arange(nnt-1), 2*nnt+2*nnr+np_blob+np.arange(nnt-1)+1], axis=1) #vertices on disc1
for i in range(0,nnt):                                                 #first and last point must be exactly on the y-axis
    if i==0 or i==nnt-1:
       pts_mo1[i,0]=0    

#------------------------------------------------------------------------------
# discontinuity #2
#------------------------------------------------------------------------------
theta = np.linspace(np.pi/2,-np.pi/2,num=nnt,endpoint=True)            #half outer sphere in the x-positive domain
pts_mo2 = np.stack([np.cos(theta),np.sin(theta)], axis=1)*R_disc2        #nnt-points on outer boundary
seg_mo2 = np.stack([3*nnt+2*nnr+np_blob+np.arange(nnt-1), 3*nnt+2*nnr+np_blob+np.arange(nnt-1)+1], axis=1) #vertices on disc2
for i in range(0,nnt):                                                 #first and last point must be exactly on the y-axis
    if i==0 or i==nnt-1:
       pts_mo2[i,0]=0    

#------------------------------------------------------------------------------
# discontinuity #3
#------------------------------------------------------------------------------
theta = np.linspace(np.pi/2,-np.pi/2,num=nnt,endpoint=True)            #half outer sphere in the x-positive domain
pts_mo3 = np.stack([np.cos(theta),np.sin(theta)], axis=1)*R_disc3        #nnt-points on outer boundary
seg_mo3 = np.stack([4*nnt+2*nnr+np_blob+np.arange(nnt-1), 4*nnt+2*nnr+np_blob+np.arange(nnt-1)+1], axis=1) #vertices on disc3
for i in range(0,nnt):                                                 #first and last point must be exactly on the y-axis
    if i==0 or i==nnt-1:
       pts_mo3[i,0]=0    

# Stacking the nodes and vertices 

seg = np.vstack([seg_ib,seg_topw,seg_ob,seg_botw,seg_bl,seg_mo1,seg_mo2,seg_mo3])
pts = np.vstack([pts_ib,pts_topw,pts_ob,pts_botw,pts_bl,pts_mo1,pts_mo2,pts_mo3]) 

#put all segments and nodes in a dictionary

dict_nodes = dict(vertices=pts, segments=seg,holes=[[0,0]]) #no core so we add a hole at x=0,y=0

print("generate nodes: %.3f s" % (timing.time() - start))

###############################################################################
#############  Create the P1 and P2 mesh ######################################
###############################################################################
#
#  P_2^+           P_-1
#
#  02              02
#  ||\\            ||\\
#  || \\           || \\
#  ||  \\          ||  \\
#  05   04         ||   \\
#  || 06 \\        ||    \\
#  ||     \\       ||     \\
#  00==03==01      00======01
#
# note also that triangle returns nodes 0-5, but not 6.
###############################################################################
start = timing.time()

target_area=str(int(hhh**2/2))
print('target_area=',target_area)

dict_mesh = tr.triangulate(dict_nodes,'pqa'+target_area)

#tr.compare(plt, dict_nodes, dict_mesh)
#plt.axis
#plt.show()
#exit()

print("call mesher: %.3f s" % (timing.time() - start))
start = timing.time()

## define icon, x and z for P1 mesh
iconP1=dict_mesh['triangles'] ; iconP1=iconP1.T
xP1=dict_mesh['vertices'][:,0]
zP1=dict_mesh['vertices'][:,1]
NP1=np.size(xP1)
mP,nel=np.shape(iconP1)
#export_elements_to_vtu(xP1,zP1,iconP1,'meshP1.vtu')

print("make P1 mesh: %.3f s" % (timing.time() - start))
start = timing.time()

NV0,xP2,zP2,iconP2=mesh_P1_to_P2(NP1,nel,xP1,zP1,iconP1)

print("make P2 mesh: %.3f s" % (timing.time() - start))

#export_elements_to_vtuP2(xP2,zP2,iconP2,'meshP2.vtu')

###############################################################################
# compute NP, NV, NfemV, NfemP, Nfem for both element pairs
# and build xV,zV,iconV,xP,zP,iconP
###############################################################################
start = timing.time()

if CR:
   NP=3*nel*ndofP
   NV=NV0+nel
   NfemV=NV*ndofV                       # number of velocity dofs
   NfemP=NP*ndofP                       # number of pressure dofs
   #-----
   #iconV
   #-----
   iconV=np.zeros((mV,nel),dtype=np.int32)
   iconV[0,:]=iconP2[0,:]
   iconV[1,:]=iconP2[1,:]
   iconV[2,:]=iconP2[2,:]
   iconV[3,:]=iconP2[3,:]
   iconV[4,:]=iconP2[4,:]
   iconV[5,:]=iconP2[5,:]
   for iel in range (0,nel):
       iconV[6,iel]=NV0+iel
   #-----
   #xV,zV
   #-----
   xV=np.zeros(NV,dtype=np.float64)     # x coordinates
   zV=np.zeros(NV,dtype=np.float64)     # y coordinates
   xV[0:NV0]=xP2[0:NV0]
   zV[0:NV0]=zP2[0:NV0]
   for iel in range (0,nel):
       xV[NV0+iel]=(xV[iconV[0,iel]]+xV[iconV[1,iel]]+xV[iconV[2,iel]])/3.
       zV[NV0+iel]=(zV[iconV[0,iel]]+zV[iconV[1,iel]]+zV[iconV[2,iel]])/3.
   #-----------
   #iconP,xP,zP
   #-----------
   xP=np.empty(NP,dtype=np.float64)  # x coordinates
   zP=np.empty(NP,dtype=np.float64)  # y coordinates
   rP=np.empty(NP,dtype=np.float64)  # x coordinates
   iconP=np.zeros((mP,nel),dtype=np.int32)
   counter=0
   for iel in range(0,nel):
       xP[counter]=xP1[iconP1[0,iel]]
       zP[counter]=zP1[iconP1[0,iel]]
       iconP[0,iel]=counter
       counter+=1
       xP[counter]=xP1[iconP1[1,iel]]
       zP[counter]=zP1[iconP1[1,iel]]
       iconP[1,iel]=counter
       counter+=1
       xP[counter]=xP1[iconP1[2,iel]]
       zP[counter]=zP1[iconP1[2,iel]]
       iconP[2,iel]=counter
       rP[counter]=np.sqrt(xP[counter]**2+zP[counter]**2)
       counter+=1

else:
   NP=NP1
   NV=NV0 #replace by NP2
   NfemV=NV*ndofV    # number of velocity dofs
   NfemP=NP*ndofP    # number of pressure dofs
   #-----
   #iconV
   #-----
   iconV=np.zeros((mV,nel),dtype=np.int32)
   iconV[0,:]=iconP2[0,:]
   iconV[1,:]=iconP2[1,:]
   iconV[2,:]=iconP2[2,:]
   iconV[3,:]=iconP2[3,:]
   iconV[4,:]=iconP2[4,:]
   iconV[5,:]=iconP2[5,:]
   #-----
   #xV,zV
   #-----
   xV=np.zeros(NV,dtype=np.float64)     # x coordinates
   zV=np.zeros(NV,dtype=np.float64)     # y coordinates
   xV[0:NV0]=xP2[0:NV0]
   zV[0:NV0]=zP2[0:NV0]
   #-----
   #iconP
   #-----
   iconP=np.zeros((mP,nel),dtype=np.int32)
   iconP[0,:]=iconP1[0,:]
   iconP[1,:]=iconP1[1,:]
   iconP[2,:]=iconP1[2,:]
   #-----------
   #xP,zP
   #-----------
   xP=np.empty(NfemP,dtype=np.float64)  # x coordinates
   zP=np.empty(NfemP,dtype=np.float64)  # y coordinates
   rP=np.empty(NfemP,dtype=np.float64)  # y coordinates
   xP[0:NP]=xP1[0:NV]
   zP[0:NP]=zP1[0:NV]
   rP[:]=np.sqrt(xP[:]**2+zP[:]**2)


Nfem=NfemV+NfemP  # total number of dofs

print('     -> nel', nel)
print('     -> NV', NV)
print('     -> NfemV', NfemV)
print('     -> NfemP', NfemP)
print('     -> Nfem', Nfem)
print("     -> xV (min/max): %.4f %.4f" %(np.min(xV),np.max(xV)))
print("     -> zV (min/max): %.4f %.4f" %(np.min(zV),np.max(zV)))
print("     -> xP (min/max): %.4f %.4f" %(np.min(xP),np.max(xP)))
print("     -> zP (min/max): %.4f %.4f" %(np.min(zP),np.max(zP)))

print("generate FE meshes: %.3f s" % (timing.time() - start))

###############################################################################
# read profiles 
###############################################################################
start = timing.time()

#---------------------------
if radial_model==-1: #constant density hollow sphere
   npt_rho=1000
   npt_eta=1000
   profile_rho=np.empty((2,npt_rho),dtype=np.float64) 
   profile_eta=np.empty((2,npt_rho),dtype=np.float64) 
   for i in range(0,npt_rho):
       profile_rho[0,i]=R_inner+(R_outer-R_inner)/(npt_rho-1)*i
       profile_eta[0,i]=R_inner+(R_outer-R_inner)/(npt_eta-1)*i
   profile_rho[1,:]=rho0
   profile_eta[1,:]=eta0

#---------------------------
if radial_model==0: # 3 layer model

   npt_rho=1000
   npt_eta=1000
   profile_rho=np.empty((2,npt_rho),dtype=np.float64) 
   profile_eta=np.empty((2,npt_rho),dtype=np.float64) 
   for i in range(0,npt_rho):
       profile_rho[0,i]=R_inner+(R_outer-R_inner)/(npt_rho-1)*i
       profile_eta[0,i]=R_inner+(R_outer-R_inner)/(npt_eta-1)*i

   for i in range(0,npt_rho):
       if profile_rho[0,i]>R_disc1:
          profile_rho[1,i]=rho_crust       
       elif profile_rho[0,i]>R_disc2:
          profile_rho[1,i]=rho_lith       
       elif profile_rho[0,i]>R_disc3:
          profile_rho[1,i]=rho_mantle     
       else:
          profile_rho[1,i]=rho_layer     

   for i in range(0,npt_eta):
       if profile_eta[0,i]>R_disc1:
          profile_eta[1,i]=eta_crust       
       elif profile_eta[0,i]>R_disc2:
          profile_eta[1,i]=eta_lith       
       elif profile_eta[0,i]>R_disc3:
          profile_eta[1,i]=eta_mantle       
       else:
          profile_eta[1,i]=eta_layer

#---------------------------
if radial_model==1: #steinberger

   npt_rho=3390
   npt_eta=1968

   profile_eta=np.empty(npt_eta,dtype=np.float64) 
   profile_depth=np.empty(npt_eta,dtype=np.float64) 
   #profile_eta,profile_depth=np.loadtxt('data/steinberger_eta.ascii',unpack=True,usecols=[0,1])

   profile_rho=np.empty(npt_rho,dtype=np.float64) 
   profile_depth=np.empty(npt_rho,dtype=np.float64) 
   #profile_rho,profile_depth=np.loadtxt('data/steinberger_rho.ascii',unpack=True,usecols=[0,1])

   # gets current file path as string 
   cfilepath = os.path.dirname(os.path.abspath(__file__)) 
   # changes the current working directory to current file path    
   os.chdir(cfilepath)
   profile_eta,profile_depth=np.loadtxt(cfilepath + '/data/steinberger_eta.ascii',unpack=True,usecols=[0,1]) 
   profile_rho,profile_depth=np.loadtxt(cfilepath + '/data/steinerger_rho.ascii',unpack=True,usecols=[0,1]) 

   profile_eta[:]=10**profile_eta[:]
   profile_rho[:]=1000*profile_rho[:]

#---------------------------
if radial_model==2: # samuel

   npt_rho=410
   npt_eta=307

   profile_eta=np.empty(npt_eta,dtype=np.float64) 
   profile_depth=np.empty(npt_eta,dtype=np.float64) 
   #profile_eta,profile_depth=np.loadtxt('data/samuel_eta.ascii',unpack=True,usecols=[0,1])

   profile_rho=np.empty(npt_rho,dtype=np.float64) 
   profile_depth=np.empty(npt_rho,dtype=np.float64) 
   #profile_rho,profile_depth=np.loadtxt('data/samuel_rho.ascii',unpack=True,usecols=[0,1])

   # gets current file path as string 
   cfilepath = os.path.dirname(os.path.abspath(__file__)) 
   # changes the current working directory to current file path    
   os.chdir(cfilepath)
   profile_eta,profile_depth=np.loadtxt(cfilepath + '/data/samuel_eta.ascii',unpack=True,usecols=[0,1]) 
   profile_rho,profile_depth=np.loadtxt(cfilepath + '/data/samuel_rho.ascii',unpack=True,usecols=[0,1]) 

   #*MANIPULATE

#np.savetxt('profile_rho.ascii',np.array([profile_rad,profile_rho]).T)

print("read profiles: %.3f s" % (timing.time() - start))

###############################################################################
# from density profile build gravity profile
###############################################################################
start = timing.time()

profile_grav=np.zeros(npt_rho,dtype=np.float64) 
profile_mass=np.zeros(npt_rho,dtype=np.float64) 

#profile_grav[0]=0
#for i in range(1,npt_rho):
#    profile_mass[i]=profile_mass[i-1]+4*np.pi/3*(profile_rad[i]**3-profile_rad[i-1]**3)\
#                                     *(profile_rho[i]+profile_rho[i-1])/2
#    profile_grav[i]=Ggrav*profile_mass[i]/profile_rad[i]**2
    
#np.savetxt('profile_grav.ascii',np.array([profile_rad,profile_mass,profile_grav]).T)

print("build additional profiles: %.3f s" % (timing.time() - start))

###############################################################################
# project mid-edge nodes onto circle at surface and cmb
# and compute r,theta (spherical coordinates) for each node
###############################################################################
start = timing.time()

theta_nodal=np.zeros(NV,dtype=np.float64)
r_nodal=np.zeros(NV,dtype=np.float64)
surface_node=np.zeros(NV,dtype=np.bool) 
cmb_node=np.zeros(NV,dtype=np.bool) 

for i in range(0,NV):
    theta_nodal[i]=np.arctan2(xV[i],zV[i])
    r_nodal[i]=np.sqrt(xV[i]**2+zV[i]**2)
    if r_nodal[i]>0.999*R_outer:
       r_nodal[i]=R_outer*0.99999999
       xV[i]=r_nodal[i]*np.sin(theta_nodal[i])
       zV[i]=r_nodal[i]*np.cos(theta_nodal[i])
       surface_node[i]=True
    if r_nodal[i]<1.001*R_inner:
       r_nodal[i]=R_inner*1.00000001
       xV[i]=r_nodal[i]*np.sin(theta_nodal[i])
       zV[i]=r_nodal[i]*np.cos(theta_nodal[i])
       cmb_node[i]=True

print("     -> theta_nodal (m,M) %.6e %.6e " %(np.min(theta_nodal),np.max(theta_nodal)))
print("     -> r_nodal (m,M) %.6e %.6e "     %(np.min(r_nodal),np.max(r_nodal)))

#np.savetxt('gridV_after.ascii',np.array([xV,zV]).T,header='# xV,zV')

print("flag cmb nodes: %.3f s" % (timing.time() - start))

###############################################################################
# make blob a sphere - push mid edges out
###############################################################################
start = timing.time()

#np.savetxt('gridV_before.ascii',np.array([xV,zV]).T,header='# xV,zV')

for iel in range(0,nel):
    inode1=iconV[0,iel]
    inode2=iconV[1,iel]
    if abs(xV[inode1]**2+(zV[inode1]-z_blob)**2-R_blob**2)/R_blob**2<1e-4 and\
       abs(xV[inode2]**2+(zV[inode2]-z_blob)**2-R_blob**2)/R_blob**2<1e-4 :
       inode_mid=iconV[3,iel]
       theta=np.arctan2(xV[inode_mid],zV[inode_mid]-z_blob)
       xV[inode_mid]=R_blob*np.sin(theta)
       zV[inode_mid]=R_blob*np.cos(theta)+z_blob

    inode1=iconV[1,iel]
    inode2=iconV[2,iel]
    if abs(xV[inode1]**2+(zV[inode1]-z_blob)**2-R_blob**2)/R_blob**2<1e-4 and\
       abs(xV[inode2]**2+(zV[inode2]-z_blob)**2-R_blob**2)/R_blob**2<1e-4 :
       inode_mid=iconV[4,iel]
       theta=np.arctan2(xV[inode_mid],zV[inode_mid]-z_blob)
       xV[inode_mid]=R_blob*np.sin(theta)
       zV[inode_mid]=R_blob*np.cos(theta)+z_blob

    inode1=iconV[2,iel]
    inode2=iconV[0,iel]
    if abs(xV[inode1]**2+(zV[inode1]-z_blob)**2-R_blob**2)/R_blob**2<1e-4 and\
       abs(xV[inode2]**2+(zV[inode2]-z_blob)**2-R_blob**2)/R_blob**2<1e-4 :
       inode_mid=iconV[5,iel]
       theta=np.arctan2(xV[inode_mid],zV[inode_mid]-z_blob)
       xV[inode_mid]=R_blob*np.sin(theta)
       zV[inode_mid]=R_blob*np.cos(theta)+z_blob

#np.savetxt('gridV_after.ascii',np.array([xV,zV]).T,header='# xV,zV')

print("making blob a sphere: %.3f s" % (timing.time() - start))

###############################################################################
# flag surface P nodes (needed for p normalisation)
###############################################################################
start = timing.time()

surface_Pnode=np.zeros(NP,dtype=np.bool) 
for i in range(0,NP):
    rP[i]=np.sqrt(xP[i]**2+zP[i]**2)
    if rP[i]>=0.999*R_outer: 
       surface_Pnode[i]=True

#np.savetxt('gridP.ascii',np.array([xP,zP,rP,surface_Pnode]).T,header='# x,y')

print("flag surface nodes: %.3f s" % (timing.time() - start))

###############################################################################
# assigning material properties to nodes - only for plotting
###############################################################################
start = timing.time()

eta_nodal=np.zeros(NV,dtype=np.float64) 
rho_nodal=np.zeros(NV,dtype=np.float64) 

for i in range(0,NV):
    eta_nodal[i],rho_nodal[i]=material_model(xV[i],zV[i],eta_blob,rho_blob,z_blob,R_blob,npt_rho,\
                                             npt_eta,profile_rho,profile_eta)

print("     -> eta_nodal (m,M) %.6e %.6e " %(np.min(eta_nodal),np.max(eta_nodal)))
print("     -> rho_nodal (m,M) %.6e %.6e " %(np.min(rho_nodal),np.max(rho_nodal)))

print("compute nodal rho eta: %.3f s" % (timing.time() - start))

######################################################################
# compute element center coordinates
######################################################################
start = timing.time()

xc = np.zeros(nel,dtype=np.float64)  
zc = np.zeros(nel,dtype=np.float64)  

for iel in range(0,nel):
    xc[iel]= (xV[iconV[0,iel]]+xV[iconV[1,iel]]+xV[iconV[2,iel]])/3
    zc[iel]= (zV[iconV[0,iel]]+zV[iconV[1,iel]]+zV[iconV[2,iel]])/3

print("     -> xc (m,M) %.6e %.6e " %(np.min(xc),np.max(xc)))
print("     -> zc (m,M) %.6e %.6e " %(np.min(zc),np.max(zc)))

#np.savetxt('centers.ascii',np.array([xc,zc]).T)

print("compute element center coords: %.3f s" % (timing.time() - start))

###############################################################################
# flag elements inside blob
###############################################################################
start = timing.time()

blob=np.zeros(nel,dtype=np.bool) 

for iel in range(0,nel):
    if xc[iel]**2+(zc[iel]-z_blob)**2<R_blob**2:
       blob[iel]=True

print("flag elts in blob: %.3f s" % (timing.time() - start))

###############################################################################
# assigning material properties to elts- only for plotting
###############################################################################
start = timing.time()

eta_eltal=np.zeros(nel,dtype=np.float64) 
rho_eltal=np.zeros(nel,dtype=np.float64) 

for iel in range(0,nel):
    eta_eltal[iel],rho_eltal[iel]=material_model(xc[iel],zc[iel],eta_blob,rho_blob,z_blob,R_blob,npt_rho,\
                                                 npt_eta,profile_rho,profile_eta)

print("     -> eta_eltal (m,M) %.6e %.6e " %(np.min(eta_eltal),np.max(eta_eltal)))
print("     -> rho_eltal (m,M) %.6e %.6e " %(np.min(rho_eltal),np.max(rho_eltal)))

print("compute eltal rho eta: %.3f s" % (timing.time() - start))

###############################################################################
# define boundary conditions
###############################################################################
start = timing.time()

bc_fix=np.zeros(NfemV,dtype=np.bool)  # boundary condition, yes/no
bc_val=np.zeros(NfemV,dtype=np.float64)  # boundary condition, value
on_surf=np.zeros(NV,dtype=np.bool)  # boundary condition, yes/no

for i in range(0, NV):
    #Left boundary  
    if xV[i]<0.000001*R_inner:
       bc_fix[i*ndofV  ] = True ; bc_val[i*ndofV  ] = 0

    #planet surface
    if surface_node[i] and surface_bc==0: #no-slip surface
       bc_fix[i*ndofV  ] = True ; bc_val[i*ndofV  ] = 0.
       bc_fix[i*ndofV+1] = True ; bc_val[i*ndofV+1] = 0.

    #core mantle boundary
    if cmb_node[i] and cmb_bc==0: #no-slip surface
       bc_fix[i*ndofV  ] = True ; bc_val[i*ndofV  ] = 0.
       bc_fix[i*ndofV+1] = True ; bc_val[i*ndofV+1] = 0.

print("define boundary conditions: %.3f s" % (timing.time() - start))

###############################################################################
# compute area of elements
###############################################################################
start = timing.time()

area=np.zeros(nel,dtype=np.float64) 
arear=np.zeros(nel,dtype=np.float64) 
vol_blob=0

for iel in range(0,nel):
    for kq in range (0,nqel):
        rq=qcoords_r[kq]
        sq=qcoords_s[kq]
        weightq=qweights[kq]
        NNNV=NNV(rq,sq,CR)
        dNNNVdr=dNNVdr(rq,sq,CR)
        dNNNVds=dNNVds(rq,sq,CR)
        jcb=np.zeros((2,2),dtype=np.float64)
        for k in range(0,mV):
            jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
            jcb[0,1] += dNNNVdr[k]*zV[iconV[k,iel]]
            jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
            jcb[1,1] += dNNNVds[k]*zV[iconV[k,iel]]
        jcob = np.linalg.det(jcb)
        area[iel]+=jcob*weightq
        xq=NNNV.dot(xV[iconV[:,iel]])
        arear[iel]+=jcob*weightq*xq*2*np.pi
    if blob[iel]:
       vol_blob+=arear[iel]

VOL=4*np.pi*(R_outer**3-R_inner**3)/3

print("     -> area (m,M) %.6e %.6e " %(np.min(area),np.max(area)))
print("     -> total area (meas) %.6f " %(area.sum()))
print("     -> total area (anal) %.6f " %(np.pi*(R_outer**2-R_inner**2)/2))
print("     -> total vol  (meas) %.6f " %(arear.sum()))
print("     -> total vol  (error) %.6f percent" %((abs(arear.sum()/VOL)-1)*100))
print("     -> blob vol (meas) %.6f " %(vol_blob))
print("     -> blob vol (anal) %.6f " %(4/3*np.pi*R_blob**3))
print("     -> blob vol (error) %.6f percent" % (abs(vol_blob/(4/3*np.pi*R_blob**3)-1)*100))

print("compute elements areas: %.3f s" % (timing.time() - start))

#################################################################
# compute normal to surface 
#################################################################
start = timing.time()

nx=np.zeros(NV,dtype=np.float64)     # x coordinates
nz=np.zeros(NV,dtype=np.float64)     # y coordinates

for i in range(0,NV):
    #Left boundary  
    if xV[i]<0.000001*R_inner:
       nx[i]=-1
       nz[i]=0.
    #planet surface
    if xV[i]**2+zV[i]**2>0.9999*R_outer**2:
       nx[i]=xV[i]/R_outer
       nz[i]=zV[i]/R_outer
#end for

print("compute surface normal vector: %.3f s" % (timing.time() - start))

#################################################################
# flag all elements with a node touching the surface r=R_outer
# or r=R_inner, used later for free slip b.c.
#################################################################
start = timing.time()

flag_top=np.zeros(nel,dtype=np.float64)  
flag_bot=np.zeros(nel,dtype=np.float64)  
for iel in range(0,nel):
    if surface_node[iconV[0,iel]] or surface_node[iconV[1,iel]] or\
       surface_node[iconV[2,iel]] or surface_node[iconV[3,iel]] or\
       surface_node[iconV[4,iel]] or surface_node[iconV[5,iel]]:
       flag_top[iel]=1
    if cmb_node[iconV[0,iel]] or cmb_node[iconV[1,iel]] or\
       cmb_node[iconV[2,iel]] or cmb_node[iconV[3,iel]] or\
       cmb_node[iconV[4,iel]] or cmb_node[iconV[5,iel]]:
       flag_bot[iel]=1

print("flag elts on boundaries: %.3f s" % (timing.time() - start))

###############################################################################

u = np.zeros(NV,dtype=np.float64)           # x-component velocity
v = np.zeros(NV,dtype=np.float64)           # y-component velocity

for istep in range(0,nstep):

    print("-----------------------------")
    print("istep= ", istep)
    print("-----------------------------")

    #################################################################
    # build FE matrix
    # [ K G ][u]=[f]
    # [GT 0 ][p] [h]
    #################################################################
    start = timing.time()

    A_sparse = lil_matrix((Nfem,Nfem),dtype=np.float64)
    rhs      = np.zeros(Nfem,dtype=np.float64)         # right hand side of Ax=b
    f_rhs    = np.zeros(NfemV,dtype=np.float64)        # right hand side f 
    h_rhs    = np.zeros(NfemP,dtype=np.float64)        # right hand side h 
    NNNP     = np.zeros(mP,dtype=np.float64)           # shape functions P
    dNNNVdx  = np.zeros(mV,dtype=np.float64)           # shape functions derivatives
    dNNNVdy  = np.zeros(mV,dtype=np.float64)           # shape functions derivatives
    b_mat    = np.zeros((4,ndofV*mV),dtype=np.float64) # gradient matrix B 
    N_mat    = np.zeros((4,ndofP*mP),dtype=np.float64) # matrix  
    c_mat    = np.array([[2,0,0,0],[0,2,0,0],[0,0,2,0],[0,0,0,1]],dtype=np.float64) 

    mass=0

    for iel in range(0,nel):

        if iel%2000==0:
           print(iel)

        # set arrays to 0 every loop
        f_el =np.zeros((mV*ndofV),dtype=np.float64)
        K_el =np.zeros((mV*ndofV,mV*ndofV),dtype=np.float64)
        G_el=np.zeros((mV*ndofV,mP*ndofP),dtype=np.float64)
        h_el=np.zeros((mP*ndofP),dtype=np.float64)
        NNNP= np.zeros(mP*ndofP,dtype=np.float64)   

        for kq in range (0,nqel):

            # position & weight of quad. point
            rq=qcoords_r[kq]
            sq=qcoords_s[kq]
            weightq=qweights[kq]

            NNNV=NNV(rq,sq,CR)
            dNNNVdr=dNNVdr(rq,sq,CR)
            dNNNVds=dNNVds(rq,sq,CR)
            NNNP[0:mP]=NNP(rq,sq)

            # calculate jacobian matrix
            jcb=np.zeros((2,2),dtype=np.float64)
            for k in range(0,mV):
                jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
                jcb[0,1] += dNNNVdr[k]*zV[iconV[k,iel]]
                jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
                jcb[1,1] += dNNNVds[k]*zV[iconV[k,iel]]
            jcob = np.linalg.det(jcb)
            jcbi = np.linalg.inv(jcb)

            if jcob<0:
               exit("jacobian is negative - bad triangle")

            # compute dNdx & dNdy
            xq=0.0
            yq=0.0
            for k in range(0,mV):
                xq+=NNNV[k]*xV[iconV[k,iel]]
                yq+=NNNV[k]*zV[iconV[k,iel]]
                dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
                dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]

            # compute etaq, rhoq
            etaq,rhoq=material_model(xq,yq,eta_blob,rho_blob,z_blob,R_blob,npt_rho,\
                                     npt_eta,profile_rho,profile_eta)

            for i in range(0,mV):
                b_mat[0:4, 2*i:2*i+2] = [[dNNNVdx[i],0.       ],
                                         [NNNV[i]/xq,0.       ],
                                         [0.        ,dNNNVdy[i]],
                                         [dNNNVdy[i],dNNNVdx[i]]]
            K_el+=b_mat.T.dot(c_mat.dot(b_mat))*etaq*weightq*jcob * 2*np.pi*xq
            for i in range(0,mP):
                N_mat[0,i]=NNNP[i]
                N_mat[1,i]=NNNP[i]
                N_mat[2,i]=NNNP[i]
                N_mat[3,i]=0.
            G_el-=b_mat.T.dot(N_mat)*weightq*jcob * 2*np.pi*xq

            mass+=jcob*weightq*rhoq * 2*np.pi*xq

            #compute gx,gy
            radq=np.sqrt(xq**2+yq**2)
            if use_isog:
               grav=g0
            else:
               grav=profile_grav[int(radq/1000)]
            angle=np.arctan2(yq,xq)
            gx=grav*np.cos(angle)
            gy=grav*np.sin(angle)
            #print(xq,yq,gx,gy)

            for i in range(0,mV):
                f_el[ndofV*i  ]-=NNNV[i]*jcob*weightq*gx*rhoq * 2*np.pi*xq
                f_el[ndofV*i+1]-=NNNV[i]*jcob*weightq*gy*rhoq * 2*np.pi*xq
            #end for 

        #end for kq

        if (surface_bc==1 and flag_top[iel]) or (cmb_bc==1 and flag_bot[iel]):
           for k in range(0,mV):
               inode=iconV[k,iel]
               if surface_node[inode] or cmb_node[inode]:
                  RotMat=np.zeros((mV*ndofV,mV*ndofV),dtype=np.float64)
                  for i in range(0,mV*ndofV):
                      RotMat[i,i]=1.
                  angle=np.pi/2-theta_nodal[inode]
                  #RotMat[2*k  ,2*k]= np.cos(theta_nodal[inode]) ; RotMat[2*k  ,2*k+1]=np.sin(theta_nodal[inode])  
                  #RotMat[2*k+1,2*k]=-np.sin(theta_nodal[inode]) ; RotMat[2*k+1,2*k+1]=np.cos(theta_nodal[inode])  
                  RotMat[2*k  ,2*k]= np.cos(angle) ; RotMat[2*k  ,2*k+1]=np.sin(angle)
                  RotMat[2*k+1,2*k]=-np.sin(angle) ; RotMat[2*k+1,2*k+1]=np.cos(angle)
                  # apply counter rotation 
                  K_el=RotMat.dot(K_el.dot(RotMat.T))
                  f_el=RotMat.dot(f_el)
                  G_el=RotMat.dot(G_el)
                  # apply boundary conditions
                  # x-component set to 0
                  ikk=ndofV*k                 
                  K_ref=K_el[ikk,ikk] 
                  for jkk in range(0,mV*ndofV):
                      K_el[ikk,jkk]=0
                      K_el[jkk,ikk]=0
                  K_el[ikk,ikk]=K_ref
                  f_el[ikk]=0#K_ref*bc_val[m1]
                  #h_el[:]-=G_el[ikk,:]*bc_val[m1]
                  G_el[ikk,:]=0
                  # rotate back 
                  K_el=RotMat.T.dot(K_el.dot(RotMat))
                  f_el=RotMat.T.dot(f_el)
                  G_el=RotMat.T.dot(G_el)


        # impose b.c. 
        for k1 in range(0,mV):
            for i1 in range(0,ndofV):
                ikk=ndofV*k1          +i1
                m1 =ndofV*iconV[k1,iel]+i1
                if bc_fix[m1]:
                   K_ref=K_el[ikk,ikk] 
                   for jkk in range(0,mV*ndofV):
                       f_el[jkk]-=K_el[jkk,ikk]*bc_val[m1]
                       K_el[ikk,jkk]=0
                       K_el[jkk,ikk]=0
                   K_el[ikk,ikk]=K_ref
                   f_el[ikk]=K_ref*bc_val[m1]
                   h_el[:]-=G_el[ikk,:]*bc_val[m1]
                   G_el[ikk,:]=0
                #end if
            #end for 
        #end for

        G_el*=eta_ref/R_outer
        h_el*=eta_ref/R_outer

        # assemble matrix K_mat and right hand side rhs
        for k1 in range(0,mV):
            for i1 in range(0,ndofV):
                ikk=ndofV*k1          +i1
                m1 =ndofV*iconV[k1,iel]+i1
                for k2 in range(0,mV):
                    for i2 in range(0,ndofV):
                        jkk=ndofV*k2          +i2
                        m2 =ndofV*iconV[k2,iel]+i2
                        #K_mat[m1,m2]+=K_el[ikk,jkk]
                        A_sparse[m1,m2] += K_el[ikk,jkk] 
                    #end for
                #end for
                for k2 in range(0,mP):
                    jkk=k2
                    m2 =iconP[k2,iel]
                    #G_mat[m1,m2]+=G_el[ikk,jkk]
                    A_sparse[m1,NfemV+m2]+=G_el[ikk,jkk] 
                    A_sparse[NfemV+m2,m1]+=G_el[ikk,jkk] 
                #end for
                f_rhs[m1]+=f_el[ikk] 
            #end for
        #end for
        for k2 in range(0,mP):
            m2=iconP[k2,iel]
            h_rhs[m2]+=h_el[k2]  
        #end for
    #end for

    rhs[0:NfemV]=f_rhs
    rhs[NfemV:Nfem]=h_rhs

    print('     -> mass=',mass)

    print("build FE matrix: %.3f s" % (timing.time() - start))

    ######################################################################
    # solve system
    ######################################################################
    start = timing.time()

    sol = np.zeros(Nfem,dtype=np.float64) 

    sparse_matrix=A_sparse.tocsr()

    sol=sps.linalg.spsolve(sparse_matrix,rhs)

    u,v=np.reshape(sol[0:NfemV],(NV,2)).T
    p=sol[NfemV:Nfem]*eta_ref/R_outer

    #np.savetxt('solution_velocity.ascii',np.array([xV,zV,u,v]).T,header='# x,y,u,v')
    #np.savetxt('solution_pressure.ascii',np.array([xP,zP,p]).T,header='# x,y,p')

    print("     -> u (m,M) %.6e %.6e " %(np.min(u),np.max(u)))
    print("     -> v (m,M) %.6e %.6e " %(np.min(v),np.max(v)))
    print("     -> p (m,M) %.6e %.6e " %(np.min(p),np.max(p)))

    print("solve time: %.3f s" % (timing.time() - start))

    ######################################################################
    # compute vrms 
    ######################################################################
    start = timing.time()

    vrms=0
    for iel in range(0,0):
        for kq in range (0,nqel):
            # position & weight of quad. point
            rq=qcoords_r[kq]
            sq=qcoords_s[kq]
            weightq=qweights[kq]
            NNNV[0:mV]=NNV(rq,sq,CR)
            dNNNVdr[0:mV]=dNNVdr(rq,sq,CR)
            dNNNVds[0:mV]=dNNVds(rq,sq,CR)
            NNNP[0:mP]=NNP(rq,sq)
            # calculate jacobian matrix
            jcb=np.zeros((2,2),dtype=np.float64)
            for k in range(0,mV):
                jcb[0,0] += dNNNVdr[k]*xV[iconV[k,iel]]
                jcb[0,1] += dNNNVdr[k]*zV[iconV[k,iel]]
                jcb[1,0] += dNNNVds[k]*xV[iconV[k,iel]]
                jcb[1,1] += dNNNVds[k]*zV[iconV[k,iel]]
            jcob = np.linalg.det(jcb)
            # compute dNdx & dNdy
            xq=NNNV[0:mV].dot(xV[iconV[0:mV,iel]])  
            zq=NNNV[0:mV].dot(zV[iconV[0:mV,iel]])
            uq=NNNV[0:mV].dot(u[iconV[0:mV,iel]])
            vq=NNNV[0:mV].dot(v[iconV[0:mV,iel]])
            vrms+=(uq**2+vq**2)*jcob*weightq *xq*2*np.pi
        #end for
    #end for
    vrms=np.sqrt(vrms/(4/3*np.pi*R_outer**3))

    print("     -> nel= %6d ; vrms (m/year)= %e " %(nel,vrms*year))

    print("compute vrms: %.3f s" % (timing.time() - start))

    ######################################################################
    # if free slip  or no slip is used at the surface then there is 
    # a pressure nullspace which needs to be removed. 
    # I here make sure that the pressure is zero on the surface on average
    ######################################################################
    start = timing.time()

    if surface_bc==0 or surface_bc==1:

       counter=0
       perim=0
       avrg_p=0
       for iel in range(0,nel):
           if surface_Pnode[iconP[0,iel]] and surface_Pnode[iconP[1,iel]]:
              xxp=(xP[iconP[0,iel]]+xP[iconP[1,iel]])/2
              zzp=(zP[iconP[0,iel]]+zP[iconP[1,iel]])/2
              ppp=( p[iconP[0,iel]]+ p[iconP[1,iel]])/2
              theta0=np.arctan2(xP[iconP[0,iel]],zP[iconP[0,iel]])
              theta1=np.arctan2(xP[iconP[1,iel]],zP[iconP[1,iel]])
              dtheta=abs(theta0-theta1)
              thetap=np.arctan2(xxp,zzp)
              dist=np.sqrt((xP[iconP[0,iel]]-xP[iconP[1,iel]])**2+(zP[iconP[0,iel]]-zP[iconP[1,iel]])**2)
              perim+=dist
              avrg_p+=ppp*dist
           if surface_Pnode[iconP[1,iel]] and surface_Pnode[iconP[2,iel]]:
              xxp=(xP[iconP[1,iel]]+xP[iconP[2,iel]])/2
              zzp=(zP[iconP[1,iel]]+zP[iconP[2,iel]])/2
              ppp=( p[iconP[1,iel]]+ p[iconP[2,iel]])/2
              theta1=np.arctan2(xP[iconP[1,iel]],zP[iconP[1,iel]])
              theta2=np.arctan2(xP[iconP[2,iel]],zP[iconP[2,iel]])
              dtheta=abs(theta1-theta2)
              thetap=np.arctan2(xxp,zzp)
              dist=np.sqrt((xP[iconP[1,iel]]-xP[iconP[2,iel]])**2+(zP[iconP[1,iel]]-zP[iconP[2,iel]])**2)
              perim+=dist
              avrg_p+=ppp*dist
           if surface_Pnode[iconP[2,iel]] and surface_Pnode[iconP[0,iel]]:
              xxp=(xP[iconP[2,iel]]+xP[iconP[0,iel]])/2
              zzp=(zP[iconP[2,iel]]+zP[iconP[0,iel]])/2
              ppp=( p[iconP[2,iel]]+ p[iconP[0,iel]])/2
              theta2=np.arctan2(xP[iconP[2,iel]],zP[iconP[2,iel]])
              theta0=np.arctan2(xP[iconP[0,iel]],zP[iconP[0,iel]])
              dtheta=abs(theta2-theta0)
              thetap=np.arctan2(xxp,zzp)
              dist=np.sqrt((xP[iconP[2,iel]]-xP[iconP[0,iel]])**2+(zP[iconP[2,iel]]-zP[iconP[0,iel]])**2)
              perim+=dist
              avrg_p+=ppp*dist

       p-=avrg_p/perim 

       print('     -> perim (meas) =',perim)
       print('     -> perim (anal) =',np.pi*R_outer)
       print('     -> perim (error)=',abs(perim-np.pi*R_outer)/(np.pi*R_outer)*100,'%')
       print('     -> p (m,M) %.6e %.6e ' %(np.min(p),np.max(p)))

       #np.savetxt('solution_pressure_normalised.ascii',np.array([xP,zP,p,rP]).T)

    print("normalise pressure: %.3f s" % (timing.time() - start))


    ######################################################################
    # compute nodal strainrate
    #  02              02
    #  ||\\            ||\\
    #  || \\           || \\
    #  ||  \\          ||  \\
    #  05   04         ||   \\
    #  || 06 \\        ||    \\
    #  ||     \\       ||     \\
    #  00==03==01      00======01
    ######################################################################
    start = timing.time()

    e_xx_nodal = np.zeros(NV,dtype=np.float64)  
    e_zz_nodal = np.zeros(NV,dtype=np.float64)  
    e_xz_nodal = np.zeros(NV,dtype=np.float64)  
    tau_xx_nodal = np.zeros(NV,dtype=np.float64)  
    tau_zz_nodal = np.zeros(NV,dtype=np.float64)  
    tau_xz_nodal = np.zeros(NV,dtype=np.float64)  
    cc         = np.zeros(NV,dtype=np.float64)
    q          = np.zeros(NV,dtype=np.float64)

    rVnodes=[0,1,0,0.5,0.5,0,1./3.] # valid for CR and P2P1
    sVnodes=[0,0,1,0,0.5,0.5,1./3.]

    #u[:]=xV[:]
    #v[:]=zV[:]

    for iel in range(0,nel):
        for kk in range(0,mV):
            inode=iconV[kk,iel]
            rq = rVnodes[kk]
            sq = sVnodes[kk]
            NNNV[0:mV]=NNV(rq,sq,CR)
            dNNNVdr[0:mV]=dNNVdr(rq,sq,CR)
            dNNNVds[0:mV]=dNNVds(rq,sq,CR)
            NNNP[0:mP]=NNP(rq,sq)
            jcb=np.zeros((2,2),dtype=np.float64)
            for k in range(0,mV):
                jcb[0,0]+=dNNNVdr[k]*xV[iconV[k,iel]]
                jcb[0,1]+=dNNNVdr[k]*zV[iconV[k,iel]]
                jcb[1,0]+=dNNNVds[k]*xV[iconV[k,iel]]
                jcb[1,1]+=dNNNVds[k]*zV[iconV[k,iel]]
            jcob=np.linalg.det(jcb)
            jcbi=np.linalg.inv(jcb)
            for k in range(0,mV):
                dNNNVdx[k]=jcbi[0,0]*dNNNVdr[k]+jcbi[0,1]*dNNNVds[k]
                dNNNVdy[k]=jcbi[1,0]*dNNNVdr[k]+jcbi[1,1]*dNNNVds[k]
            for k in range(0,mV):
                tau_xx_nodal[inode] += dNNNVdx[k]*u[iconV[k,iel]]*2*(eta_nodal[inode]/eta_ref)        
                tau_zz_nodal[inode] += dNNNVdy[k]*v[iconV[k,iel]]*2*(eta_nodal[inode]/eta_ref)                
                tau_xz_nodal[inode] += 0.5*dNNNVdy[k]*u[iconV[k,iel]]*2*(eta_nodal[inode]/eta_ref)+\
                                       0.5*dNNNVdx[k]*v[iconV[k,iel]]*2*(eta_nodal[inode]/eta_ref)                   
                e_xx_nodal[inode] += dNNNVdx[k]*u[iconV[k,iel]]
                e_zz_nodal[inode] += dNNNVdy[k]*v[iconV[k,iel]]
                e_xz_nodal[inode] += 0.5*dNNNVdy[k]*u[iconV[k,iel]] + 0.5*dNNNVdx[k]*v[iconV[k,iel]]
            for k in range(0,mP):
                q[inode]+= NNNP[k]*p[iconP[k,iel]]   
            #end for
            cc[inode]+=1
        #end for
    #end for
    e_xx_nodal/=cc
    e_zz_nodal/=cc
    e_xz_nodal/=cc
    tau_xx_nodal/=cc
    tau_zz_nodal/=cc
    tau_xz_nodal/=cc
    tau_xx_nodal*=eta_ref
    tau_zz_nodal*=eta_ref
    tau_xz_nodal*=eta_ref
    q[:]/=cc[:]

    #np.savetxt('solution_q.ascii',np.array([xV,zV,q]).T)
    #np.savetxt('solution_tau_cartesian.ascii',np.array([xV,zV,tau_xx_nodal,tau_zz_nodal,tau_xz_nodal]).T)

    print("     -> e_xx_nodal   (m,M) %.6e %.6e " %(np.min(e_xx_nodal),np.max(e_xx_nodal)))
    print("     -> e_zz_nodal   (m,M) %.6e %.6e " %(np.min(e_zz_nodal),np.max(e_zz_nodal)))
    print("     -> e_xz_nodal   (m,M) %.6e %.6e " %(np.min(e_xz_nodal),np.max(e_xz_nodal)))
    print("     -> tau_xx_nodal (m,M) %.6e %.6e " %(np.min(tau_xx_nodal),np.max(tau_xx_nodal)))
    print("     -> tau_zz_nodal (m,M) %.6e %.6e " %(np.min(tau_zz_nodal),np.max(tau_zz_nodal)))
    print("     -> tau_xz_nodal (m,M) %.6e %.6e " %(np.min(tau_xz_nodal),np.max(tau_xz_nodal)))

    print("compute sr and stress: %.3f s" % (timing.time() - start))

    #####################################################################
    # compute stress tensor components
    #####################################################################
    start = timing.time()

    e_rr_nodal=np.zeros(NV,dtype=np.float64)  
    e_tt_nodal=np.zeros(NV,dtype=np.float64)  
    e_rt_nodal=np.zeros(NV,dtype=np.float64)  
    tau_rr_nodal=np.zeros(NV,dtype=np.float64)  
    tau_tt_nodal=np.zeros(NV,dtype=np.float64)  
    tau_rt_nodal=np.zeros(NV,dtype=np.float64)  

    tau_rr_nodal=tau_xx_nodal*np.sin(theta_nodal)**2+2*tau_xz_nodal*np.sin(theta_nodal)*np.cos(theta_nodal)+tau_zz_nodal*np.cos(theta_nodal)**2
    tau_tt_nodal=tau_xx_nodal*np.cos(theta_nodal)**2-2*tau_xz_nodal*np.sin(theta_nodal)*np.cos(theta_nodal)+tau_zz_nodal*np.sin(theta_nodal)**2
    tau_rt_nodal=(tau_xx_nodal-tau_zz_nodal)*np.sin(theta_nodal)*np.cos(theta_nodal)+tau_xz_nodal*(-np.sin(theta_nodal)**2+np.cos(theta_nodal)**2)

    e_rr_nodal=e_xx_nodal*np.sin(theta_nodal)**2+2*e_xz_nodal*np.sin(theta_nodal)*np.cos(theta_nodal)+e_zz_nodal*np.cos(theta_nodal)**2
    e_tt_nodal=e_xx_nodal*np.cos(theta_nodal)**2-2*e_xz_nodal*np.sin(theta_nodal)*np.cos(theta_nodal)+e_zz_nodal*np.sin(theta_nodal)**2
    e_rt_nodal=(e_xx_nodal-e_zz_nodal)*np.sin(theta_nodal)*np.cos(theta_nodal)+e_xz_nodal*(-np.sin(theta_nodal)**2+np.cos(theta_nodal)**2)

    sigma_rr_nodal=-q+tau_rr_nodal
    sigma_tt_nodal=-q+tau_tt_nodal
    sigma_rt_nodal=   tau_rr_nodal

    #np.savetxt('solution_tau_spherical.ascii',np.array([xV,zV,tau_rr_nodal,tau_tt_nodal,tau_rt_nodal]).T)

    print("rotate stresses: %.3f s" % (timing.time() - start))

    #####################################################################
    # compute traction at surface and cmb
    #####################################################################
    start = timing.time()

    tracfile=open('surface_traction_nodal_{:04d}.ascii'.format(istep),"w")
    tracfile.write("# theta sigma_rr x z tau_rr pressure e_rr ")
    for i in range(0,NV):
        if surface_node[i]: 
           tracfile.write("%e %e %e %e %e %e %e\n" \
                          %(theta_nodal[i],tau_rr_nodal[i]-q[i],xV[i],zV[i],tau_rr_nodal[i],q[i],e_rr_nodal[i]))
    tracfile.close()

    #tracfile=open('surface_vr_{:04d}.ascii'.format(istep),"w")
    #for i in range(0,NV):
    #    if surface_node[i]: 
    #       tracfile.write("%10e %10e \n" \
    #                      %(theta_nodal[i],u[i]*np.sin(theta_nodal[i])+v[i]*np.cos(theta_nodal[i])  ))
    #tracfile.close()

    tracfile=open('surface_vt_{:04d}.ascii'.format(istep),"w")
    for i in range(0,NV):
        if surface_node[i]: 
           tracfile.write("%10e %10e \n" \
                          %(theta_nodal[i],u[i]*np.cos(theta_nodal[i])-v[i]*np.sin(theta_nodal[i]) ) )
    tracfile.close()

    tracfile=open('cmb_traction_nodal_{:04d}.ascii'.format(istep),"w")
    for i in range(0,NV):
        if cmb_node[i]: 
           tracfile.write("%e %e %e %e %e %e %e\n" \
                          %(theta_nodal[i],tau_rr_nodal[i]-q[i],xV[i],zV[i],tau_rr_nodal[i],q[i],e_rr_nodal[i]))
    tracfile.close()

    #tracfile=open('cmb_vr_{:04d}.ascii'.format(istep),"w")
    #for i in range(0,NV):
    #    if cmb_node[i]: 
    #       tracfile.write("%10e %10e \n" \
    #                      %(theta_nodal[i],u[i]*np.sin(theta_nodal[i])+v[i]*np.cos(theta_nodal[i])  ))
    #tracfile.close()

    tracfile=open('cmb_vt_{:04d}.ascii'.format(istep),"w")
    for i in range(0,NV):
        if cmb_node[i]: 
           tracfile.write("%10e %10e \n" \
                          %(theta_nodal[i],u[i]*np.cos(theta_nodal[i])-v[i]*np.sin(theta_nodal[i]) ) )
    tracfile.close()
        
    print("compute surface tractions: %.3f s" % (timing.time() - start))

    #####################################################################
    # plot of solution
    # the 7-node P2+ element does not exist in vtk, but the 6-node one does, i.e. type=22. 
    #####################################################################
    start = timing.time()

    #u[:]/=(cm/year)
    #v[:]/=(cm/year)

    filename = 'solution_{:04d}.vtu'.format(istep)
    vtufile=open(filename,"w")
    vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
    vtufile.write("<UnstructuredGrid> \n")
    vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(NV,nel))
    #####
    vtufile.write("<Points> \n")
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" %(xV[i],0.,zV[i]))
    vtufile.write("</DataArray>\n")
    vtufile.write("</Points> \n")
    #####
    vtufile.write("<CellData Scalars='scalars'>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='area' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (area[iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='rho' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (rho_eltal[iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='eta' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (eta_eltal[iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='flag_top' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (flag_top[iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='flag_bot' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%10e\n" % (flag_bot[iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</CellData>\n")
    #####
    vtufile.write("<PointData Scalars='scalars'>\n")
    #--
    vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Name='velocity (cm/year)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e %10e %10e \n" %(u[i]/cm*year,0.,v[i]/cm*year))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32'  Name='vr (cm/year)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % (u[i]*np.sin(theta_nodal[i])+v[i]*np.cos(theta_nodal[i]) ) )
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32'  Name='vt (cm/year)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%10e \n" % (u[i]*np.cos(theta_nodal[i])-v[i]*np.sin(theta_nodal[i]) ) )
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='gravity vector (norm)' Format='ascii'> \n")
    for i in range(0,NV):
        rad=np.sqrt(xV[i]**2+zV[i]**2)
        if use_isog:
           grav=g0
        else:
           grav=profile_grav[int(rad/1000)]
        vtufile.write("%10e \n" %grav)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='p (nod)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%e \n" %q[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='r' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%e \n" %r_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='rho' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%e \n" %rho_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='eta' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%e \n" %eta_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='surface' Format='ascii'> \n")
    for i in range(0,NV):
        if surface_node[i]:
           vtufile.write("%d \n" %1)
        else:
           vtufile.write("%d \n" %0)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='cmb' Format='ascii'> \n")
    for i in range(0,NV):
        if cmb_node[i]:
           vtufile.write("%d \n" %1)
        else:
           vtufile.write("%d \n" %0)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='theta (sph.coords)' Format='ascii'> \n")
    for i in range(0,NV):
        vtufile.write("%e \n" %theta_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='dev. stress (tau_xx)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % tau_xx_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='dev. stress (tau_zz)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % tau_zz_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='dev. stress (tau_xz)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % tau_xz_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='dev. stress (tau_rr)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % tau_rr_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='dev. stress (tau_tt)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % tau_tt_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='dev. stress (tau_rt)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % tau_rt_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='strain rate (e_rr)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % e_rr_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='strain rate (e_tt)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % e_tt_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='strain rate (e_rt)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % e_rt_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='strain rate (e_xx)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % e_xx_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='strain rate (e_zz)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % e_zz_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='strain rate (e_xz)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % e_xz_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='stress (sigma_rr)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % sigma_rr_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='stress (sigma_tt)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % sigma_tt_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='stress (sigma_rt)' Format='ascii'> \n")
    for i in range (0,NV):
        vtufile.write("%10e\n" % sigma_rt_nodal[i])
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='fix_u' Format='ascii'> \n")
    for i in range(0,NV):
        if bc_fix[i*2]:
           val=1
        else:
           val=0
        vtufile.write("%10e \n" %val)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Float32' Name='fix_v' Format='ascii'> \n")
    for i in range(0,NV):
        if bc_fix[i*2+1]:
           val=1
        else:
           val=0
        vtufile.write("%10e \n" %val)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</PointData>\n")
    #####
    vtufile.write("<Cells>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%d %d %d %d %d %d\n" %(iconV[0,iel],iconV[1,iel],iconV[2,iel],\
                                              iconV[3,iel],iconV[4,iel],iconV[5,iel]))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
    for iel in range (0,nel):
        vtufile.write("%d \n" %((iel+1)*6))
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
    for iel in range (0,nel):
        vtufile.write("%d \n" %22)
    vtufile.write("</DataArray>\n")
    #--
    vtufile.write("</Cells>\n")
    #####
    vtufile.write("</Piece>\n")
    vtufile.write("</UnstructuredGrid>\n")
    vtufile.write("</VTKFile>\n")
    vtufile.close()

    print("write data: %.3fs" % (timing.time() - start))

    #####################################################################
    # compute gravity. phi goes from 0 to 2pi
    #####################################################################
    start = timing.time()

    xM=np.zeros(np_grav,dtype=np.float64)     
    yM=np.zeros(np_grav,dtype=np.float64)     
    zM=np.zeros(np_grav,dtype=np.float64)     
    gvect_x=np.zeros(np_grav,dtype=np.float64)   
    gvect_y=np.zeros(np_grav,dtype=np.float64)   
    gvect_z=np.zeros(np_grav,dtype=np.float64)   
    gvect_x_0=np.zeros(np_grav,dtype=np.float64)   
    gvect_y_0=np.zeros(np_grav,dtype=np.float64)   
    gvect_z_0=np.zeros(np_grav,dtype=np.float64)   
    angleM=np.zeros(np_grav,dtype=np.float64)   

    if radial_model==-1: 
       testfile=open('gravity_benchmark.ascii',"w")
       testfile.write("# angle gr_meas gr_anal \n")

    dphi=2*np.pi/nel_phi
    for i in range(0,np_grav):
        angleM[i]=np.pi/2-np.pi/2/(np_grav-1)*i
        xM[i]=(R_outer+height)*np.cos(angleM[i])
        zM[i]=(R_outer+height)*np.sin(angleM[i])

        if gravity_method==0:
           break

        elif gravity_method==1:
           gvect_x[i],gvect_y[i],gvect_z[i]=compute_gravity_at_point1(xM[i],yM[i],zM[i],nel,xV,zV,iconV,arear,dphi,nel_phi,\
                                                                      eta_blob,rho_blob,z_blob,R_blob,npt_rho,\
                                                                      npt_eta,profile_rho,profile_eta)
        elif gravity_method==2:
           gvect_x[i],gvect_y[i],gvect_z[i]=compute_gravity_at_point2(xM[i],yM[i],zM[i],nel,xV,zV,iconV,\
                                                                      dphi,nel_phi,qcoords_r,qcoords_s,qweights,CR,mV,nqel,\
                                                                      eta_blob,rho_blob,z_blob,R_blob,npt_rho,\
                                                                      npt_eta,profile_rho,profile_eta)
        if i%20==0: 
           print('point',i,'gx,gy,gz',gvect_x[i],gvect_y[i],gvect_z[i])

        if test==1:
           dist2=xM[i]**2+zM[i]**2
           gr=Ggrav*rho0*4/3*np.pi*(R_outer**3-R_inner**3)/dist2
           testfile.write("%e %e %e\n" %(angleM[i],np.sqrt(gvect_x[i]**2+gvect_y[i]**2+gvect_z[i]**2),gr))
           
        if test==2:
           dist2=xM[i]**2+(zM[i]-z_blob)**2
           gr=Ggrav*rho_blob*4/3*np.pi*R_blob**3/dist2
           testfile.write("%e %e %e\n" %(np.pi/2-angleM[i],np.sqrt(gvect_x[i]**2+gvect_y[i]**2+gvect_z[i]**2),gr))

    #end for

    gvect=np.sqrt(gvect_x**2+gvect_y**2+gvect_z**2)
    rM=np.sqrt(xM**2+yM**2+zM**2)

    filename = 'gravity_{:04d}.ascii'.format(istep)
    np.savetxt(filename,np.array([xM,yM,zM,rM,angleM,gvect_x,gvect_y,gvect_z,gvect]).T,fmt='%.6e',\
               header='# xM,yM,zM,rM,angleM,gvect_x,gvect_y,gvect_z,gvect')

    if istep>0:
       filename = 'gravity_diff_{:04d}.ascii'.format(istep)
       np.savetxt(filename,np.array([xM,yM,zM,rM,angleM,gvect_x-gvect_x_0,gvect_y-gvect_y_0,gvect_z-gvect_z_0,gvect-gvect_0]).T,fmt='%.6e')
    else:
       gvect_x_0[:]=gvect_x[:]
       gvect_y_0[:]=gvect_y[:]
       gvect_z_0[:]=gvect_z[:]
       gvect_0=np.sqrt(gvect_x_0**2+gvect_y_0**2+gvect_z_0**2)

    print("compute gravity: %.3fs" % (timing.time() - start))

    #####################################################################
    # compute timestep
    #####################################################################
    start = timing.time()

    CFL_nb=1
    dt=CFL_nb*(np.min(np.sqrt(area)))/np.max(np.sqrt(u**2+v**2))

    dt=min(dt,dt_user)

    print('     -> dt = %.6f yr' % (dt/year))

    print("compute dt: %.3fs" % (timing.time() - start))

    #####################################################################
    # evolve mesh
    #####################################################################
    start = timing.time()

    #np.savetxt('meshV_bef_'+str(istep)+'.ascii',np.array([xV/km,zV/km,u,v]).T,header='# x,y')
    #np.savetxt('meshP_bef_'+str(istep)+'.ascii',np.array([xP/km,zP/km]).T,header='# x,y')

    for i in range(0,NV):
        if not surface_node[i] and not cmb_node[i]:
           xV[i]+=u[i]*dt
           zV[i]+=v[i]*dt

    for iel in range(0,nel):
        xP[iconP[0,iel]]=xV[iconV[0,iel]]
        xP[iconP[1,iel]]=xV[iconV[1,iel]]
        xP[iconP[2,iel]]=xV[iconV[2,iel]]
        zP[iconP[0,iel]]=zV[iconV[0,iel]]
        zP[iconP[1,iel]]=zV[iconV[1,iel]]
        zP[iconP[2,iel]]=zV[iconV[2,iel]]

    #np.savetxt('meshV_aft_'+str(istep)+'.ascii',np.array([xV/km,zV/km]).T,header='# x,y')
    #np.savetxt('meshP_aft_'+str(istep)+'.ascii',np.array([xP/km,zP/km]).T,header='# x,y')

    print("evolve mesh: %.3fs" % (timing.time() - start))

#end istep

print("-----------------------------")
print("------------the end----------")
print("-----------------------------")
