from pulp import *

def leer_datos(archivo):
    with open(archivo, 'r') as f:
        contenido = f.read().split()
    
    idx = 0
    i_count = int(contenido[idx+1]); idx+=2
    o_count = int(contenido[idx+1]); idx+=2
    n_count = int(contenido[idx+1]); idx+=2

    r = {}
    s = {}

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

def resolver(archivo):
    I, J, K, r, s = leer_datos(archivo)

    D = 10  
    V = 5   
    M = 100000

    prob = LpProblem("CrossDocking", LpMinimize)

    # Variables continuas
    T  = LpVariable("makespan", lowBound=0)
    c  = LpVariable.dicts("c", I, lowBound=0)  # entrada camion entrante i
    F  = LpVariable.dicts("F", I, lowBound=0)  # salida camion entrante i
    d  = LpVariable.dicts("d", J, lowBound=0)  # entrada camion saliente j
    L  = LpVariable.dicts("L", J, lowBound=0)  # salida camion saliente j


    x = LpVariable.dicts("x", [(i,j,k) for i in I for j in J for k in K], lowBound=0, cat='Integer')

  
    v = LpVariable.dicts("v", [(i,j) for i in I for j in J], cat='Binary')
    p = LpVariable.dicts("p", [(i,i2) for i in I for i2 in I], cat='Binary')
    q = LpVariable.dicts("q", [(j,j2) for j in J for j2 in J], cat='Binary')

    # Funcion objetivo
    prob += T

    # Restriccion 1
    for j in J:
        prob += T >= L[j]

    # Restriccion 2
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
            for k in K:
                prob += x[(i,j,k)] <= M * v[(i,j)]

    # Restriccion 5: 
    for i in I:
        prob += F[i] >= c[i] + lpSum(r.get((i,k), 0) for k in K)

    # Restriccion 6: 
    for i in I:
        for i2 in I:
            if i != i2:
                prob += c[i2] >= F[i] + D - M * (1 - p[(i,i2)])

    # Restriccion 7: 
    for i in I:
        for i2 in I:
            if i != i2:
                prob += c[i] >= F[i2] + D - M * p[(i,i2)]

    # Restriccion 8: 
    for i in I:
        prob += p[(i,i)] == 0

    # Restriccion 9: 
    for j in J:
        prob += L[j] >= d[j] + lpSum(s.get((j,k), 0) for k in K)

    # Restriccion 10: 
    for j in J:
        for j2 in J:
            if j != j2:
                prob += d[j2] >= L[j] + D - M * (1 - q[(j,j2)])

    # Restriccion 11: 
    for j in J:
        for j2 in J:
            if j != j2:
                prob += d[j] >= L[j2] + D - M * q[(j,j2)]

    # Restriccion 12: 
    for j in J:
        prob += q[(j,j)] == 0

    # Restriccion 13: 
    for i in I:
        for j in J:
            prob += L[j] >= c[i] + V + lpSum(x[(i,j,k)] for k in K) - M * (1 - v[(i,j)])

    
    prob.solve(PULP_CBC_CMD(msg=0))

    # Resultados
    print("="*50)
    print(f"Estado: {LpStatus[prob.status]}")
    print(f"Tiempo minimo de operacion: {value(T):.0f} minutos")
    print("="*50)

    print("\nOrden de camiones entrantes:")
    orden_entrada = sorted(I, key=lambda i: value(c[i]))
    for i in orden_entrada:
        print(f"  Camion entrante {i} -> entra min {value(c[i]):.0f}, sale min {value(F[i]):.0f}")

    print("\nOrden de camiones salientes:")
    orden_salida = sorted(J, key=lambda j: value(d[j]))
    for j in orden_salida:
        print(f"  Camion saliente {j} -> entra min {value(d[j]):.0f}, sale min {value(L[j]):.0f}")

    print("\nTransferencias:")
    for i in I:
        for j in J:
            for k in K:
                val = value(x[(i,j,k)])
                if val and val > 0.01:
                    fin_descarga_i = value(F[i])
                    inicio_carga_j = value(d[j])
                    if inicio_carga_j < fin_descarga_i:
                        print(f"  Camion entrante {i} -> Camion saliente {j} | Producto {k}: {val:.0f} uds ⚠️ ALMACENAMIENTO TEMPORAL")
                    else:
                        print(f"  Camion entrante {i} -> Camion saliente {j} | Producto {k}: {val:.0f} uds ✅ DIRECTO")

resolver("TS5.txt")