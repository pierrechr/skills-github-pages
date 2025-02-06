import os
import time
from Crypto.Util.number import inverse

#########################################################
# For a survey about ladders, we refer to
# https://eprint.iacr.org/2017/293.pdf
#########################################################

def dbl(P1):
    X1, Z1 = P1
    XX = X1**2 % p
    ZZ = Z1**2 % p
    A = 2 * ((X1 + Z1) ** 2 - XX - ZZ) % p
    aZZ = a * ZZ % p
    X3 = ((XX - aZZ) ** 2 - 2 * b * A * ZZ) % p
    Z3 = (A * (XX + aZZ) + 4 * b * ZZ**2) % p
    return (X3, Z3)


def diffadd(P1, P2, x0):
    X1, Z1 = P1
    X2, Z2 = P2
    X1Z2 = X1 * Z2 % p
    X2Z1 = X2 * Z1 % p
    Z1Z2 = Z1 * Z2 % p
    T = (X1Z2 + X2Z1) * (X1 * X2 + a * Z1Z2) % p
    Z3 = (X1Z2 - X2Z1) ** 2 % p
    X3 = (2 * T + 4 * b * Z1Z2**2 - x0 * Z3) % p
    return (X3, Z3)

def scalarmult(scalar, x0):
    R0 = (x0, 1)
    R1 = dbl(R0)
    n = scalar.bit_length()
    pbit = 0
    for i in range(n - 2, -1, -1):
        bit = (scalar >> i) & 1
        pbit = pbit ^^ bit
        if pbit:
            R0, R1 = R1, R0
        R1 = diffadd(R0, R1, x0)
        R0 = dbl(R0)
        pbit = bit
    if bit:
        R0 = R1
    if R0[1] == 0:
        return "Zero point"
    return R0[0] * inverse(R0[1], p) % p

#########################################################
# Fake single coordinate scalar multiplication
# Should be a single-coordinate scalar multiplication
# for short Weierstrass form
#########################################################

def fake_scalarmult(E, scalar, x0):
    P = E.lift_x(x0)
    Q = scalar * P
    return Q.x()

#########################################################
# Set up the Invalid Curve Attack
#########################################################


p = 0xffffffffffffffffffffffffffffffffffffffffffffff13
a = 0xffffffffffffffffffffffffffffffffffffffffffffff10
b = 0x383ede2c889ca69e337f7f4adab6f486181f00da0be6826b
order = 0xfffffffffffffffffffffffe4bfe78b8c2b8586d5ea2a226


print("[+] Creating GF(p)")
t = time.time()
k = GF(p)
print(" |   Time needed to create GF(p) :", round(time.time()-t,3)," seconds.")
E = EllipticCurve(k,[a,b])

# Retrieving the twists and their coefficients

print("[+] Creating curve E, it's non trivial twist and checking orders.")
E1,E2 = E.twists()
if E1 != E :
    E1 , E2 = E2 , E1
at = E2.a4()
bt = E2.a6()
G = E1.gens()[0]
print(" |   Done : ", G.order() == order)

#########################################################
# This section plays a bit with the non trivial twist.
# This is added only to illustrate the paper.
#########################################################

d2 = k(at/a)
d,dp = sqrt(d2,all=True)

# Note that d2 has two square roots, d and -d.
# Since -1 is not a square in k, only one of d and -d is a square in k
# Set d to be the non square

print("[+] -1 is a square in GF(p) :", legendre_symbol(-1,p) == 1)
if legendre_symbol(d,p) != -1:
    d ,dp = dp ,d

# Checks that the quadratic twist of E by d is isomorphic to the twist E2

Ed = EllipticCurve(k,[a*(d**2),b*(d**3)])
print("[+] Checking isomorphism classes over GF(p).")
print(" |   Ed is isomorphic to E over GF(p) :", Ed.is_isomorphic(E))
print(" |   Ed is a non trivial twist of E over GF(p) :", Ed.is_isomorphic(E2))

#########################################################
# Setting up Invalid Curve Attack
#########################################################

print("[+] Creating GF(p**2)")
t = time.time()
k2 = GF(p**2)
print(" |   Time needed to create GF(p**2) :", round(time.time()-t,3)," seconds.")
print(" |   Ed is isomorphic to E over GF(p) :",Ed.is_isomorphic(E))
Edk2 = Ed.base_extend(k2)
Ek2 = E.base_extend(k2)
print(" |   Ed is isomorphic to E over GF(p**2) : ", Edk2.is_isomorphic(Ek2))
sqd = k2(d).sqrt()

# Defining the equation of the morphisms from E to Ed and from Ed to E
# The y-coordinate is not of any use, just omit it

def phi(x):
    return k(x/d)
def phi_inv(x):
    return k(x*d)

# G0 is a point on E2 but not on E

print("[+] Creates the point G0 = (0,y) on Ed and Factorize its order.")
x0 = 0
G0t = E2.lift_x(x0)
g0 = G0t.order()
l0 = ecm.factor(g0)
print(" |   Prime facorization of G0's order :", l0)
print(" |-  bit length of each prime in the factorization :", [a.bit_length() for a in l0])

# G1 is a point on E

print("[+] Creates the point G1 = (2,y) on E and Factorize its order.")
x1 = 2
G1 = E.lift_x(x1)
g1 = G1.order()
l1 = ecm.factor(g1)
print(" |   Prime facorization of G1's order :", l1)
print(" |-  bit length of each prime in the factorization :", [a.bit_length() for a in l1])

# There are unhandleable cofactors for DLP working in subgroups with 'small' prime factors

print("[+] Restricting to the subgroups of order containing only the small primes")
cofact0 = 1749002286417992230333906793
cofact1 = 1763644255088983457164385909
G0_ = cofact0 * G0t
G1_ = cofact1 * G1
g0_ = G0_.order()
g1_ = G1_.order()
print(" |   Done : ", G.order() == order)
print(" |   Working in the subgroup generated by G0_'s having order with prime factors : ",ecm.factor(g0_))
print(" |   Working in the subgroup generated by G1_'s having order with prime factors : ",ecm.factor(g1_))


for i in range(1):

    print("[+] Solving Challenge Number : ", i)
    rand = int.from_bytes(os.urandom(24),"big")
    privkey = min( rand %order,(order-rand)%order)

# should be
#
# pubkey0, pubkey1 = scalarmult(privkey,x0)),scalarmult(privkey,x1)
#
# for some method scalarmult implementing single-coordinate scalar multiplication ladder

    pubkey0, pubkey1 = k(fake_scalarmult(Ek2,privkey,x0)),k(fake_scalarmult(Ek2,privkey,x1))
    P0=E2.lift_x(phi_inv(pubkey0))*cofact0
    t0 = time.time()
    d0 = P0.log(G0_)
    print(" |  time for first DLP :", round(time.time()-t0,3),"seconds.")
    P1 = (E.lift_x(pubkey1))*cofact1
    t = time.time()
    d1 = P1.log(G1_)
    print(" |  time for second DLP :", round(time.time()-t,3),"seconds.")
    for s1,s2 in [(1,1),(1,-1),(-1,1),(-1,-1)]:
        if CRT_list([s1*d0 ,s2*d1],[g0_,g1_]) %order == privkey:
            print(" |-  \U0001F600 "+ " "+ "Challenge solved, privkey recovered in ", round(time.time() - t0,3)," seconds.")









