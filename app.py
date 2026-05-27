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


def tiempo_descarga(i, K, r):
    return sum(r.get((i,k), 0) for k in K)

def tiempo_carga(j, K, s):
    return sum(s.get((j,k), 0) for k in K)


def resolver(I, J, K, r, s):
    M = 100000

    prob = LpProblem("CrossDocking", LpMinimize)

    x = LpVariable.dicts("x", [(i,j,k) for i in I for j in J for k in K], lowBound=0)
    v = LpVariable.dicts("v", [(i,j) for i in I for j in J], cat='Binary')
    u_in  = LpVariable.dicts("u_in",  [(i,i2) for i in I for i2 in I], cat='Binary')
    u_out = LpVariable.dicts("u_out", [(j,j2) for j in J for j2 in J], cat='Binary')
    a = LpVariable.dicts("a", I, lowBound=0)
    d = LpVariable.dicts("d", J, lowBound=0)
    C = LpVariable("makespan", lowBound=0)

    prob += C

    for j in J:
        prob += C >= d[j] + tiempo_carga(j, K, s)

    for i in I:
        for k in K:
            prob += lpSum(x[(i,j,k)] for j in J) == r.get((i,k), 0)

    for j in J:
        for k in K:
            prob += lpSum(x[(i,j,k)] for i in I) == s.get((j,k), 0)

    for i in I:
        for j in J:
            prob += lpSum(x[(i,j,k)] for k in K) <= M * v[(i,j)]

    for i in I:
        for i2 in I:
            if i != i2:
                prob += a[i2] >= a[i] + tiempo_descarga(i, K, r) + 10 - M * (1 - u_in[(i,i2)])
                prob += a[i]  >= a[i2] + tiempo_descarga(i2, K, r) + 10 - M * u_in[(i,i2)]

    for i in I:
        for i2 in I:
            if i != i2:
                prob += u_in[(i,i2)] + u_in[(i2,i)] == 1

    for i in I:
        prob += u_in[(i,i)] == 0

    for j in J:
        for j2 in J:
            if j != j2:
                prob += d[j2] >= d[j] + tiempo_carga(j, K, s) + 10 - M * (1 - u_out[(j,j2)])
                prob += d[j]  >= d[j2] + tiempo_carga(j2, K, s) + 10 - M * u_out[(j,j2)]

    for j in J:
        for j2 in J:
            if j != j2:
                prob += u_out[(j,j2)] + u_out[(j2,j)] == 1

    for j in J:
        prob += u_out[(j,j)] == 0

    for i in I:
        for j in J:
            prob += d[j] >= a[i] + tiempo_descarga(i, K, r) + 5 - M * (1 - v[(i,j)])

    prob.solve(PULP_CBC_CMD(msg=0))

    return prob, C, a, d, x, I, J, K


st.title("Cross Docking - LogiFast CR")
st.write("Subí el archivo TXT con los datos de operación")

archivo = st.file_uploader("Seleccioná el archivo", type="txt")

if archivo is not None:
    with st.spinner("Resolviendo el modelo..."):
        I, J, K, r, s = leer_datos(archivo.read())
        prob, C, a, d, x, I, J, K = resolver(I, J, K, r, s)

    if LpStatus[prob.status] == "Optimal":
        st.success(f"Tiempo mínimo de operación: {value(C):.0f} minutos")

        st.subheader("Orden de camiones entrantes")
        orden_entrada = sorted(I, key=lambda i: value(a[i]))
        for i in orden_entrada:
            st.write(f"Camión entrante {i} → empieza en minuto {value(a[i]):.0f}")

        st.subheader("Orden de camiones salientes")
        orden_salida = sorted(J, key=lambda j: value(d[j]))
        for j in orden_salida:
            st.write(f"Camión saliente {j} → empieza en minuto {value(d[j]):.0f}")

        st.subheader("Transferencias")
        for i in I:
            for j in J:
                for k in K:
                    val = value(x[(i,j,k)])
                    if val and val > 0.01:
                        st.write(f"Camión entrante {i} → Camión saliente {j} | Producto {k}: {val:.0f} unidades")
    else:
        st.error("No se encontró solución óptima")