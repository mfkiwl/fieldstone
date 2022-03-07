import numpy as np

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def cartesian_mesh(Lx,Ly,nelx,nely,element):

    hx=Lx/nelx
    hy=Ly/nely
    nel=nelx*nely

    #---------------------------------
    if element=='Q0':
       N=nelx*nely
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0 
       for j in range(0,nely):
           for i in range(0,nelx):
               x[counter]=(i+0.5)*hx
               y[counter]=(j+0.5)*hy
               counter += 1
       icon =np.zeros((1,nel),dtype=np.int32)
       counter = 0 
       for j in range(0,nely):
           for i in range(0,nelx):
               icon[0,counter]=counter
               counter += 1
       icon2 =np.zeros((1,nel),dtype=np.int32)
       icon2[:]=icon[:]

    #---------------------------------
    elif element=='Q1':
       N=(nelx+1)*(nely+1)
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0 
       for j in range(0,nely+1):
           for i in range(0,nelx+1):
               x[counter]=i*hx
               y[counter]=j*hy
               counter += 1
       icon =np.zeros((4,nel),dtype=np.int32)
       counter = 0 
       for j in range(0,nely):
           for i in range(0,nelx):
               icon[0,counter]=i+j*(nelx+1)
               icon[1,counter]=i+1+j*(nelx+1)
               icon[2,counter]=i+1+(j+1)*(nelx+1)
               icon[3,counter]=i+(j+1)*(nelx+1)
               counter += 1
       icon2 =np.zeros((4,nel),dtype=np.int32)
       icon2[:]=icon[:]

    #---------------------------------
    elif element=='Q1+':
       N=(nelx+1)*(nely+1)+nel
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0
       for j in range(0,nely+1):
           for i in range(0,nelx+1):
               x[counter]=i*hx
               y[counter]=j*hy
               counter += 1
       for j in range(0,nely):
           for i in range(0,nelx):
               x[counter]=i*hx+1/2.*hx
               y[counter]=j*hy+1/2.*hy
               counter += 1
       icon=np.zeros((5,nel),dtype=np.int32)
       counter = 0
       for j in range(0, nely):
           for i in range(0, nelx):
               icon[0,counter]=i+j*(nelx+1)
               icon[1,counter]=i+1+j*(nelx+1)
               icon[2,counter]=i+1+(j+1)*(nelx+1)
               icon[3,counter]=i+(j+1)*(nelx+1)
               icon[4,counter]=(nelx+1)*(nely+1)+counter
               counter += 1
       icon2=np.zeros((4,nel),dtype=np.int32)
       icon2[0:4,0:nel]=icon[0:4,0:nel]

    #---------------------------------
    elif element=='Q2':
       N=(2*nelx+1)*(2*nely+1)
       nnx=2*nelx+1
       nny=2*nely+1
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0
       for j in range(0,nny):
           for i in range(0,nnx):
               x[counter]=i*hx/2.
               y[counter]=j*hy/2.
               counter += 1
           #end for
       #end for
       icon=np.zeros((9,nel),dtype=np.int32)
       counter = 0
       for j in range(0,nely):
           for i in range(0,nelx):
               icon[0,counter]=(i)*2+1+(j)*2*nnx -1
               icon[1,counter]=(i)*2+3+(j)*2*nnx -1
               icon[2,counter]=(i)*2+3+(j)*2*nnx+nnx*2 -1
               icon[3,counter]=(i)*2+1+(j)*2*nnx+nnx*2 -1
               icon[4,counter]=(i)*2+2+(j)*2*nnx -1
               icon[5,counter]=(i)*2+3+(j)*2*nnx+nnx -1
               icon[6,counter]=(i)*2+2+(j)*2*nnx+nnx*2 -1
               icon[7,counter]=(i)*2+1+(j)*2*nnx+nnx -1
               icon[8,counter]=(i)*2+2+(j)*2*nnx+nnx -1
               counter += 1
           #end for
       #end for
       icon2 =np.zeros((4,4*nel),dtype=np.int32)
       counter = 0 
       for j in range(0,2*nely):
           for i in range(0,2*nelx):
               icon2[0,counter]=i+j*(2*nelx+1)
               icon2[1,counter]=i+1+j*(2*nelx+1)
               icon2[2,counter]=i+1+(j+1)*(2*nelx+1)
               icon2[3,counter]=i+(j+1)*(2*nelx+1)
               counter += 1



    #---------------------------------
    elif element=='Q3':
       N=(3*nelx+1)*(3*nely+1)
       nnx=3*nelx+1
       nny=3*nely+1
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0
       for j in range(0,nny):
           for i in range(0,nnx):
               x[counter]=i*hx/3
               y[counter]=j*hy/3
               counter += 1
           #end for
       #end for
       icon=np.zeros((16,nel),dtype=np.int32)
       counter=0
       for j in range(0,nely):
           for i in range(0,nelx):
               counter2=0
               for k in range(0,4):
                   for l in range(0,4):
                       icon[counter2,counter]=i*3+l+j*3*nnx+nnx*k
                       counter2+=1
               counter += 1 
       icon2 =np.zeros((4,9*nel),dtype=np.int32)
       counter = 0 
       for j in range(0,3*nely):
           for i in range(0,3*nelx):
               icon2[0,counter]=i+j*(3*nelx+1)
               icon2[1,counter]=i+1+j*(3*nelx+1)
               icon2[2,counter]=i+1+(j+1)*(3*nelx+1)
               icon2[3,counter]=i+(j+1)*(3*nelx+1)
               counter += 1

    #---------------------------------
    elif element=='Q4':
       N=(4*nelx+1)*(4*nely+1)
       nnx=4*nelx+1
       nny=4*nely+1
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0
       for j in range(0,nny):
           for i in range(0,nnx):
               x[counter]=i*hx/4
               y[counter]=j*hy/4
               counter += 1
           #end for
       #end for
       icon=np.zeros((25,nel),dtype=np.int32)
       counter=0
       for j in range(0,nely):
           for i in range(0,nelx):
               counter2=0
               for k in range(0,5):
                   for l in range(0,5):
                       icon[counter2,counter]=i*4+l+j*4*nnx+nnx*k
                       counter2+=1
               counter += 1 
       icon2 =np.zeros((4,16*nel),dtype=np.int32)
       counter = 0 
       for j in range(0,4*nely):
           for i in range(0,4*nelx):
               icon2[0,counter]=i+j*(4*nelx+1)
               icon2[1,counter]=i+1+j*(4*nelx+1)
               icon2[2,counter]=i+1+(j+1)*(4*nelx+1)
               icon2[3,counter]=i+(j+1)*(4*nelx+1)
               counter += 1



    #---------------------------------
    #
    # 3-------2
    # |\  C  /|
    # |  \ /  |
    # | D 4 B |
    # |  / \  |
    # |/  A  \|
    # 0-------1


    elif element=='P1':
       N=(nelx+1)*(nely+1)+nel
       nel*=4
       x = np.empty(N,dtype=np.float64) 
       y = np.empty(N,dtype=np.float64)
       counter = 0 
       for j in range(0,nely+1):
           for i in range(0,nelx+1):
               x[counter]=i*hx
               y[counter]=j*hy
               counter += 1
       for j in range(0,nely):
           for i in range(0,nelx):
               x[counter]=(i+0.5)*hx
               y[counter]=(j+0.5)*hy
               counter += 1
       icon =np.zeros((3,nel),dtype=np.int32)
       counter = 0 
       for j in range(0,nely):
           for i in range(0,nelx):
               inode0=i+j*(nelx+1)     
               inode1=i+1+j*(nelx+1)
               inode2=i+1+(j+1)*(nelx+1)
               inode3=i+(j+1)*(nelx+1)
               inode4=(nelx+1)*(nely+1)+nelx*j+i
               # triangle A
               icon[0,counter]=inode0
               icon[1,counter]=inode1
               icon[2,counter]=inode4
               counter += 1
               # triangle B
               icon[0,counter]=inode1
               icon[1,counter]=inode2
               icon[2,counter]=inode4
               counter += 1
               # triangle C
               icon[0,counter]=inode2
               icon[1,counter]=inode3
               icon[2,counter]=inode4
               counter += 1
               # triangle D
               icon[0,counter]=inode3
               icon[1,counter]=inode0
               icon[2,counter]=inode4
               counter += 1

       icon2 =np.zeros((3,nel),dtype=np.int32)
       icon2[:]=icon[:]

    else:
       exit("FEtools:cartesian_mesh: space unknown ")

    return N,nel,x,y,icon,icon2

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def export_mesh_to_ascii(x,y,filename):
    np.savetxt(filename,np.array([x,y]).T,header='# x,y')

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def export_connectivity_array_to_ascii(x,y,icon,filename):
    m,nel=np.shape(icon)
    iconfile=open(filename,"w")
    for iel in range (0,nel):
        iconfile.write('--------'+str(iel)+'-------\n')
        for k in range(0,m):
            iconfile.write("node "+str(k)+' | '+str(icon[k,iel])+" at pos. "+str(x[icon[k,iel]])+','+str(y[icon[k,iel]])+'\n')

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def export_mesh_to_vtu(x,y,icon,space,filename):
    N=np.size(x)
    m,nel=np.shape(icon)
    if m==3 or m==4: 
       vtufile=open(filename,"w")
       vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
       vtufile.write("<UnstructuredGrid> \n")
       vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(N,nel))
       #####
       vtufile.write("<Points> \n")
       vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'> \n")
       for i in range(0,N):
           vtufile.write("%10e %10e %10e \n" %(x[i],y[i],0.))
       vtufile.write("</DataArray>\n")
       vtufile.write("</Points> \n")
       #####
       vtufile.write("<Cells>\n")
       #--
       vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
       for iel in range (0,nel):
           if m==3:
              vtufile.write("%d %d %d \n" %(icon[0,iel],icon[1,iel],icon[2,iel]))
           if m==4:
              vtufile.write("%d %d %d %d \n" %(icon[0,iel],icon[1,iel],icon[2,iel],icon[3,iel]))
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
       for iel in range (0,nel):
           vtufile.write("%d \n" %((iel+1)*m))
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
       for iel in range (0,nel):
           if m==3:
              vtufile.write("%d \n" %5)
           else:
              vtufile.write("%d \n" %9)
       vtufile.write("</DataArray>\n")
       #--
       vtufile.write("</Cells>\n")
       #####
       vtufile.write("</Piece>\n")
       vtufile.write("</UnstructuredGrid>\n")
       vtufile.write("</VTKFile>\n")
       vtufile.close()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def export_swarm_to_vtu(x,y,filename):
       N=np.size(x)
       vtufile=open(filename,"w")
       vtufile.write("<VTKFile type='UnstructuredGrid' version='0.1' byte_order='BigEndian'> \n")
       vtufile.write("<UnstructuredGrid> \n")
       vtufile.write("<Piece NumberOfPoints=' %5d ' NumberOfCells=' %5d '> \n" %(N,N))
       #--
       vtufile.write("<Points> \n")
       vtufile.write("<DataArray type='Float32' NumberOfComponents='3' Format='ascii'>\n")
       for i in range(0,N):
           vtufile.write("%10e %10e %10e \n" %(x[i],y[i],0.))
       vtufile.write("</DataArray>\n")
       vtufile.write("</Points> \n")
       vtufile.write("<Cells>\n")
       vtufile.write("<DataArray type='Int32' Name='connectivity' Format='ascii'> \n")
       for i in range(0,N):
           vtufile.write("%d " % i)
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Int32' Name='offsets' Format='ascii'> \n")
       for i in range(0,N):
           vtufile.write("%d " % (i+1))
       vtufile.write("</DataArray>\n")
       vtufile.write("<DataArray type='Int32' Name='types' Format='ascii'>\n")
       for i in range(0,N):
           vtufile.write("%d " % 1)
       vtufile.write("</DataArray>\n")
       vtufile.write("</Cells>\n")
       vtufile.write("</Piece>\n")
       vtufile.write("</UnstructuredGrid>\n")
       vtufile.write("</VTKFile>\n")
       vtufile.close()

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def bc_setup(x,y,Lx,Ly,ndof,left,right,bottom,top):
    eps=1e-8
    N=np.size(x)
    Nfem=2*N
    bc_fix = np.zeros(Nfem, dtype=np.bool)     # boundary condition, yes/no
    bc_val = np.zeros(Nfem, dtype=np.float64)  # boundary condition, value
    for i in range(0,N):

        if x[i]/Lx<eps:
           if left=='free_slip':
              bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
           if left=='no_slip':
              bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
              bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.

        if x[i]/Lx>(1-eps):
           if right=='free_slip':
              bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
           if right=='no_slip':
              bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
              bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.

        if y[i]/Ly<eps:
           if bottom=='free_slip':
              bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.
           if bottom=='no_slip':
              bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
              bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.

        if y[i]/Ly>(1-eps):
           if top=='free_slip':
              bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.
           if top=='no_slip':
              bc_fix[i*ndof+0] = True ; bc_val[i*ndof+0] = 0.
              bc_fix[i*ndof+1] = True ; bc_val[i*ndof+1] = 0.

    return bc_fix,bc_val

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def J(m,dNdr,dNds,x,y):
    jcb = np.zeros((2,2),dtype=np.float64)
    jcb[0,0] = dNdr.dot(x)
    jcb[0,1] = dNdr.dot(y)
    jcb[1,0] = dNds.dot(x)
    jcb[1,1] = dNds.dot(y)
    jcbi=np.linalg.inv(jcb)
    jcob=np.linalg.det(jcb)
    dNdx= np.zeros(m,dtype=np.float64)
    dNdy= np.zeros(m,dtype=np.float64)
    dNdx[:]=jcbi[0,0]*dNdr[:]+jcbi[0,1]*dNds[:]
    dNdy[:]=jcbi[1,0]*dNdr[:]+jcbi[1,1]*dNds[:]
    return jcob,jcbi,dNdx,dNdy

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def assemble_K(K_el,A_sparse,iconV,mV,ndofV,iel):

    for k1 in range(0,mV):
        for i1 in range(0,ndofV):
            ikk=ndofV*k1+i1
            m1 =ndofV*iconV[k1,iel]+i1
            for k2 in range(0,mV):
                for i2 in range(0,ndofV):
                    jkk=ndofV*k2+i2
                    m2 =ndofV*iconV[k2,iel]+i2
                    A_sparse[m1,m2] += K_el[ikk,jkk]

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def assemble_G(G_el,A_sparse,iconV,iconP,NfemV,mV,mP,ndofV,ndofP,iel):

    for k1 in range(0,mV):
        for i1 in range(0,ndofV):
            ikk=ndofV*k1+i1
            m1 =ndofV*iconV[k1,iel]+i1
            for k2 in range(0,mP):
                m2 =iconP[k2,iel]
                A_sparse[m1,NfemV+m2]+=G_el[ikk,k2]
                A_sparse[NfemV+m2,m1]+=G_el[ikk,k2]

#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

def apply_bc(K_el,G_el,f_el,h_el,bc_val,bc_fix,iconV,mV,ndofV,iel):

    for k1 in range(0,mV):
        for i1 in range(0,ndofV):
            ikk=ndofV*k1+i1
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





