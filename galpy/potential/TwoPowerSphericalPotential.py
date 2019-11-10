###############################################################################
#   TwoPowerSphericalPotential.py: General class for potentials derived from 
#                                  densities with two power-laws
#
#                                                    amp
#                             rho(r)= ------------------------------------
#                                      (r/a)^\alpha (1+r/a)^(\beta-\alpha)
###############################################################################
import math as m
import numpy
from numpy import sqrt, pi
from scipy import optimize, integrate
from scipy.special import gamma as Gamma, hyp2f1
from galpy.util import bovy_conversion
from .Potential import Potential, kms_to_kpcGyrDecorator, _APY_LOADED
if _APY_LOADED:
    from astropy import units

class TwoPowerSphericalPotential(Potential):
    """Class that implements spherical potentials that are derived from 
    two-power density models

    .. math::

        \\rho(r) = \\frac{\\mathrm{amp}}{4\\,\\pi\\,a^3}\\,\\frac{1}{(r/a)^\\alpha\\,(1+r/a)^{\\beta-\\alpha}}
    """
    def __init__(self,amp=1.,a=5.,alpha=1.5,beta=3.5,
                 normalize=False,ro=None,vo=None):
        """
        NAME:

           __init__

        PURPOSE:

           initialize a two-power-density potential

        INPUT:

           amp - amplitude to be applied to the potential (default: 1); can be a Quantity with units of mass or Gxmass

           a - scale radius (can be Quantity)

           alpha - inner power

           beta - outer power

           normalize - if True, normalize such that vc(1.,0.)=1., or, if given as a number, such that the force is this fraction of the force necessary to make vc(1.,0.)=1.

           ro=, vo= distance and velocity scales for translation into internal units (default from configuration file)

        OUTPUT:

           (none)

        HISTORY:

           2010-07-09 - Started - Bovy (NYU)
           2019-10-20 - Updated - Starkman (UofT)

        """
        # instantiate
        super(TwoPowerSphericalPotential, self).__init__(amp=amp,ro=ro,vo=vo,amp_units='mass')
        # integerSelf
        if ((self.__class__ == TwoPowerSphericalPotential) &
            (alpha == round(alpha)) & (beta == round(beta))):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=a,alpha=round(alpha),beta=round(beta),
                normalize=False,ro=None,vo=None)
        else:
            self.integerSelf= None
        # correcting quantities
        if _APY_LOADED and isinstance(a,units.Quantity):
            a= a.to_value(units.kpc)/self._ro
        # setting properties
        self.a= a
        self._scale= self.a
        self._alpha= alpha
        self._beta= beta
        # normalizing
        if normalize or \
                (isinstance(normalize,(int,float)) \
                     and not isinstance(normalize,bool)): #pragma: no cover
            self.normalize(normalize)
        return None

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, alpha):
        # checking if alpha allowed to change
        self._alpha = alpha  # setting alpha
        # update .integerSelf
        if alpha == round(alpha) and self._beta == round(self._beta):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=self.a,alpha=round(alpha),beta=round(self._beta),
                normalize=False)
        else:
            self.integerSelf= None

    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self, beta):
        self._beta = beta  # setting alpha
        # update .integerSelf
        if self._alpha == round(self._alpha) and beta == round(beta):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=self.a,alpha=round(self._alpha),beta=round(beta),
                normalize=False)
        else:
            self.integerSelf= None

    def _evaluate(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
        """
        NAME:
           _evaluate
        PURPOSE:
           evaluate the potential at R,z
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           Phi(R,z)
        HISTORY:
           2010-07-09 - Started - Bovy (NYU)
        """
        if not _forceFloatEval and self.integerSelf is not None:
            return self.integerSelf._evaluate(R,z,phi=phi,t=t)
        elif self.beta == 3.:
            a, alpha, beta = self.a, self.alpha, self.beta
            r= sqrt(R**2.+z**2.)
            return (1./a)\
                *(r-a*(r/a)**(3.-alpha)/(3.-alpha)\
                      *hyp2f1(3.-alpha, 2.-alpha, 4.-alpha, -r/a))/(alpha-2.)/r
        # else:
        a, alpha, beta = self.a, self._alpha, self._beta
        r= sqrt(R**2.+z**2.)
        return Gamma(beta-3.)\
            *((r/a)**(3.-beta)/Gamma(beta-1.)\
                  *hyp2f1(beta-3., beta-alpha, beta-1., -a/r)
              -Gamma(3.-alpha)/Gamma(beta-alpha))/r

    def _Rforce(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
        """
        NAME:
           _Rforce
        PURPOSE:
           evaluate the radial force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the radial force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        if not _forceFloatEval and self.integerSelf is not None:
            return self.integerSelf._Rforce(R,z,phi=phi,t=t)
        # else:
        a, alpha, beta = self.a, self._alpha, self._beta
        r= sqrt(R**2.+z**2.)
        return -R/r**alpha*a**(alpha-3.)/(3.-alpha)\
            *hyp2f1(3.-alpha, beta-alpha, 4.-alpha, -r/a)

    def _zforce(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
        """
        NAME:
           _zforce
        PURPOSE:
           evaluate the vertical force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the vertical force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        if not _forceFloatEval and self.integerSelf is not None:
            return self.integerSelf._zforce(R,z,phi=phi,t=t)
        # else:
        a, alpha, beta = self.a, self._alpha, self._beta
        r= sqrt(R**2.+z**2.)
        return -z/r**alpha*a**(alpha-3.)/(3.-alpha)\
            *hyp2f1(3.-alpha, beta-alpha, 4.-alpha, -r/a)

    # def _R2deriv(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
    #     """
    #     NAME:
    #         _R2deriv
    #     PURPOSE:
    #         evaluate the second radial derivative for this potential
    #     INPUT:
    #         R - Galactocentric cylindrical radius
    #         z - vertical height
    #         phi - azimuth
    #         t- time
    #     OUTPUT:
    #         the second radial derivative
    #     HISTORY:
    #         2019-10-20 - Written - Starkman (UofT)
    #     """
    #     if not _forceFloatEval and self.integerSelf is not None:
    #         return self.integerSelf._R2deriv(R,z,phi=phi,t=t)
    #     # else:
    #     a, alpha, beta = self.a, self.alpha, self.beta
    #     r= sqrt(R**2.+z**2.)

    #     if beta == 3.:
    #         # Need to have derivatives of hyp2f1
    #         raise ValueError('Not yet implemented')

    #     if beta == 5.:
    #         # Need to have derivatives of hyp2f1
    #         raise ValueError('Not yet implemented')

    #     return (Gamma(beta - 3) / r**5 *
    #             (((z**2 - 2 * R**2) * Gamma(3 - alpha)) / Gamma(beta - alpha) +
    #              a**(-3 + beta) * (R**2 + z**2)**(1 - beta / 2.) *
    #              ((z**2 * (a * (alpha - beta) - r * (beta - 2)) +
    #                R**2 * (r * (beta - 2) *
    #                        (beta - 1) + 2 * a * (beta - alpha))
    #                ) * hyp2f1(-2 + beta, beta - alpha + 1, beta,
    #                           -(a / r)) / Gamma(beta) +
    #               (a * (R**2 * (2 + alpha * (-3 + beta)) - z**2 * (beta - 2)) +
    #                r * (-z**2 + R**2 * (beta - 1)) * (beta - 2)) *
    #               (-2 + beta) * hyp2f1(beta - 1, beta - alpha + 1, beta,
    #                                    -(a / r)) / Gamma(beta))))

    def _z2deriv(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
        """
        NAME:
           _z2deriv
        PURPOSE:
           evaluate the second vertical derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           the second vertical derivative
        HISTORY:
           2012-07-26 - Written - Bovy (IAS@MPIA)
           2019-10-20 - Edited - Starkman (UofT)
        """
        return self._R2deriv(numpy.fabs(z),R,phi=phi,t=t,
                             _forceFloatEval=_forceFloatEval) #Spherical potential


    # def _Rzderiv(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
    #     """
    #     NAME:
    #        _Rzderiv
    #     PURPOSE:
    #        evaluate the mixed R,z derivative for this potential
    #     INPUT:
    #        R - Galactocentric cylindrical radius
    #        z - vertical height
    #        phi - azimuth
    #        t - time
    #     OUTPUT:
    #        d2phi/dR/dz
    #     HISTORY:
    #        2019-10-20 - Written - Starkman (UofT)
    #     """
    #     if not _forceFloatEval and self.integerSelf is not None:
    #         return self.integerSelf._Rzderiv(R,z,phi=phi,t=t)
    #     # else:
    #     a, alpha, beta = self.a, self.alpha, self.beta
    #     r= sqrt(R**2.+z**2.)

    #     if beta == 3.:
    #         # Need to have derivatives of hyp2f1
    #         raise ValueError('Not yet implemented')

    #     if beta == 5.:
    #         # Need to have derivatives of hyp2f1
    #         raise ValueError('Not yet implemented')

    #     return (R * z * Gamma(beta - 3) / r**5 *
    #             ((-3 * Gamma(3 - alpha)) / Gamma(beta - alpha) +
    #              a**(beta - 3) * r**(2 - beta) *
    #              ((r * (beta - 2) * beta + 3 * a * (-alpha + beta)) *
    #               hyp2f1(beta - 2, beta - alpha + 1, beta,
    #                      -(a / r)) / Gamma(beta) +
    #               (-2 + beta) * (r * (-2 + beta) * beta +
    #                              a * (alpha * (-3 + beta) + beta)) *
    #               hyp2f1(beta - 1, beta - alpha + 1, beta,
    #                      -(a / r)) / Gamma(beta))))


    def _dens(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _dens
        PURPOSE:
           evaluate the density for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the density
        HISTORY:
           2010-08-08 - Written - Bovy (NYU)
        """
        a, alpha, beta = self.a, self._alpha, self._beta
        r= sqrt(R**2.+z**2.)
        return (a/r)**alpha/(1.+r/a)**(beta-alpha)/4./m.pi/a**3.

    def _mass(self,R,z=0.,t=0.):
        """
        NAME:
           _mass
        PURPOSE:
           evaluate the mass within R for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           t - time
        OUTPUT:
           the mass enclosed
        HISTORY:
           2014-04-01 - Written - Erkal (IoA)
        """
        a, alpha, beta = self.a, self._alpha, self._beta
        r= R if z is None else sqrt(R**2.+z**2.)
        # if z is None:
        #     r= R
        # else:
        #     r= sqrt(R**2.+z**2.)
        return (r/a)**(3.-alpha)/(3.-alpha)*hyp2f1(3.-alpha,-alpha+beta,4.-alpha,-r/a)


class DehnenSphericalPotential(TwoPowerSphericalPotential):
    """Class that implements the Dehnen Spherical Potential from Dehnen 1993

    .. math::

          \\rho(r) = \\frac{\\mathrm{amp}(3-\\alpha)}{4\\,\\pi\\,a^3}\\,\\frac{1}{(r/a)^{\\alpha}\\,(1+r/a)^{4-\\alpha}}
    """
    def __init__(self,amp=1.,a=1.,alpha=1.5,dehnen_amp=False,
                 normalize=False,ro=None,vo=None):
        """
        NAME:

           __init__

        PURPOSE:

           initialize a Dehnen Spherical Potential

        INPUT:

           amp - amplitude to be applied to the potential (default: 1); can be a Quantity with units of mass or Gxmass will be rescaled to amp*(3-alpha) (except for Jaffe, which is already scaled)

           a - scale radius (can be Quantity)

           alpha - inner power, restricted to [0, 3)

           dehnen_amp - if True, use dehnen normalization, amp -> amp * (3 - alpha)

           normalize - if True, normalize such that vc(1.,0.)=1., or, if given as a number, such that the force is this fraction of the force necessary to make vc(1.,0.)=1.

           ro=, vo= distance and velocity scales for translation into internal units (default from configuration file)

        OUTPUT:

           (none)

        HISTORY:

           2019-10-07 - Started - Starkman (UofT)

        """
        # instantiate
        if dehnen_amp:
            amp= amp*(3-alpha)  # difference between bovy and Dehnen implementation
        super(DehnenSphericalPotential, self).__init__(
            amp=amp,a=a,alpha=alpha,beta=4,
            normalize=normalize,ro=ro,vo=vo
        )
        if ((self.__class__ == DehnenSphericalPotential) &
            (alpha == round(alpha))):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=a,alpha=round(alpha),beta=4,
                normalize=False,ro=None,vo=None)
        else:
            self.integerSelf= None
        # set properties
        self.hasC= True
        self.hasC_dxdv= True
        self._nemo_accname= 'Dehnen'
        return None

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, alpha):
        # checking if alpha allowed to change
        self._alpha = alpha  # setting alpha
        # checking if should update .integerSelf
        if alpha == round(alpha):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=self.a,alpha=round(alpha),beta=4,
                normalize=False,)
        else:
            self.integerSelf= None

    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self, value):
        raise Exception('cannot modify beta')

    def _R2deriv(self,R,z,phi=0.,t=0.,_forceFloatEval=False):
        """
        NAME:
           _R2deriv
        PURPOSE:
           evaluate the second radial derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           the second radial derivative
        HISTORY:
           2019-10-11 - Written - Starkman (UofT)
        """
        if not _forceFloatEval and self.integerSelf is not None:
            return self.integerSelf._R2deriv(self, R, z, phi=phi, t=t)
        # else:
        a, alpha = self.a, self._alpha
        r = sqrt(R**2. + z**2.)

        return (((1 + a / r)**alpha *
                 (2 * R**4 - z**2 * (z**2 + a * r) +
                  R**2 * (z**2 + a * r * (-1 + alpha)))) /
                (r**3 * (a + r)**4 * (-3 + alpha)))

    def _z2deriv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _z2deriv
        PURPOSE:
           evaluate the second vertical derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           the second vertical derivative
        HISTORY:
           2019-10-20 - Written - Starkman (UofT)
        """
        a, alpha = self.a, self._alpha
        r = sqrt(R**2. + z**2.)
        return (((1 + a / r)**alpha *
                 (R**4 - 2 * z**4 + R**2 * (-z**2 + a * r) -
                  a * z**2 * r * (-1 + alpha))) /
                (r**3 * (a + r)**4 * (3 - alpha)))

    def _Rzderiv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rzderiv
        PURPOSE:
           evaluate the mixed R,z derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           d2phi/dR/dz
        HISTORY:
           2019-10-11 - Written - Starkman (UofT)
        """
        if self.integerSelf is not None:
            return self.integerSelf._Rzderiv(self, R, z, phi=phi, t=t)
        # else:
        a, alpha= self.a, self._alpha
        r= sqrt(R**2.+z**2.)
        p= R * z * (1 + a / r)**alpha * (3 * r**2 + a * alpha * r)
        q= r**3. * (a + r)**4. * (alpha - 3)
        return p / q


class TwoPowerIntegerSphericalPotential(TwoPowerSphericalPotential):
    """Class that implements the two-power-density spherical potentials in 
    the case of integer powers"""
    def __init__(self,amp=1.,a=1.,alpha=1,beta=3,
                 normalize=False,ro=None,vo=None):
        """
        NAME:

           __init__

        PURPOSE:

           initialize a two-power-density potential for integer powers

        INPUT:

           amp - amplitude to be applied to the potential (default: 1); can be a Quantity with units of mass or Gxmass

           a - scale radius (can be Quantity)

           alpha - inner power (default: NFW)

           beta - outer power (default: NFW)

           normalize - if True, normalize such that vc(1.,0.)=1., or, if 
                       given as a number, such that the force is this fraction 
                       of the force necessary to make vc(1.,0.)=1.

           ro=, vo= distance and velocity scales for translation into internal units (default from configuration file)

        OUTPUT:

           (none)

        HISTORY:

           2010-07-09 - Started - Bovy (NYU)
        """
        Potential.__init__(self, amp=amp,ro=ro,vo=vo,amp_units='mass')

        # integerSelf
        if alpha == 1 and beta == 4:
            self.integerSelf= HernquistPotential(amp=1.,a=a,normalize=False)
        elif alpha == 2 and beta == 4:
            self.integerSelf= JaffePotential(amp=1.,a=a,normalize=False)
        elif alpha == 1 and beta == 3:
            self.integerSelf= NFWPotential(amp=1.,a=a,normalize=False)
        else:
            self.integerSelf= None
        # astropy
        if _APY_LOADED and isinstance(a,units.Quantity):
            a= a.to(units.kpc).value/self._ro
        # setting properties
        self.a= a
        self._scale= self.a
        self._alpha= alpha
        self._beta= beta
        # normalizing
        if normalize or \
                (isinstance(normalize,(int,float)) \
                     and not isinstance(normalize,bool)): #pragma: no cover
            self.normalize(normalize)
        return None

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self,alpha):
        # checking if alpha is an integer
        if alpha != int(alpha):
            raise ValueError('alpha must be an integer')
        self._alpha= int(alpha)  # setting alpha
        # update .integerSelf
        if alpha == int(alpha) and self._beta == int(self._beta):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=self.a,alpha=int(alpha),beta=int(self._beta),
                normalize=False)
        else:
            self.integerSelf= None


    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self,beta):
        # checking if beta is an integer
        if beta != int(beta):
            raise ValueError('beta must be an integer')
        self._beta= int(beta)  # setting alpha
        # update .integerSelf
        if self._alpha == int(self._alpha) and beta == int(beta):
            self.integerSelf= TwoPowerIntegerSphericalPotential(
                amp=1.,a=self.a,alpha=int(self._alpha),beta=int(beta),
                normalize=False)
        else:
            self.integerSelf= None

    def _evaluate(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _evaluate
        PURPOSE:
           evaluate the potential at R,z
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           Phi(R,z)
        HISTORY:
           2010-07-09 - Started - Bovy (NYU)
        """
        if self.integerSelf is not None:
            return self.integerSelf._evaluate(R,z,phi=phi,t=t)
        else:
            return super(TwoPowerIntegerSphericalPotential, self)._evaluate(
                R,z, phi=phi,t=t, _forceFloatEval=True)

    def _Rforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rforce
        PURPOSE:
           evaluate the radial force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the radial force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        if self.integerSelf is not None:
            return self.integerSelf._Rforce(R,z,phi=phi,t=t)
        else:
            return super(TwoPowerIntegerSphericalPotential, self)._Rforce(
                R,z,phi=phi,t=t,_forceFloatEval=True)

    def _zforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _zforce
        PURPOSE:
           evaluate the vertical force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the vertical force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        if self.integerSelf is not None:
            return self.integerSelf._zforce(R,z,phi=phi,t=t)
        else:
            return super(TwoPowerIntegerSphericalPotential, self)._zforce(
                R,z,phi=phi,t=t,_forceFloatEval=True)

    def _R2deriv(self,R,z,phi=0.,t=0.):
        """
        NAME:
            _R2deriv
        PURPOSE:
            evaluate the second radial derivative for this potential
        INPUT:
            R - Galactocentric cylindrical radius
            z - vertical height
            phi - azimuth
            t- time
        OUTPUT:
            the second radial derivative
        HISTORY:
            2019-10-20 - Written - Starkman (UofT)
        """
        if self.integerSelf is not None:
            return self.integerSelf._R2deriv(R,z,phi=phi,t=t)
        # else:
        a, alpha, beta = self.a, self.alpha, self.beta
        r= sqrt(R**2.+z**2.)

        return (Gamma(beta - 3) / r**5 *
                (((z**2 - 2 * R**2) * Gamma(3 - alpha)) / Gamma(beta - alpha) +
                 a**(-3 + beta) * (R**2 + z**2)**(1 - beta / 2.) *
                 ((z**2 * (a * (alpha - beta) - r * (beta - 2)) +
                   R**2 * (r * (beta - 2) *
                           (beta - 1) + 2 * a * (beta - alpha))
                   ) * hyp2f1(-2 + beta, beta - alpha + 1, beta,
                              -(a / r)) / Gamma(beta) +
                  (a * (R**2 * (2 + alpha * (-3 + beta)) - z**2 * (beta - 2)) +
                   r * (-z**2 + R**2 * (beta - 1)) * (beta - 2)) *
                  (-2 + beta) * hyp2f1(beta - 1, beta - alpha + 1, beta,
                                       -(a / r)) / Gamma(beta))))


class HernquistPotential(DehnenSphericalPotential):
    """Class that implements the Hernquist potential

    .. math::

        \\rho(r) = \\frac{\\mathrm{amp}}{4\\,\\pi\\,a^3}\\,\\frac{1}{(r/a)\\,(1+r/a)^{3}}

    """
    def __init__(self,amp=1.,a=1.,dehnen_amp=False,normalize=False,ro=None,vo=None):
        """
        NAME:

           __init__

        PURPOSE:

           Initialize a Hernquist potential

        INPUT:

           amp - amplitude to be applied to the potential (default: 1); can be a Quantity with units of mass or Gxmass

           a - scale radius (can be Quantity)

           dehnen_amp - if True, use dehnen normalization, amp -> amp * (3 - alpha)

           normalize - if True, normalize such that vc(1.,0.)=1., or, if given as a number, such that the force is this fraction of the force necessary to make vc(1.,0.)=1.

           ro=, vo= distance and velocity scales for translation into internal units (default from configuration file)

        OUTPUT:

           (none)

        HISTORY:

           2010-07-09 - Written - Bovy (NYU)

        """
        super(HernquistPotential, self).__init__(
            amp=amp,a=a,alpha=1,dehnen_amp=dehnen_amp,
            normalize=normalize,ro=ro,vo=vo)
        self.hasC= True
        self.hasC_dxdv= True
        self._nemo_accname= 'Dehnen'
        return None

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, value):
        raise Exception('cannot modify alpha')

    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self, value):
        raise Exception('cannot modify beta')

    def _evaluate(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _evaluate
        PURPOSE:
           evaluate the potential at R,z
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           Phi(R,z)
        HISTORY:
           2010-07-09 - Started - Bovy (NYU)
        """
        a= self.a
        return -1./(1.+sqrt(R**2.+z**2.)/a)/2./a

    def _Rforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rforce
        PURPOSE:
           evaluate the radial force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           the radial force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        a= self.a
        r= sqrt(R**2.+z**2.)
        return -R/a/r/(1.+r/a)**2./2./a

    def _zforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _zforce
        PURPOSE:
           evaluate the vertical force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           t - time
        OUTPUT:
           the vertical force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        a= self.a
        r= sqrt(R**2.+z**2.)
        return -z/a/r/(1.+r/a)**2./2./a

    def _R2deriv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _R2deriv
        PURPOSE:
           evaluate the second radial derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           the second radial derivative
        HISTORY:
           2011-10-09 - Written - Bovy (IAS)
        """
        a= self.a
        r= sqrt(R**2.+z**2.)
        return (a*z**2.+(z**2.-2.*R**2.)*r)/r**3.\
            /(a+r)**3./2.

    def _Rzderiv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rzderiv
        PURPOSE:
           evaluate the mixed R,z derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t- time
        OUTPUT:
           d2phi/dR/dz
        HISTORY:
           2013-08-28 - Written - Bovy (IAS)
        """
        a= self.a
        r= sqrt(R**2.+z**2.)
        return -R*z*(a+3.*r)*(r*(a+r))**-3./2.

    def _surfdens(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _surfdens
        PURPOSE:
           evaluate the surface density for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the surface density
        HISTORY:
           2018-08-19 - Written - Bovy (UofT)
        """
        a= self.a
        r= sqrt(R**2.+z**2.)
        Rma= sqrt(R**2.-a**2.+0j)
        if Rma == 0.:
            return (-12.*a**3-5.*a*z**2
                      +sqrt(1.+z**2/a**2)\
                         *(12.*a**3-a*z**2+2/a*z**4))\
                          /30./pi*z**-5.
        else:
            return a*((2.*a**2.+R**2.)*Rma**-5\
                               *(numpy.arctan(z/Rma)-numpy.arctan(a*z/r/Rma))
                           +z*(5.*a**3.*r-4.*a**4
                               +a**2*(2.*r**2.+R**2)
                               -a*r*(5.*R**2.+3.*z**2.)+R**2.*r**2.)
                           /(a**2.-R**2.)**2.
                           /(r**2-a**2.)**2.).real/4./pi

    def _mass(self,R,z=0.,t=0.):
        """
        NAME:
           _mass
        PURPOSE:
           calculate the mass out to a given radius
        INPUT:
           R - radius at which to return the enclosed mass
           z - (don't specify this) vertical height
        OUTPUT:
           mass in natural units
        HISTORY:
           2014-01-29 - Written - Bovy (IAS)
        """
        a= self.a
        r= R if z is None else sqrt(R**2.+z**2.)
        return (r/a)**2./2./(1.+r/a)**2.

    @kms_to_kpcGyrDecorator
    def _nemo_accpars(self,vo,ro):
        """
        NAME:

           _nemo_accpars

        PURPOSE:

           return the accpars potential parameters for use of this potential with NEMO

        INPUT:

           vo - velocity unit in km/s

           ro - length unit in kpc

        OUTPUT:

           accpars string

        HISTORY:

           2018-09-14 - Written - Bovy (UofT)

        """
        GM= self._amp*vo**2.*ro/2.
        return "0,1,%s,%s,0" % (GM,self.a*ro)


class JaffePotential(DehnenSphericalPotential):
    """Class that implements the Jaffe potential

    .. math::

        \\rho(r) = \\frac{\\mathrm{amp}}{4\\,\\pi\\,a^3}\\,\\frac{1}{(r/a)^2\\,(1+r/a)^{2}}

    """
    def __init__(self,amp=1.,a=1.,dehnen_amp=False,normalize=False,ro=None,vo=None):
        """
        NAME:

           __init__

        PURPOSE:

           Initialize a Jaffe potential

        INPUT:

           amp - amplitude to be applied to the potential (default: 1); can be a Quantity with units of mass or Gxmass

           a - scale radius (can be Quantity)

           dehnen_amp - if True, use dehnen normalization, amp -> amp * (3 - alpha)

           normalize - if True, normalize such that vc(1.,0.)=1., or, if given as a number, such that the force is this fraction of the force necessary to make vc(1.,0.)=1.

           ro=, vo= distance and velocity scales for translation into internal units (default from configuration file)

        OUTPUT:

           (none)

        HISTORY:

           2010-07-09 - Written - Bovy (NYU)

        """
        super(JaffePotential, self).__init__(
            amp=amp,a=a,alpha=2,dehnen_amp=dehnen_amp,
            normalize=normalize,ro=ro,vo=vo)
        self.hasC= True
        self.hasC_dxdv= True
        del self._nemo_accname  # TODO implement as None
        return None

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, value):
        raise Exception('cannot modify alpha')

    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self, value):
        raise Exception('cannot modify beta')

    def _evaluate(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _evaluate
        PURPOSE:
           evaluate the potential at R,z
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           Phi(R,z)
        HISTORY:
           2010-07-09 - Started - Bovy (NYU)
        """
        a= self.a
        return -numpy.log(1.+a/sqrt(R**2.+z**2.))/a

    def _Rforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rforce
        PURPOSE:
           evaluate the radial force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the radial force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        sqrtRz= sqrt(R**2.+z**2.)
        return -R/sqrtRz**3./(1.+self.a/sqrtRz)

    def _zforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _zforce
        PURPOSE:
           evaluate the vertical force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the vertical force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        sqrtRz= sqrt(R**2.+z**2.)
        return -z/sqrtRz**3./(1.+self.a/sqrtRz)

    def _R2deriv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _R2deriv
        PURPOSE:
           evaluate the second radial derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the second radial derivative
        HISTORY:
           2011-10-09 - Written - Bovy (IAS)
        """
        a= self.a
        sqrtRz= sqrt(R**2.+z**2.)
        return (a*(z**2.-R**2.)+(z**2.-2.*R**2.)*sqrtRz)\
            /sqrtRz**4./(a+sqrtRz)**2.

    def _Rzderiv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rzderiv
        PURPOSE:
           evaluate the mixed R,z derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           d2phi/dR/dz
        HISTORY:
           2013-08-28 - Written - Bovy (IAS)
        """
        a= self.a
        sqrtRz= sqrt(R**2.+z**2.)
        return -R*z*(2.*a+3.*sqrtRz)*sqrtRz**-4.\
            *(a+sqrtRz)**-2.

    def _surfdens(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _surfdens
        PURPOSE:
           evaluate the surface density for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the surface density
        HISTORY:
           2018-08-19 - Written - Bovy (UofT)
        """
        a= self.a
        r= sqrt(R**2.+z**2.)
        Rma= sqrt(R**2.-a**2.+0j)
        if Rma == 0.:
            return (3.*z**2.-2.*a**2.
                    +2.*sqrt(1.+(z/a)**2.)\
                        *(a**2.-2.*z**2.)
                    +3.*z**3./a*numpy.arctan(z/a))\
                    /a/z**3./6./pi
        else:
            return ((2.*a**2.-R**2.)*Rma**-3\
                        *(numpy.arctan(z/Rma)-numpy.arctan(a*z/r/Rma))
                    +numpy.arctan(z/R)/R
                    -a*z/(R**2-a**2)/(r+a)).real\
                    /a/2./pi

    def _mass(self,R,z=0.,t=0.):
        """
        NAME:
           _mass
        PURPOSE:
           calculate the mass out to a given radius
        INPUT:
           R - radius at which to return the enclosed mass
           z - (don't specify this) vertical height
        OUTPUT:
           mass in natural units
        HISTORY:
           2014-01-29 - Written - Bovy (IAS)
        """
        a= self.a
        r= R if z is None else sqrt(R**2.+z**2.)
        # if z is None: r= R
        # else: r= sqrt(R**2.+z**2.)
        return r/a/(1.+r/a)


class NFWPotential(TwoPowerSphericalPotential):
    """Class that implements the NFW potential

    .. math::

        \\rho(r) = \\frac{\\mathrm{amp}}{4\\,\\pi\\,a^3}\\,\\frac{1}{(r/a)\\,(1+r/a)^{2}}

    """
    def __init__(self,amp=1.,a=1.,normalize=False,
                 conc=None,mvir=None,
                 vo=None,ro=None,
                 H=70.,Om=0.3,overdens=200.,wrtcrit=False):
        """
        NAME:

           __init__

        PURPOSE:

           Initialize a NFW potential

        INPUT:

           amp - amplitude to be applied to the potential (default: 1); can be a Quantity with units of mass or Gxmass

           a - scale radius (can be Quantity)

           normalize - if True, normalize such that vc(1.,0.)=1., or, if given as a number, such that the force is this fraction of the force necessary to make vc(1.,0.)=1.


           Alternatively, NFW potentials can be initialized using 

              conc= concentration

              mvir= virial mass in 10^12 Msolar

           in which case you also need to supply the following keywords
           
              H= (default: 70) Hubble constant in km/s/Mpc
           
              Om= (default: 0.3) Omega matter
       
              overdens= (200) overdensity which defines the virial radius

              wrtcrit= (False) if True, the overdensity is wrt the critical density rather than the mean matter density
           
           ro=, vo= distance and velocity scales for translation into internal units (default from configuration file)

        OUTPUT:

           (none)

        HISTORY:

           2010-07-09 - Written - Bovy (NYU)

           2014-04-03 - Initialization w/ concentration and mass - Bovy (IAS)

        """
        Potential.__init__(self,amp=amp,ro=ro,vo=vo,amp_units='mass')  # need to initialize some params
        if _APY_LOADED and isinstance(a,units.Quantity):
            a= a.to(units.kpc).value/self._ro
        if conc is None:
            pass
        else:
            if wrtcrit:
                od= overdens/bovy_conversion.dens_in_criticaldens(self._vo,
                                                                  self._ro,H=H)
            else:
                od= overdens/bovy_conversion.dens_in_meanmatterdens(self._vo,
                                                                    self._ro,
                                                                    H=H,Om=Om)
            mvirNatural= mvir*100./bovy_conversion.mass_in_1010msol(self._vo,
                                                                    self._ro)
            rvir= (3.*mvirNatural/od/4./pi)**(1./3.)
            amp= mvirNatural/(numpy.log(1.+conc)-conc/(1.+conc))
            a= rvir/conc

        # reinitialize, properly now
        self.integerSelf=None
        super(NFWPotential, self).__init__(
            amp=amp,a=a,alpha=1,beta=3,
            normalize=normalize,ro=ro,vo=vo)
        self.hasC= True
        self.hasC_dxdv= True
        self._nemo_accname= 'NFW'
        return None

    @property
    def alpha(self):
        return self._alpha
    @alpha.setter
    def alpha(self, value):
        raise Exception('cannot modify alpha')

    @property
    def beta(self):
        return self._beta
    @beta.setter
    def beta(self, value):
        raise Exception('cannot modify beta')

    def _evaluate(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _evaluate
        PURPOSE:
           evaluate the potential at R,z
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           Phi(R,z)
        HISTORY:
           2010-07-09 - Started - Bovy (NYU)
        """
        r= sqrt(R**2.+z**2.)
        return -numpy.log(1.+r/self.a)/r

    def _Rforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rforce
        PURPOSE:
           evaluate the radial force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the radial force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        Rz= R**2.+z**2.
        sqrtRz= sqrt(Rz)
        return R*(1./Rz/(self.a+sqrtRz)-numpy.log(1.+sqrtRz/self.a)/sqrtRz/Rz)

    def _zforce(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _zforce
        PURPOSE:
           evaluate the vertical force for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the vertical force
        HISTORY:
           2010-07-09 - Written - Bovy (NYU)
        """
        Rz= R**2.+z**2.
        sqrtRz= sqrt(Rz)
        return z*(1./Rz/(self.a+sqrtRz)-numpy.log(1.+sqrtRz/self.a)/sqrtRz/Rz)

    def _R2deriv(self,R,z,phi=0.,t=0.,_forceFloatEval=True):
        """
        NAME:
           _R2deriv
        PURPOSE:
           evaluate the second radial derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
           _forceFloatEval: always true
        OUTPUT:
           the second radial derivative
        HISTORY:
           2011-10-09 - Written - Bovy (IAS)
        """
        Rz= R**2.+z**2.
        sqrtRz= sqrt(Rz)
        return (3.*R**4.+2.*R**2.*(z**2.+self.a*sqrtRz)\
                    -z**2.*(z**2.+self.a*sqrtRz)\
                    -(2.*R**2.-z**2.)*(self.a**2.+R**2.+z**2.+2.*self.a*sqrtRz)\
                    *numpy.log(1.+sqrtRz/self.a))\
                    /Rz**2.5/(self.a+sqrtRz)**2.

    def _Rzderiv(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _Rzderiv
        PURPOSE:
           evaluate the mixed R,z derivative for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           d2phi/dR/dz
        HISTORY:
           2013-08-28 - Written - Bovy (IAS)
        """
        Rz= R**2.+z**2.
        sqrtRz= sqrt(Rz)
        return -R*z*(-4.*Rz-3.*self.a*sqrtRz+3.*(self.a**2.+Rz+2.*self.a*sqrtRz)*numpy.log(1.+sqrtRz/self.a))*Rz**-2.5*(self.a+sqrtRz)**-2.

    def _surfdens(self,R,z,phi=0.,t=0.):
        """
        NAME:
           _surfdens
        PURPOSE:
           evaluate the surface density for this potential
        INPUT:
           R - Galactocentric cylindrical radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           the surface density
        HISTORY:
           2018-08-19 - Written - Bovy (UofT)
        """
        r= sqrt(R**2.+z**2.)
        Rma= sqrt(R**2.-self.a**2.+0j)
        if Rma == 0.:
            za2= (z/self.a)**2
            return self.a*(2.+sqrt(za2+1.)*(za2-2.))/6./pi/z**3
        else:
            return (self.a*Rma**-3\
                        *(numpy.arctan(self.a*z/r/Rma)-numpy.arctan(z/Rma))
                    +z/(r+self.a)/(R**2.-self.a**2.)).real/2./pi

    def _mass(self,R,z=0.,t=0.):
        """
        NAME:
           _mass
        PURPOSE:
           calculate the mass out to a given radius
        INPUT:
           R - radius at which to return the enclosed mass
           z - (don't specify this) vertical height
        OUTPUT:
           mass in natural units
        HISTORY:
           2014-01-29 - Written - Bovy (IAS)
        """
        if z is None: r= R
        else: r= sqrt(R**2.+z**2.)
        return numpy.log(1+r/self.a)-r/self.a/(1.+r/self.a)

    @bovy_conversion.physical_conversion('position',pop=False)
    def rvir(self,H=70.,Om=0.3,t=0.,overdens=200.,wrtcrit=False,ro=None,vo=None,
             use_physical=False): # use_physical necessary bc of pop=False, does nothing inside
        """
        NAME:

           rvir

        PURPOSE:

           calculate the virial radius for this density distribution

        INPUT:

           H= (default: 70) Hubble constant in km/s/Mpc
           
           Om= (default: 0.3) Omega matter
       
           overdens= (200) overdensity which defines the virial radius

           wrtcrit= (False) if True, the overdensity is wrt the critical density rather than the mean matter density

           ro= distance scale in kpc or as Quantity (default: object-wide, which if not set is 8 kpc))

           vo= velocity scale in km/s or as Quantity (default: object-wide, which if not set is 220 km/s))

        OUTPUT:
        
           virial radius
        
        HISTORY:

           2014-01-29 - Written - Bovy (IAS)

        """
        if ro is None: ro= self._ro
        if vo is None: vo= self._vo
        if wrtcrit:
            od= overdens/bovy_conversion.dens_in_criticaldens(vo,ro,H=H)
        else:
            od= overdens/bovy_conversion.dens_in_meanmatterdens(vo,ro,
                                                                H=H,Om=Om)
        dc= 12.*self.dens(self.a,0.,t=t,use_physical=False)/od
        x= optimize.brentq(lambda y: (numpy.log(1.+y)-y/(1.+y))/y**3.-1./dc,
                           0.01,100.)
        return x*self.a

    @kms_to_kpcGyrDecorator
    def _nemo_accpars(self,vo,ro):
        """
        NAME:

           _nemo_accpars

        PURPOSE:

           return the accpars potential parameters for use of this potential with NEMO

        INPUT:

           vo - velocity unit in km/s

           ro - length unit in kpc

        OUTPUT:

           accpars string

        HISTORY:

           2014-12-18 - Written - Bovy (IAS)

        """
        ampl= self._amp*vo**2.*ro
        vmax= sqrt(ampl/self.a/ro*0.2162165954) #Take that factor directly from gyrfalcon
        return "0,%s,%s" % (self.a*ro,vmax)
