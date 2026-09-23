import pandas as pd
import gurobipy as gp
from gurobipy import GRB, Model

model = Model("1||ΣTi")

model.setParam("TimeLimit", ...) # limite de execução (segundos)

# Dados
df = pd.read_csv("arquivo.csv", sep=";")

tarefas = df["tarefa"].to_list()
p = df.set_index("tarefa")["pi"].to_dict()
d = df.set_index("tarefa")["di"].to_dict()

M = ... # parâmetro Big-M

# Variáveis
C = model.addVars(tarefas, vtype=GRB.CONTINUOUS, lb=0, name="Ci")
X = model.addVars(tarefas, tarefas, vtype=GRB.BINARY, name="Xij")
T = model.addVars(tarefas, vtype=GRB.CONTINUOUS, lb=0, name="Ti")

# Função objetivo
model.setObjective(gp.quicksum(T[i] for i in tarefas if i != 0), GRB.MINIMIZE)

# Restrições
for i in tarefas:
    # (1): cada tarefa tem exatamente um sucessor
    model.addConstr(gp.quicksum(X[i, j] for j in tarefas if j != i) == 1)

for j in tarefas:
    # (2): cada tarefa tem exatamente um predecessor
    model.addConstr(gp.quicksum(X[i, j] for i in tarefas if i != j) == 1)

for i in tarefas:
    for j in tarefas:
        if i != j and j != 0: # tarefa fictícia não pode ser sucessora
            # (3): restrição de precedência
            model.addConstr(C[j] >= C[i] - M + (p[j] + M) * X[i, j])

# (4): fixação da tarefa fictícia 0 como início do cronograma
model.addConstr(C[0] == 0)

for i in tarefas:
    if i != 0:
        # definição do atraso de cada tarefa
        model.addConstr(T[i] >= C[i] - d[i])

# Otimização
model.optimize()

# Mapeamento de status
status_map = {
    GRB.LOADED: "LOADED",
    GRB.OPTIMAL: "OPTIMAL",
    GRB.INFEASIBLE: "INFEASIBLE",
    GRB.INF_OR_UNBD: "INF_OR_UNBD",
    GRB.UNBOUNDED: "UNBOUNDED",
    GRB.CUTOFF: "CUTOFF",
    GRB.ITERATION_LIMIT: "ITERATION_LIMIT",
    GRB.NODE_LIMIT: "NODE_LIMIT",
    GRB.TIME_LIMIT: "TIME_LIMIT",
    GRB.SOLUTION_LIMIT: "SOLUTION_LIMIT",
    GRB.INTERRUPTED: "INTERRUPTED",
    GRB.NUMERIC: "NUMERIC",
    GRB.SUBOPTIMAL: "SUBOPTIMAL",
    GRB.INPROGRESS: "INPROGRESS",
    GRB.USER_OBJ_LIMIT: "USER_OBJ_LIMIT",
    GRB.WORK_LIMIT: "WORK_LIMIT",
    GRB.MEM_LIMIT: "MEM_LIMIT",
    GRB.LOCALLY_OPTIMAL: "LOCALLY_OPTIMAL",
    GRB.LOCALLY_INFEASIBLE: "LOCALLY_INFEASIBLE"
}
status_str = status_map.get(model.Status, f"UNKNOWN_{model.Status}")

# Impressão dos resultados
if model.SolCount > 0:
    gap = model.MIPGap

    resultados = []
    for i in tarefas:
        if i != 0:
            termino = C[i].X
            inicio = termino - p[i]
            resultados.append({
                "tarefa": i,
                "inicio": int(round(inicio)),
                "termino": int(round(termino)),
                "atraso": round(T[i].X, 2),
                "status": status_str,
                "objetivo": model.ObjVal,
                "gap": gap
            })

    dfr = pd.DataFrame(resultados).sort_values(by=["inicio"])
    dfr.to_csv("resultado.csv", sep=";", index=False)
else:
    print(f"\nNenhuma solução viável encontrada. Status: {status_str}\n")

# Referências
# ARENALES, Marcos Nereu et al. Pesquisa Operacional. Rio de Janeiro: Elsevier, 2007.
# GUROBI OPTIMIZATION, LLC. Gurobi Optimizer: versão 13.0. Beaverton: Gurobi Optimization, 2025. Disponível em: https://www.gurobi.com. Acesso em: 23 set. 2026.
