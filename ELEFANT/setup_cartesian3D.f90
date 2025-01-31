!==================================================================================================!
!==================================================================================================!
!                                                                                                  !
! ELEFANT                                                                        C. Thieulot       !
!                                                                                                  !
!==================================================================================================!
!==================================================================================================!

subroutine setup_cartesian3D

use module_parameters
use module_mesh
use module_constants 
use module_timing

implicit none

integer counter,ielx,iely,ielz,i,k,nnx,nny,nnz
real(8) hx,hy,hz

call system_clock(counti,count_rate)

!==================================================================================================!
!==================================================================================================!
!@@ \subsubsection{setup\_cartesian3D.f90}
!@@ This subroutine assigns to every element the coordinates of the its velocity, pressure,
!@@ and temperature nodes, the velocity, pressure and temperature connectivity arrays,
!@@ the coordinates of its center (xc,yc,zc), its integer coordinates (ielx,iely,ielz),
!@@ and its dimensions (hx,hy,hz).
!==================================================================================================!

if (iproc==0) then

hx=Lx/nelx
hy=Ly/nely
hz=Lz/nelz

allocate(mesh(nel))

counter=0    
do ielz=1,nelz    
   do iely=1,nely    
      do ielx=1,nelx    
         counter=counter+1    
         mesh(counter)%ielx=ielx
         mesh(counter)%iely=iely
         mesh(counter)%ielz=ielz
         mesh(counter)%hx=hx
         mesh(counter)%hy=hy
         mesh(counter)%hz=hz
         mesh(counter)%vol=hx*hy*hz
         if (ielx==1)    mesh(counter)%bnd1=.true.
         if (ielx==nelx) mesh(counter)%bnd2=.true.
         if (iely==1)    mesh(counter)%bnd3=.true.
         if (iely==nely) mesh(counter)%bnd4=.true.
         if (ielz==1)    mesh(counter)%bnd5=.true.
         if (ielz==nelz) mesh(counter)%bnd6=.true.
      end do    
   end do    
end do

!==========================================================
!velocity 

if (pair=='q1p0' .or. pair=='q1q1') then
   counter=0    
   do ielz=1,nelz    
      do iely=1,nely    
         do ielx=1,nelx    
            counter=counter+1    
            mesh(counter)%iconV(1)=(nelx+1)*(nely+1)*(ielz-1)+ (iely-1)*(nelx+1) + ielx
            mesh(counter)%iconV(2)=(nelx+1)*(nely+1)*(ielz-1)+ (iely-1)*(nelx+1) + ielx+1
            mesh(counter)%iconV(3)=(nelx+1)*(nely+1)*(ielz-1)+ (iely  )*(nelx+1) + ielx+1
            mesh(counter)%iconV(4)=(nelx+1)*(nely+1)*(ielz-1)+ (iely  )*(nelx+1) + ielx
            mesh(counter)%iconV(5)=(nelx+1)*(nely+1)*(ielz  )+ (iely-1)*(nelx+1) + ielx
            mesh(counter)%iconV(6)=(nelx+1)*(nely+1)*(ielz  )+ (iely-1)*(nelx+1) + ielx+1
            mesh(counter)%iconV(7)=(nelx+1)*(nely+1)*(ielz  )+ (iely  )*(nelx+1) + ielx+1
            mesh(counter)%iconV(8)=(nelx+1)*(nely+1)*(ielz  )+ (iely  )*(nelx+1) + ielx
            mesh(counter)%xV(1)=(ielx-1)*hx
            mesh(counter)%xV(2)=(ielx-1)*hx+hx
            mesh(counter)%xV(3)=(ielx-1)*hx+hx
            mesh(counter)%xV(4)=(ielx-1)*hx
            mesh(counter)%xV(5)=(ielx-1)*hx
            mesh(counter)%xV(6)=(ielx-1)*hx+hx
            mesh(counter)%xV(7)=(ielx-1)*hx+hx
            mesh(counter)%xV(8)=(ielx-1)*hx
            mesh(counter)%yV(1)=(iely-1)*hy
            mesh(counter)%yV(2)=(iely-1)*hy
            mesh(counter)%yV(3)=(iely-1)*hy+hy
            mesh(counter)%yV(4)=(iely-1)*hy+hy
            mesh(counter)%yV(5)=(iely-1)*hy
            mesh(counter)%yV(6)=(iely-1)*hy
            mesh(counter)%yV(7)=(iely-1)*hy+hy
            mesh(counter)%yV(8)=(iely-1)*hy+hy
            mesh(counter)%zV(1)=(ielz-1)*hz
            mesh(counter)%zV(2)=(ielz-1)*hz
            mesh(counter)%zV(3)=(ielz-1)*hz
            mesh(counter)%zV(4)=(ielz-1)*hz
            mesh(counter)%zV(5)=(ielz-1)*hz+hz
            mesh(counter)%zV(6)=(ielz-1)*hz+hz
            mesh(counter)%zV(7)=(ielz-1)*hz+hz
            mesh(counter)%zV(8)=(ielz-1)*hz+hz

            mesh(counter)%xL(1:mL)=mesh(counter)%xV(1:8)
            mesh(counter)%yL(1:mL)=mesh(counter)%yV(1:8)
            mesh(counter)%zL(1:mL)=mesh(counter)%zV(1:8)

            mesh(counter)%xc=(ielx-1)*hx+hx/2
            mesh(counter)%yc=(iely-1)*hy+hy/2
            mesh(counter)%zc=(ielz-1)*hz+hz/2
         end do    
      end do    
   end do    
end if

if (pair=='q1q1') then ! add bubble node
   do iel=1,nel
      mesh(iel)%xV(9)=mesh(iel)%xV(1)+hx/3
      mesh(iel)%yV(9)=mesh(iel)%yV(1)+hy/3
      mesh(iel)%zV(9)=mesh(iel)%zV(1)+hz/3
      mesh(counter)%iconV(9)=(nelx+1)*(nely+1)*(nelz+1)+2*(iel-1)+1
      mesh(iel)%xV(10)=mesh(iel)%xV(1)+2*hx/3
      mesh(iel)%yV(10)=mesh(iel)%yV(1)+2*hy/3
      mesh(iel)%zV(10)=mesh(iel)%zV(1)+2*hz/3
      mesh(counter)%iconV(10)=(nelx+1)*(nely+1)*(nelz+1)+2*(iel-1)+2
      !write(888,*) mesh(iel)%xV(9),mesh(iel)%yV(9),mesh(iel)%zV(9)
   end do
end if

if (pair=='q2q1') then
   nnx=2*nelx+1
   nny=2*nely+1
   nnz=2*nelz+1
   counter=0    
   do ielz=1,nelz    
      do iely=1,nely    
         do ielx=1,nelx    
            counter=counter+1    

            mesh(counter)%iconV(1)=(ielx-1)*2+1+(iely-1)*2*nnx                   + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(2)=(ielx-1)*2+2+(iely-1)*2*nnx                   + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(3)=(ielx-1)*2+3+(iely-1)*2*nnx                   + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(4)=(ielx-1)*2+1+(iely-1)*2*nnx+nnx               + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(5)=(ielx-1)*2+2+(iely-1)*2*nnx+nnx               + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(6)=(ielx-1)*2+3+(iely-1)*2*nnx+nnx               + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(7)=(ielx-1)*2+1+(iely-1)*2*nnx+nnx*2             + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(8)=(ielx-1)*2+2+(iely-1)*2*nnx+nnx*2             + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(9)=(ielx-1)*2+3+(iely-1)*2*nnx+nnx*2             + 2*nnx*nny*(ielz-1)
 
            mesh(counter)%iconV(10)=(ielx-1)*2+1+(iely-1)*2*nnx        + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(11)=(ielx-1)*2+2+(iely-1)*2*nnx        + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(12)=(ielx-1)*2+3+(iely-1)*2*nnx        + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(13)=(ielx-1)*2+1+(iely-1)*2*nnx+nnx    + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(14)=(ielx-1)*2+2+(iely-1)*2*nnx+nnx    + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(15)=(ielx-1)*2+3+(iely-1)*2*nnx+nnx    + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(16)=(ielx-1)*2+1+(iely-1)*2*nnx+nnx*2  + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(17)=(ielx-1)*2+2+(iely-1)*2*nnx+nnx*2  + nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(18)=(ielx-1)*2+3+(iely-1)*2*nnx+nnx*2  + nnx*nny + 2*nnx*nny*(ielz-1)

            mesh(counter)%iconV(19)=(ielx-1)*2+1+(iely-1)*2*nnx        + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(20)=(ielx-1)*2+2+(iely-1)*2*nnx        + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(21)=(ielx-1)*2+3+(iely-1)*2*nnx        + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(22)=(ielx-1)*2+1+(iely-1)*2*nnx+nnx    + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(23)=(ielx-1)*2+2+(iely-1)*2*nnx+nnx    + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(24)=(ielx-1)*2+3+(iely-1)*2*nnx+nnx    + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(25)=(ielx-1)*2+1+(iely-1)*2*nnx+nnx*2  + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(26)=(ielx-1)*2+2+(iely-1)*2*nnx+nnx*2  + 2*nnx*nny + 2*nnx*nny*(ielz-1)
            mesh(counter)%iconV(27)=(ielx-1)*2+3+(iely-1)*2*nnx+nnx*2  + 2*nnx*nny + 2*nnx*nny*(ielz-1)

            mesh(counter)%xV(01)=(ielx-1)*hx
            mesh(counter)%xV(02)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(03)=(ielx-1)*hx+hx
            mesh(counter)%xV(04)=(ielx-1)*hx
            mesh(counter)%xV(05)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(06)=(ielx-1)*hx+hx
            mesh(counter)%xV(07)=(ielx-1)*hx
            mesh(counter)%xV(08)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(09)=(ielx-1)*hx+hx

            mesh(counter)%xV(10)=(ielx-1)*hx
            mesh(counter)%xV(11)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(12)=(ielx-1)*hx+hx
            mesh(counter)%xV(13)=(ielx-1)*hx
            mesh(counter)%xV(14)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(15)=(ielx-1)*hx+hx
            mesh(counter)%xV(16)=(ielx-1)*hx
            mesh(counter)%xV(17)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(18)=(ielx-1)*hx+hx

            mesh(counter)%xV(19)=(ielx-1)*hx
            mesh(counter)%xV(20)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(21)=(ielx-1)*hx+hx
            mesh(counter)%xV(22)=(ielx-1)*hx
            mesh(counter)%xV(23)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(24)=(ielx-1)*hx+hx
            mesh(counter)%xV(25)=(ielx-1)*hx
            mesh(counter)%xV(26)=(ielx-1)*hx+hx/2d0
            mesh(counter)%xV(27)=(ielx-1)*hx+hx

            mesh(counter)%yV(01)=(iely-1)*hy
            mesh(counter)%yV(02)=(iely-1)*hy
            mesh(counter)%yV(03)=(iely-1)*hy
            mesh(counter)%yV(04)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(05)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(06)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(07)=(iely-1)*hy+hy
            mesh(counter)%yV(08)=(iely-1)*hy+hy
            mesh(counter)%yV(09)=(iely-1)*hy+hy

            mesh(counter)%yV(10)=(iely-1)*hy
            mesh(counter)%yV(11)=(iely-1)*hy
            mesh(counter)%yV(12)=(iely-1)*hy
            mesh(counter)%yV(13)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(14)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(15)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(16)=(iely-1)*hy+hy
            mesh(counter)%yV(17)=(iely-1)*hy+hy
            mesh(counter)%yV(18)=(iely-1)*hy+hy

            mesh(counter)%yV(19)=(iely-1)*hy
            mesh(counter)%yV(20)=(iely-1)*hy
            mesh(counter)%yV(21)=(iely-1)*hy
            mesh(counter)%yV(22)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(23)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(24)=(iely-1)*hy+hy/2d0
            mesh(counter)%yV(25)=(iely-1)*hy+hy
            mesh(counter)%yV(26)=(iely-1)*hy+hy
            mesh(counter)%yV(27)=(iely-1)*hy+hy

            mesh(counter)%zV(01)=(ielz-1)*hz
            mesh(counter)%zV(02)=(ielz-1)*hz
            mesh(counter)%zV(03)=(ielz-1)*hz
            mesh(counter)%zV(04)=(ielz-1)*hz
            mesh(counter)%zV(05)=(ielz-1)*hz
            mesh(counter)%zV(06)=(ielz-1)*hz
            mesh(counter)%zV(07)=(ielz-1)*hz
            mesh(counter)%zV(08)=(ielz-1)*hz
            mesh(counter)%zV(09)=(ielz-1)*hz

            mesh(counter)%zV(10)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(11)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(12)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(13)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(14)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(15)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(16)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(17)=(ielz-1)*hz+hz/2d0
            mesh(counter)%zV(18)=(ielz-1)*hz+hz/2d0

            mesh(counter)%zV(19)=(ielz-1)*hz+hz
            mesh(counter)%zV(20)=(ielz-1)*hz+hz
            mesh(counter)%zV(21)=(ielz-1)*hz+hz
            mesh(counter)%zV(22)=(ielz-1)*hz+hz
            mesh(counter)%zV(23)=(ielz-1)*hz+hz
            mesh(counter)%zV(24)=(ielz-1)*hz+hz
            mesh(counter)%zV(25)=(ielz-1)*hz+hz
            mesh(counter)%zV(26)=(ielz-1)*hz+hz
            mesh(counter)%zV(27)=(ielz-1)*hz+hz

         end do
      end do
   end do
end if

!==========================================================
! pressure 

if (pair=='q1p0') then
   counter=0    
   do ielz=1,nelz
      do iely=1,nely    
         do ielx=1,nelx    
            counter=counter+1    
            mesh(counter)%iconP(1)=counter
            mesh(counter)%xP(1)=mesh(counter)%xC
            mesh(counter)%yP(1)=mesh(counter)%yC
            mesh(counter)%zP(1)=mesh(counter)%zC
         end do    
      end do    
   end do    
end if

if (pair=='q1q1') then
   do i=1,mP
      mesh(1:nel)%xP(i)=mesh(1:nel)%xV(i)
      mesh(1:nel)%yP(i)=mesh(1:nel)%yV(i)
      mesh(1:nel)%zP(i)=mesh(1:nel)%zV(i)
      mesh(1:nel)%iconP(i)=mesh(1:nel)%iconV(i)
   end do
end if

if (pair=='q2q1') then
   counter=0    
   do ielz=1,nelz    
      do iely=1,nely    
         do ielx=1,nelx    
            counter=counter+1    

            mesh(counter)%iconP(1)=(nelx+1)*(nely+1)*(ielz-1)+ (iely-1)*(nelx+1) + ielx
            mesh(counter)%iconP(2)=(nelx+1)*(nely+1)*(ielz-1)+ (iely-1)*(nelx+1) + ielx+1
            mesh(counter)%iconP(3)=(nelx+1)*(nely+1)*(ielz-1)+ (iely  )*(nelx+1) + ielx+1
            mesh(counter)%iconP(4)=(nelx+1)*(nely+1)*(ielz-1)+ (iely  )*(nelx+1) + ielx
            mesh(counter)%iconP(5)=(nelx+1)*(nely+1)*(ielz  )+ (iely-1)*(nelx+1) + ielx
            mesh(counter)%iconP(6)=(nelx+1)*(nely+1)*(ielz  )+ (iely-1)*(nelx+1) + ielx+1
            mesh(counter)%iconP(7)=(nelx+1)*(nely+1)*(ielz  )+ (iely  )*(nelx+1) + ielx+1
            mesh(counter)%iconP(8)=(nelx+1)*(nely+1)*(ielz  )+ (iely  )*(nelx+1) + ielx

            mesh(counter)%xP(1)=(ielx-1)*hx
            mesh(counter)%xP(2)=(ielx-1)*hx+hx
            mesh(counter)%xP(3)=(ielx-1)*hx+hx
            mesh(counter)%xP(4)=(ielx-1)*hx
            mesh(counter)%xP(5)=(ielx-1)*hx
            mesh(counter)%xP(6)=(ielx-1)*hx+hx
            mesh(counter)%xP(7)=(ielx-1)*hx+hx
            mesh(counter)%xP(8)=(ielx-1)*hx

            mesh(counter)%yP(1)=(iely-1)*hy
            mesh(counter)%yP(2)=(iely-1)*hy
            mesh(counter)%yP(3)=(iely-1)*hy+hy
            mesh(counter)%yP(4)=(iely-1)*hy+hy
            mesh(counter)%yP(5)=(iely-1)*hy
            mesh(counter)%yP(6)=(iely-1)*hy
            mesh(counter)%yP(7)=(iely-1)*hy+hy
            mesh(counter)%yP(8)=(iely-1)*hy+hy

            mesh(counter)%zP(1)=(ielz-1)*hz
            mesh(counter)%zP(2)=(ielz-1)*hz
            mesh(counter)%zP(3)=(ielz-1)*hz
            mesh(counter)%zP(4)=(ielz-1)*hz
            mesh(counter)%zP(5)=(ielz-1)*hz+hz
            mesh(counter)%zP(6)=(ielz-1)*hz+hz
            mesh(counter)%zP(7)=(ielz-1)*hz+hz
            mesh(counter)%zP(8)=(ielz-1)*hz+hz
         end do
      end do
   end do
end if


!==========================================================
! temperature 

do k=1,mT
   mesh(1:nel)%xT(k)=mesh(1:nel)%xV(k)
   mesh(1:nel)%yT(k)=mesh(1:nel)%yV(k)
   mesh(1:nel)%zT(k)=mesh(1:nel)%zV(k)
   mesh(1:nel)%iconT(k)=mesh(1:nel)%iconV(k)
end do

!==========================================================
! flag nodes on boundaries

do iel=1,nel
   do i=1,ncorners
      mesh(iel)%bnd1_node(i)=(abs(mesh(iel)%xV(i)-0 )<eps*Lx)
      mesh(iel)%bnd2_node(i)=(abs(mesh(iel)%xV(i)-Lx)<eps*Lx)
      mesh(iel)%bnd3_node(i)=(abs(mesh(iel)%yV(i)-0 )<eps*Ly)
      mesh(iel)%bnd4_node(i)=(abs(mesh(iel)%yV(i)-Ly)<eps*Ly)
      mesh(iel)%bnd5_node(i)=(abs(mesh(iel)%zV(i)-0 )<eps*Lz)
      mesh(iel)%bnd6_node(i)=(abs(mesh(iel)%zV(i)-Lz)<eps*Lz)
   end do
end do

!==========================================================
! initialise boundary arrays

do iel=1,nel
   mesh(iel)%fix_u=.false.
   mesh(iel)%fix_v=.false.
   mesh(iel)%fix_w=.false.
   mesh(iel)%fix_T=.false.
end do

if (debug) then
   do iel=1,nel
   print *,'--------------------------------------------------'
   print *,'elt:',iel,' | iconV',mesh(iel)%iconV(1:mV),' | iconP',mesh(iel)%iconP(1:mP)
   do k=1,mV
      write(777,*) mesh(iel)%xV(k),mesh(iel)%yV(k),mesh(iel)%zV(k)
   end do
   end do
end if

!==============================================================================!

call system_clock(countf) ; elapsed=dble(countf-counti)/dble(count_rate)

write(*,'(a,f6.2,a)') '     >> setup_cartesian3D                ',elapsed,' s'

end if ! iproc

end subroutine

!==================================================================================================!
!==================================================================================================!
