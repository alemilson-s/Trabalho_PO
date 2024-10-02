from pyomo.environ import *
from pyomo.opt import SolverFactory


def read_parameters(file_path):
    q = {}
    C_W = {}
    C_P = {}
    D = {}
    S_a = {}
    S_p = {}
    S_total_animais = 0
    S_total_pecas = 0

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('#') or not line:
                continue

            parts = line.split()
            param_name = parts[0]
            param_value = float(parts[-1])

            if param_name.startswith('custo_'):
                if param_name.split('_')[1] in ['boi', 'porco', 'frango']:
                    animal = param_name.split('_')[1]
                    C_W[animal] = param_value
                else:
                    piece = '_'.join(param_name.split('_')[1:])
                    C_P[piece] = param_value
            elif param_name.startswith('demanda_'):
                piece = '_'.join(param_name.split('_')[1:])
                D[piece] = param_value
            elif param_name.startswith('espaco_'):
                if 'animal' in param_name:
                    animal = param_name.split('_')[2]
                    S_a[animal] = param_value
                else:
                    piece = '_'.join(param_name.split('_')[1:])
                    S_p[piece] = param_value
            elif param_name.startswith('capacidade_total_animais'):
                S_total_animais = param_value
            elif param_name.startswith('capacidade_total_pecas'):
                S_total_pecas = param_value
            else:
                try:
                    animal, piece = param_name.split('_', 1)
                    q[(animal, piece)] = param_value
                except ValueError:
                    pass

    return q, C_W, C_P, D, S_a, S_p, S_total_animais, S_total_pecas


# Criando o modelo
model = ConcreteModel()

model.Animais = Set(initialize=['boi', 'porco', 'frango'])
model.Pecas = Set(initialize=[
    'file_mignon', 'picanha', 'alcatra', 'contra_file', 'cha_dentro', 'cha_fora',
    'lagarto', 'patinho', 'acem', 'musculo', 'paleta', 'peito', 'costela_s_osso',
    'costela_c_osso', 'figado', 'costela_suina', 'lombo', 'pernil', 'bacon',
    'linguica', 'peito_frango', 'coxa_sobrecoxa', 'asa', 'moela_frango'
])

q, C_W, C_P, D, S_a, S_p, S_total_animais, S_total_pecas = read_parameters('parametros.txt')

model.q = Param(model.Animais, model.Pecas, initialize=q, default=0)
model.C_W = Param(model.Animais, initialize=C_W, default=0)
model.C_P = Param(model.Pecas, initialize=C_P, default=0)
model.D = Param(model.Pecas, initialize=D, default=0)
model.S_a = Param(model.Animais, initialize=S_a, default=0)
model.S_p = Param(model.Pecas, initialize=S_p, default=0)
model.S_total_animais = Param(initialize=S_total_animais)
model.S_total_pecas = Param(initialize=S_total_pecas)

model.W = Var(model.Animais, within=NonNegativeIntegers)
model.P = Var(model.Pecas, within=NonNegativeIntegers)


# Função objetivo
def objective_function(model):
    return (sum(model.C_W[a] * model.W[a] for a in model.Animais) +
            sum(model.C_P[p] * model.P[p] for p in model.Pecas))


model.obj = Objective(rule=objective_function, sense=minimize)


# Restrições de demanda
def demand_constraints(model, p):
    return (sum(model.q[a, p] * model.W[a] for a in model.Animais) +
            model.P[p]) >= model.D[p]


model.demand = Constraint(model.Pecas, rule=demand_constraints)


# Restrições de espaço para animais
def storage_constraint_animais(model):
    return sum(model.S_a[a] * model.W[a] for a in model.Animais) <= model.S_total_animais


model.storage_animais = Constraint(rule=storage_constraint_animais)


# Restrições de espaço para peças
def storage_constraint_pecas(model):
    return sum(model.S_p[p] * model.P[p] for p in model.Pecas) <= model.S_total_pecas


model.storage_pecas = Constraint(rule=storage_constraint_pecas)

solver = SolverFactory('glpk')
results = solver.solve(model, tee=True)

print("\nResultados da Otimização:")
for a in model.Animais:
    print(f"Número de {a}s comprados: {model.W[a].value}")

for p in model.Pecas:
    if (p != 'frango_assado'):
        print(f"Quantidade de {p}s comprados: {model.P[p].value} kg")


print("\nCusto total: R$", model.obj())

