from sage.all import *

def miller_function(T1, T2, P):
    x, y = P.xy()
    if T1.is_zero() or T2.is_zero():
        return 1

    x1, y1 = T1.xy()
    x2, y2 = T2.xy()
    E = P.curve()
    a = E.a4()
    assert E(x1, y1) and E(x2, y2) and E(x, y), "Points must be on the same curve"
    if x1 == x2 and y1 == -y2:
        return x - x1
    
    Ts = T1 + T2
    xs, _ = Ts.xy()
    if T1 == T2:
        lbd = (3*x1**2 + a) / (2*y1)
    else:
        lbd = (y2 - y1) / (x2 - x1)
    return (y - y1 - lbd * (x - x1)) / (x - xs)

def miller_algorithm(P, Q, n):
    R = P
    f = 1
    l = int(n).bit_length()
    for i in range(l - 2, -1, -1):
        f = f**2 * miller_function(R, R, Q)
        R = 2*R
        if (n >> i) & 1:
            f = f * miller_function(R, P, Q)
            R = R + P
    return f

F = GF(631)
E = EllipticCurve(F , [30, 34])
n = 10

print(f"Elliptic curve: {E}")
print(f"Order of the curve: {E.order()} = {E.order().factor()}")

F2 = GF((631, 2), 'a')
E2 = E.base_extend(F2)
print(f"Elliptic curve over extension field: {E2}")
print(f"Order of the curve over extension field: {E2.order()} = {E2.order().factor()}")

print(f"=== Weil pairing implementation ===")
def weil_pairing(P, Q, n):
    return (-1)**n * miller_algorithm(P, Q, n) / miller_algorithm(Q, P, n)

U, V = E2.torsion_basis(n)
P = U*ZZ.random_element(n) + V*ZZ.random_element(n)
Q = U*ZZ.random_element(n) + V*ZZ.random_element(n)
# P = Q = E(0)
# while P.is_zero(): 
#     R = E.random_point()
#     if R.order() % n == 0:
#         P = (R.order() // n) * R
# while Q.is_zero(): 
#     R = E.random_point()
#     if R.order() % n == 0:
#         Q = (R.order() // n) * R

print(f"P: {P}")
print(f"Q: {Q}")
print(f"e(P, Q): {weil_pairing(P, Q, n)}")
print(f"e(P, Q) (sage): {P.weil_pairing(Q, n)}")

print(f"=== Tate pairing implementation ===")
def tate_pairing(P, Q, n, k):
    return miller_algorithm(P, Q, n)**((F.order()**k - 1) // n)

k = 2
P = E(0)
while P.is_zero(): 
    R = E.random_point()
    if R.order() % n == 0:
        P = (R.order() // n) * R
P = E2(P)
Q = E2(0)
while Q.is_zero(): 
    R = E2.random_point()
    if R.order() % n == 0:
        Q = (R.order() // n) * R

print(f"P: {P}")
print(f"Q: {Q}")

print(f"t(P, Q): {tate_pairing(P, Q, n, k)}")
print(f"t(P, Q) (sage): {P.tate_pairing(Q, n, k)}")

print("=== Ate pairing implementation ===")
def ate_pairing(P, Q, n, k, t):
    return miller_algorithm(Q, P, t)**((F.order()**k - 1) // n)

t = E.trace_of_frobenius()
q = E.order()

P = E(0)
while P.is_zero(): 
    R = E.random_point()
    if R.order() % n == 0:
        P = (R.order() // n) * R
P = E2(P)
phi = E2.frobenius_endomorphism()
while Q.is_zero(): 
    R = E2.random_point()
    if R.order() % n == 0 and phi(R) == q*R:
        Q = (R.order() // n) * R

print(f"P: {P}")
print(f"Q: {Q}")

print(f"a(P, Q): {ate_pairing(P, Q, n, k, t)}")
print(f"a(P, Q) (sage): {P.ate_pairing(Q, n, k, t)}")#
