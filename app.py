import streamlit as st
from pulp import *

def leer_datos(contenido):
    tokens = contenido.decode('utf-8').split()
    
    idx = 0
    i_count = int(tokens[idx+1]); idx+=2
    o_count = int(tokens[idx+1]); idx+=2
    n_count = int(tokens[idx+1]); idx+=2

    r = {}
    s = {}

    while idx < len(tokens):
        tipo = tokens[idx]
        num  = int(tokens[idx+1])
        prod = int(tokens[idx+2])
        cant = int(tokens[idx+3])
        idx += 4
        if tipo == 'r':
            r[(num, prod)] = cant
        else:
            s[(num, prod)] = cant

    I = list(range(1, i_count+1))
    J = list(range(1, o_count+1))
    K = list(range(1, n_count+1))

    return I, J, K, r, s

def resolver(I, J, K, r, s):
    D = 10
    V = 5
    M = 100000

    prob = LpProblem("CrossDocking", LpMinimize)

    T  = LpVariable("makespan", lowBound=0)
    c  = LpVariable.dicts("c", I, lowBound=0)
    F  = LpVariable.dicts("F", I, lowBound=0)
    d  = LpVariable.dicts("d", J, lowBound=0)
    L  = LpVariable.dicts("L", J, lowBound=0)

    x = LpVariable.dicts("x", [(i,j,k) for i in I for j in J for k in K], lowBound=0, cat='Integer')
    v = LpVariable.dicts("v", [(i,j) for i in I for j in J], cat='Binary')
    p = LpVariable.dicts("p", [(i,i2) for i in I for i2 in I], cat='Binary')
    q = LpVariable.dicts("q", [(j,j2) for j in J for j2 in J], cat='Binary')

    prob += T

    for j in J:
        prob += T >= L[j]

    for i in I:
        for k in K:
            prob += lpSum(x[(i,j,k)] for j in J) == r.get((i,k), 0)

    for j in J:
        for k in K:
            prob += lpSum(x[(i,j,k)] for i in I) == s.get((j,k), 0)

    for i in I:
        for j in J:
            for k in K:
                prob += x[(i,j,k)] <= M * v[(i,j)]

    for i in I:
        prob += F[i] >= c[i] + lpSum(r.get((i,k), 0) for k in K)

    for i in I:
        for i2 in I:
            if i != i2:
                prob += c[i2] >= F[i] + D - M * (1 - p[(i,i2)])

    for i in I:
        for i2 in I:
            if i != i2:
                prob += c[i] >= F[i2] + D - M * p[(i,i2)]

    for i in I:
        prob += p[(i,i)] == 0

    for j in J:
        prob += L[j] >= d[j] + lpSum(s.get((j,k), 0) for k in K)

    for j in J:
        for j2 in J:
            if j != j2:
                prob += d[j2] >= L[j] + D - M * (1 - q[(j,j2)])

    for j in J:
        for j2 in J:
            if j != j2:
                prob += d[j] >= L[j2] + D - M * q[(j,j2)]

    for j in J:
        prob += q[(j,j)] == 0

    for i in I:
        for j in J:
            prob += L[j] >= c[i] + V + lpSum(x[(i,j,k)] for k in K) - M * (1 - v[(i,j)])

    prob.solve(PULP_CBC_CMD(msg=0))

    return prob, T, c, F, d, L, x, v, I, J, K

st.title("Cross Docking - LogiFast CR")
st.write("Subí el archivo TXT con los datos de operación")

archivo = st.file_uploader("Seleccioná el archivo", type="txt")

if archivo is not None:
    with st.spinner("Resolviendo el modelo... puede tardar unos minutos"):
        I, J, K, r, s = leer_datos(archivo.read())
        prob, T, c, F, d, L, x, v, I, J, K = resolver(I, J, K, r, s)

    if LpStatus[prob.status] == "Optimal":
        st.success(f"✅ Tiempo mínimo de operación: {value(T):.0f} minutos")

        st.subheader("Orden de camiones entrantes")
        orden_entrada = sorted(I, key=lambda i: value(c[i]))
        for i in orden_entrada:
            st.write(f"Camión entrante {i} → entra min {value(c[i]):.0f}, sale min {value(F[i]):.0f}")

        st.subheader("Orden de camiones salientes")
        orden_salida = sorted(J, key=lambda j: value(d[j]))
        for j in orden_salida:
            st.write(f"Camión saliente {j} → entra min {value(d[j]):.0f}, sale min {value(L[j]):.0f}")

        st.subheader("Transferencias")
        hay_almacenamiento = False
        for i in I:
            for j in J:
                for k in K:
                    val = value(x[(i,j,k)])
                    if val and val > 0.01:
                        if value(d[j]) < value(F[i]):
                            hay_almacenamiento = True
                            st.write(f"Camión entrante {i} → Camión saliente {j} | Producto {k}: {val:.0f} uds ⚠️ ALMACENAMIENTO TEMPORAL")
                        else:
                            st.write(f"Camión entrante {i} → Camión saliente {j} | Producto {k}: {val:.0f} uds ✅ DIRECTO")

        st.subheader("Análisis del almacenamiento temporal")
        if hay_almacenamiento:
            st.warning("Se usó almacenamiento temporal en esta solución. Esto genera tiempo extra y movimientos innecesarios.")
        else:
            st.success("No se usó almacenamiento temporal. La solución óptima logró transferencias directas en todos los casos.")
    else:
        st.error("No se encontró solución óptima")