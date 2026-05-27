from pulp import *


def leer_datos(archivo):
    with open(archivo, 'r') as f:
        contenido = f.read().split()
    
    idx = 0
    i_count = int(contenido[idx+1]); idx+=2
    o_count = int(contenido[idx+1]); idx+=2
    n_count = int(contenido[idx+1]); idx+=2

    r = {}  # r[i,k] = unidades producto k en camion entrante i
    s = {}  # s[j,k] = unidades producto k en camion saliente j

    while idx < len(contenido):
        tipo = contenido[idx]
        num  = int(contenido[idx+1])
        prod = int(contenido[idx+2])
        cant = int(contenido[idx+3])
        idx += 4
        if tipo == 'r':
            r[(num, prod)] = cant
        else:
            s[(num, prod)] = cant

    I = list(range(1, i_count+1))
    J = list(range(1, o_count+1))
    K = list(range(1, n_count+1))

    return I, J, K, r, s

def tiempo_descarga(i, K, r):
    return sum(r.get((i,k), 0) for k in K)

def tiempo_carga(j, K, s):
    return sum(s.get((j,k), 0) for k in K)


def resolver(archivo):
    I, J, K, r, s = leer_datos(archivo)

    M = 100000  

    prob = LpProblem("CrossDocking", LpMinimize)

    # Variables
    x = LpVariable.dicts("x", [(i,j,k) for i in I for j in J for k in K], lowBound=0)
    v = LpVariable.dicts("v", [(i,j) for i in I for j in J], cat='Binary')
    u_in  = LpVariable.dicts("u_in",  [(i,i2) for i in I for i2 in I], cat='Binary')
    u_out = LpVariable.dicts("u_out", [(j,j2) for j in J for j2 in J], cat='Binary')
    a = LpVariable.dicts("a", I, lowBound=0)  # tiempo inicio camion entrante
    d = LpVariable.dicts("d", J, lowBound=0)  # tiempo salida camion saliente
    C = LpVariable("makespan", lowBound=0)

    # Funcion objetivo
    prob += C

    # Restriccion 1: 
    for j in J:
        prob += C >= d[j] + tiempo_carga(j, K, s)

    # Restriccion 2: 
    for i in I:
        for k in K:
            prob += lpSum(x[(i,j,k)] for j in J) == r.get((i,k), 0)

    # Restriccion 3:
    for j in J:
        for k in K:
            prob += lpSum(x[(i,j,k)] for i in I) == s.get((j,k), 0)

    # Restriccion 4: 
    for i in I:
        for j in J:
            prob += lpSum(x[(i,j,k)] for k in K) <= M * v[(i,j)]

    # Restriccion 5 y 6: 
    for i in I:
        for i2 in I:
            if i != i2:
                prob += a[i2] >= a[i] + tiempo_descarga(i, K, r) + 10 - M * (1 - u_in[(i,i2)])
                prob += a[i]  >= a[i2] + tiempo_descarga(i2, K, r) + 10 - M * u_in[(i,i2)]

    # Restriccion 7:
    for i in I:
        for i2 in I:
            if i != i2:
                prob += u_in[(i,i2)] + u_in[(i2,i)] == 1

    # Restriccion 8: 
    for i in I:
        prob += u_in[(i,i)] == 0

    # Restriccion 9 y 10: 
    for j in J:
        for j2 in J:
            if j != j2:
                prob += d[j2] >= d[j] + tiempo_carga(j, K, s) + 10 - M * (1 - u_out[(j,j2)])
                prob += d[j]  >= d[j2] + tiempo_carga(j2, K, s) + 10 - M * u_out[(j,j2)]

    # Restriccion 11:
    for j in J:
        for j2 in J:
            if j != j2:
                prob += u_out[(j,j2)] + u_out[(j2,j)] == 1

    # Restriccion 12:
    for j in J:
        prob += u_out[(j,j)] == 0

    # Restriccion 13: 
    for i in I:
        for j in J:
            prob += d[j] >= a[i] + tiempo_descarga(i, K, r) + 5 - M * (1 - v[(i,j)])

  
    prob.solve(PULP_CBC_CMD(msg=0))


    print("="*50)
    print(f"Estado: {LpStatus[prob.status]}")
    print(f"Tiempo minimo de operacion: {value(C):.0f} minutos")
    print("="*50)

    print("\nOrden de camiones entrantes:")
    orden_entrada = sorted(I, key=lambda i: value(a[i]))
    for i in orden_entrada:
        print(f"  Camion entrante {i} -> empieza en minuto {value(a[i]):.0f}")

    print("\nOrden de camiones salientes:")
    orden_salida = sorted(J, key=lambda j: value(d[j]))
    for j in orden_salida:
        print(f"  Camion saliente {j} -> empieza en minuto {value(d[j]):.0f}")

    print("\nTransferencias:")
    for i in I:
        for j in J:
            for k in K:
                val = value(x[(i,j,k)])
                if val and val > 0.01:
                    print(f"  Camion entrante {i} -> Camion saliente {j} | Producto {k}: {val:.0f} unidades")

resolver("TS5.txt")