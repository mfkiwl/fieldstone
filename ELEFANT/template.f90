!==================================================================================================!
!==================================================================================================!
!                                                                                                  !
! ELEFANT                                                                        C. Thieulot       !
!                                                                                                  !
!==================================================================================================!
!==================================================================================================!

subroutine name

!use global_parameters
!use structures
!use constants

implicit none


!==================================================================================================!
!==================================================================================================!
!@@ \subsection{template}
!@@
!==================================================================================================!

if (iproc==0) then

call system_clock(counti,count_rate)

!==============================================================================!











!==============================================================================!

call system_clock(countf) ; elapsed=dble(countf-counti)/dble(count_rate)

if (iproc==0) write(*,*) '     -> name ',elapsed

end if ! iproc

end subroutine

!==================================================================================================!
!==================================================================================================!
