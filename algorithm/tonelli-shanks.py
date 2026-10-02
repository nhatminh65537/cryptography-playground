def tonelli_shanks(a, p):

    if pow(a, (p-1)//2, p) == -1 % p:
        raise ValueError("The value a not in QR")
    
    q = p - 1
    s = 0
    while q % 2 == 0:
        s += 1
        q //= 2

    for z in range(2, 1000):
        if pow(z, (p-1)//2, p) == -1 % p:
            break
    else:
        raise ValueError("Not found z in QNR")
    
    m = s
    c = pow(z, q, p)
    t = pow(a, q, p)
    r = pow(a, (q+1)//2, p)

    while t != 1:
        for i in range(m):
            if pow(t, 2**i, p) == 1:
                break
        b = pow(c, 2**(m - i - 1), p)

        m = i
        c = pow(b, 2, p)
        t = t*pow(b, 2, p) % p
        r = r * b % p

    return r

p = 106820149819400494839844872937187910328668278979553494454992841651120635399461
a = 31337
r1 = tonelli_shanks(a, p)
r2 = -r1 % p
print(r1, r2, sep='\n')
