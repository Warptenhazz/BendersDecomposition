from gurobipy import *
import numpy as np
# scenarioss = [sc1,sc2,sc3,sc4,sc5,sc6,sc7,sc8,sc9,sc10,sc11,sc12]
# for i in scenarioss:

from sc1 import inputBlock, upperPriceBlock, upperPriceForward, priceBlock, costBlock, PricePool, Aconstant

###################################################################################
#Sets
#Hours
t, h1 = multidict({"1": [1],"2": [1],"3": [1],"4": [1],"5": [1]})
#Scenarios
omega, sc = multidict({'1': [1],'2': [1],'3': [1],'4': [1],'5': [1],'6': [1],'7': [1],'8': [1],'9': [1],'10': [1],'11': [1],'12': [1]})
#Blocks in the price-quota curves
i, bl1 = multidict({1: [1], 2: [1],3: [1]})
#Forwards
f, fr = multidict({"Forward 1": [1],	"Forward 2": [1]})
#input blocks in forward contracts
j, pb = multidict({"Bajo": [1],"Moderado": [1],"Alto": [1]})
#Clients
l, client = multidict({"Pequeno": [1],"Mediano": [1]})
#Parameters
#targeted profit z_0s
targetedProfit = 1.5
#probability of scenario omega
scenarioProb = {
('1'): 0.083, ('2'): 0.065,	('3'): 0.10,	('4'): 0.20,	('5'): 0.06,	('6'): 0.20,	('7'): 0.10,	('8'): 0.08,	('9'): 0.15,	('10'): 0.18,	('11'): 0.20,	('12'): 0.20}
##################################################################################
#Model
m = Model("complete")
master = Model("Master")
auxiliar = Model("Auxiliar")
#Variables definition
#cost of purchasing from forward contracts in each period omega
costF = auxiliar.addVars(t, name ="cost forward", vtype= GRB.CONTINUOUS)
#net cost of trading in the pool in period t and scenario omega
costP = auxiliar.addVars(t, omega, name = "cost pool", vtype= GRB.CONTINUOUS)
#input purchased from contract f
inputTotalF =  auxiliar.addVars(f, name="input from forward contract", vtype= GRB.CONTINUOUS)
#input purchased from the jth block of the forward contracting curve belonging to contract f
inputBlockF = auxiliar.addVars(f, j, obj = 1, name="input from block from forward contract", vtype= GRB.CONTINUOUS)
#input supplied by the retailer to farmer group l in the period t and scenario omega
inputR = auxiliar.addVars(l, t, omega, name="input supplied by the retailer", vtype= GRB.CONTINUOUS)
#input traded in the pool in the period t and scenario omega
inputP = auxiliar.addVars(t, omega, name="input traded in the pool", vtype= GRB.CONTINUOUS)	
#selling price settled by the retailer for farmer group l 
gammaSellingR = auxiliar.addVars(l, name="price settled by the retailer", vtype= GRB.CONTINUOUS)
#price of the ith interval of the price-quota curve for farmer gruop l
gammaPriceR = auxiliar.addVars(l, i, name ="price of the interval of price-quota curve ", vtype= GRB.CONTINUOUS)
#revenue obtained by the retailer from selling to farmer group l in period t and scenario omega
INR = auxiliar.addVars(l,t,omega, name = "revenue obtained ", vtype= GRB.CONTINUOUS)
#binary variable selling price offered by the retailer to cliente group l belongs to block i of the price-quota curve
A = master.addVars(l,i, name="selling price offered by the retailer to farmer group", vtype=GRB.BINARY)
#Auxiliar variable who storages the profit by scenario
foAux = auxiliar.addVars(omega, name ="Auxiliar variable who storages the profit by scenario - Auxiliar", vtype = GRB.CONTINUOUS)
#Auxiliar variable who storages the profit by scenario
foMaster = master.addVars(omega, name ="Auxiliar variable who storages the profit by scenario - Master", vtype = GRB.CONTINUOUS)
#compute the risk for scenario
riskScenario = master.addVars(omega, name ="risk for scenario", vtype= GRB.CONTINUOUS)
#k(w) is an auxiliary binary variable and equal to 0 of profit(w) > z0 and 1 if profit(w) <= z0
k = master.addVars(omega, name="auxiliary binary variable 2 for calculate risk", vtype = GRB.BINARY)
#risk for scenario in auxiliar problem
dr = auxiliar.addVars(omega, name= "downside risk in auxiliar problem", vtype = GRB.CONTINUOUS)
#EDR for scenario 
EDRS = auxiliar.addVars(omega, name="EDR for scenario", vtype = GRB.CONTINUOUS)
#EDR for function objective
EDRZ = []
#zlower for optimality cut
zlower = 1 #master.addVars(name="min value for optimality cut", vtype = GRB.CONTINUOUS)
master.update()
auxiliar.update()
#save the objective function for each model
ofAux = {}
ofMaster = {}
it = 1
##################################################################################
#Constrains for the master problem
#2. The cost of purchasing input through the forward contracts.
def constraint2(priceBlock):
	ctr2 = {}
	for hour in t:
		ctr2[hour] = auxiliar.addConstr(costF[hour] == (quicksum(inputBlockF[frw,pwb] * priceBlock[frw,pwb] for frw in f for pwb in j)))	#need to changue the sumatory for pwb in j to for pwb in Nj
	auxiliar.update()

#3. The input purchased in each block is non-negative and bounded by an upper limit.
def constraint3(upperPriceForward):
	ctr3a = {}
	for pwb in j: 
		for frw in f:
			ctr3a[pwb,frw] = auxiliar.addConstr(inputBlockF[frw,pwb] >= 0)		
	auxiliar.update()
	ctr3b = {}
	for pwb in j:
		for frw in f:
			ctr3a[pwb,frw] = auxiliar.addConstr(inputBlockF[frw,pwb] <= upperPriceForward[frw,pwb])
	auxiliar.update()

#4. The input purchased for each contract is the sum of the input purchased in each block
def constraint4():
	ctr4 = {}
	for frw in f: 
		ctr4[frw] = auxiliar.addConstr(inputTotalF[frw] == quicksum(inputBlockF[frw,pwb] for pwb in j)) 
	auxiliar.update()

#The price-quota curve for each farmer group in each period and scenario can be formulated as follows:
#5. Pool related 
def constraint5(PricePool):
	ctr5 = {}
	for hour in t:
		for sc in omega:
			ctr5[hour,sc] = auxiliar.addConstr(costP[hour,sc] == PricePool[hour,sc]*inputP[hour,sc])
	auxiliar.update()


#7.A[l,i] is a set of binary variables that identify the interval of the price-quota curve corresponding to the selling price cRl  							
def constraint7():
	ctr7 = {}
	for client in l:
		ctr7[client] = auxiliar.addConstr(gammaSellingR[client] == quicksum(gammaPriceR[client,bg] for bg in i)) #need to changue the sumatory
	auxiliar.update()

#11. The revenue obtained from selling input to the farmers is calculated from the following expression. Employment of a stepwise price-quota curve allows expressing the revenue as a linear constraint
def constraint11(inputBlock):
	ctr11 = {}
	for hour in t:
		for client in l:
			for sc in omega:
				ctr11[hour,client,sc] = auxiliar.addConstr(INR[client,hour,sc] 
						== quicksum(inputBlock[client,bg,hour,sc]*gammaPriceR[client,bg] for bg in i))  
	auxiliar.update()

def solutionAuxiliar():
    if auxiliar.status == GRB.Status.OPTIMAL:
        print('-|--|--|--|--|--|--|--|--|--|')
        #price settled by the retailer
        gammaPriceRx = auxiliar.getAttr('x', gammaPriceR)
        print('\nVariables de decision:')
        #Print the variable result for the price settled
        print("\nPrecio establecido por el intermediador")
        print("Se tiene un solo precio por bloque de la curva de demanda")
        for client in l:
        	print "Cliente " + str(client) + str(quicksum(gammaPriceRx[client,bg] for bg in i))
		#revenue obtained by the retailer 
        INRX = auxiliar.getAttr('x',INR)
        print('\nGanancia obtenida por el intermediador')
        print('Esto se obtiene por escenario definido')
        for sc in omega:
			print "Escenario "+ str(sc) + str( quicksum(INRX[client,hour,sc] for client in l for hour in t))
		#input purchased from the contract
    	inputTotalFx = auxiliar.getAttr('x', inputTotalF)
    	print('\nCantidad de pesticidas (ton) comprados al mayorista')
    	print('Esto se obtiene por contrato')
    	for frw in f:
    		print "Contrato " + str(frw) + "--> " + str(inputTotalFx[frw]) #IMPORTANT OUTPUT
    	inputBlockFx = auxiliar.getAttr('x',inputBlockF)
    	print('\nPrecio al que compra el intermediador por bloque')
    	print('Se obtiene por contrato')
    	for frw in f:
    		print 'Contrato ' + str(frw) + '-->' + str( quicksum(inputBlockFx[frw,pb] for pb in j) )
    	print('\nPrecio al que vende el intermediador por tipo de cliente')
    	print('Se obtiene por tipo de cliente (creo)')
    	inputPFx = auxiliar.getAttr('x',inputP)
    	for sc in omega:
    		for hour in t:
    			print 'Escenario -> ' + str(sc) +'->'+ str(inputPFx[hour,sc])

##################################################################################
#Constrains for the master problem
#9. change bg as string to int for iterate
def constraint9():
  	ctr9 = {}
  	for client in l:
  		ctr9[client] = master.addConstr(quicksum(A[client,bg] for bg in i) == 1 )
  	master.update()

# # #14. conditional expression for calculate risk if there is unfulfilled profit
M = 1000000
def constraint14a():
 	for scenario in omega:
  		master.addConstr(0 <= riskScenario[scenario] - (targetedProfit ) <= M * (1-k[scenario]))
  	master.update()


def constraint14b():
 	for scenario in omega:
  		master.addConstr(0 <= riskScenario[scenario] <= (M*k[scenario]))
  	master.update()

def optimizeMaster():
	# master objective function
	# 12a. auxiliar variable for the profit for scenario

	for scenario in omega:			
	  	foMaster[scenario] = quicksum(inputBlock[client,bg,hour,sc]*A[client,bg] for client in l for bg in i for hour in t for sc in omega)
	  		# - inputBlockF[frw,pwb]*priceBlock[frw,pwb]  
	  		# - inputP[hour,sc]*PricePool[hour,sc] for frw in f for pwb in j for hour in t for hour in t for client in l for bg in i for sc in omega)

	quicksum(scenarioProb[sc] * quicksum(
	(quicksum(inputBlock[client,bg,hour,sc]*gammaPriceR[client,bg] for client in l for bg in i)
	- quicksum(inputP[hour,sc]*PricePool[hour,sc] for hour in t for sc in omega)
	- quicksum(inputBlockF[frw,pwb]*priceBlock[frw,pwb] for frw in f for pwb in j))
	for hour in t)
	for sc in omega)

	objFuncMaster = LinExpr()
	# # #12. The expected profit of retailer which is equal to the expected revenue obtained from selling inputs to the end-users and to the pool minus the expected cost of purchasing inputs from the pool and through forward contracts as follows:
	objFuncMaster += quicksum(scenarioProb[sc] * foMaster[sc]  for sc in omega)
	constraint9()
	constraint14a()
	constraint14b()
 	master.update()
 	master.setObjective(objFuncMaster,GRB.MAXIMIZE)
 	master.Params.Presolve = 0
 	master.optimize()
 	


def solutionMaster():
    if master.status == GRB.Status.OPTIMAL:
        print('-|--|--|--|--|--|--|--|--|')
        #price settled by the retailer
        print('\nVariables de decision:')
        #Print the variable result for the price settled
        Ax = master.getAttr('x', A)
        print("\nBloque ofrecido por el intermediador")
        print("Se tiene un solo precio por bloque de la curva de demanda por cliente")
        for client in l:
        	for bg in i:
				print "Cliente " + str(client) + " " + "Curva (Binaria) " + str(bg) + ' -> ' +str(Ax[client,bg]) 
 				Aconstant[client,bg] = Ax[client,bg] 				
 		#risk by scenario 
        riskScenariox = master.getAttr('x',riskScenario)
        print('\nNivel de riesgo por escenario')
        for sc in omega:
 			print "Escenario "+ str(sc) + " ---> " + str(riskScenariox[sc])


def solveMaster():
	optimizeMaster()
	solutionMaster()


def solveAuxiliar():
	constraint2(priceBlock)
	constraint3(upperPriceForward)
	constraint4()
	constraint5(PricePool)
	#constraint6(optimizeMaster,inputBlock)
	constraint7()
	#constraint8(upperPriceBlock)
	#constraint10(inputBlock)
	constraint11(inputBlock)
	#12a. auxiliar variable for the profit for scenario

	quicksum(scenarioProb[sc] * quicksum(
	(quicksum(inputBlock[client,bg,hour,sc]*gammaPriceR[client,bg] for client in l for bg in i)
	- quicksum(inputP[hour,sc]*PricePool[hour,sc] for hour in t for sc in omega)
	- quicksum(inputBlockF[frw,pwb]*priceBlock[frw,pwb] for frw in f for pwb in j))
	for hour in t)
	for sc in omega)

	auxiliar.update()
	#auxiliar Objective function 
	objFuncAux = LinExpr()
	#12. The expected profit of retailer which is equal to the expected revenue obtained from selling inputs to the end-users and to the pool minus the expected cost of purchasing inputs from the pool and through forward contracts as follows:
	objFuncAux += quicksum(
				scenarioProb[sc] * 
				foAux[scenario]  for scenario in omega for sc in omega)
	auxiliar.update()
	#Optimice the auxiliar problem
	auxiliar.update()
	auxiliar.setObjective(objFuncAux,GRB.MAXIMIZE)
	auxiliar.Params.Presolve = 0
	auxiliar.optimize()
	#Calculate the EDR 
	for scenario in omega:
		if foAux[scenario] <= targetedProfit:
			dr[scenario] = targetedProfit - foAux[scenario]
		else:
			dr[scenario] = 0
		EDRS[scenario] = scenarioProb[scenario] * dr[scenario]
		EDRZ.append(EDRS[scenario])
	return EDRZ



def addCuts(inputBlock,upperPriceBlock):
	#The price-quota curve for each client group in each period and scenario can be formulated as follows:
	#6. The demand provided by the retailer is equal to the level of input of the price-quota curve indicated by binary variables
	ctr6 = {}
	for hour in t:
		for client in l:
			for sc in omega:
				ctr6[hour,client,sc] = auxiliar.addConstr(inputR[client,hour,sc] == quicksum(inputBlock[client,bg,hour,sc]*Aconstant[client,bg] for bg in i)) #need to changue the sumatory
	auxiliar.update()

#8. change bg as string to int for iterate
	ctr8A = {}
	for client in l:
		for bg in (bg1 for bg1 in i if bg1 > 1): 
			ctr8A[client,bg] = auxiliar.addConstr(gammaPriceR[client,bg]  
				 >= upperPriceBlock[client,bg-1]*Aconstant[client,bg])
	ctr8B = {}
	for client in l:
		for bg in i:
			ctr8B[client,bg] = auxiliar.addConstr(gammaPriceR[client,bg] <= upperPriceBlock[client,bg]*Aconstant[client,bg])
	auxiliar.update()

#10. The electric input balance of the retailer in each period and scenario is expressed as follows
	ctr10 = {}
	for hour in t:
		for sc in omega:
			ctr10[hour,sc] = auxiliar.addConstr(
				quicksum(inputBlock[client,bg,hour,sc] for client in l for bg in i)*Aconstant[client,bg]
				>= (quicksum(inputP[hour,sc]+inputBlockF[frw,pwb] for frw in f for pwb in j)))
	auxiliar.update()

print("PRIMERO HPTAAAAAAAAAAAAA")
solveMaster()
# print('\nAUXILIAR HPTAAAAAAAAAAAAA')
# solveAuxiliar()
# print("SEGUNDO HPTAAAAAAAAAAAAA")
# addCuts(inputBlock,upperPriceBlock)
# print('---*-*--*-*--*-*--*-*--*-*-Cortes aadidos -*-*--*-*--*-*--*-*-')
# solveAuxiliar()

while it < 10:
 	print "Iteracion -------------------->> " + str(it) 
 	print('\nProblema Maestro')
 	if master.status == GRB.Status.INFEASIBLE:
 		print "Problema Maestro infactible, debe parar" 
 		v = master.getVars()
 		break
 	solveMaster()
 	solveAuxiliar()
 	if master.status == GRB.Status.OPTIMAL:
 		print('\nProblema Auxiliar')
 		solveAuxiliar()
 		solutionAuxiliar()
 		if auxiliar.status == GRB.Status.UNBOUNDED:
 			print('\nModelo auxiliar no acotado')
 			dualVariables = [c.Pi for c in auxiliar.getConstrs()]
 			print('\nAnadiendo corte por factiblidad')  
 			master.addConstr(dualVariables <=  0) #quicksum(Fy[client,i] for client in l for bg in i)
 			v = master.getVars()
			print(v[0].varName, v[0].x)
 		if auxiliar.status == GRB.Status.INFEASIBLE:
 			print('\nModelo auxiliar infactible')
 			dualVariables = [c.Pi for c in auxiliar.getConstrs()]
 			zlower = auxiliar.ObjVal
 			master.addConstr(zlower >= dualVariables)
 			v = master.getVars()
 			print(v[0].varName, v[0].x)
 	it += 1 

#try:
# 	while auxiliar.ObjVal != 0:
# 		it += 1 
# 		print "Iteracion -------------------->> " + str(it) 
# 		print('\nProblema Maestro')
# 		optimizeMaster()
# 		solutionMaster()
# 		print('\nProblema Auxiliar')
# 		optimizeAuxiliar()
# 		solutionAuxiliar()
#except AttributeError:
# 	print "Iteracion ------------------------>> " + str(it)
# 	if auxiliar.status == GRB.Status.UNBOUNDED:
# 		dualVariables = [c.Pi for c in auxiliar.getConstrs()]  
# 		h = 1
# 		Fy = {}
# 		Ax = master.getAttr('x', A)
# 		for client in l:
# 			for bg in i:
# 				Fy[client,bg] = Ax[client,bg]
#		factCuts ={}
# 		print('\nAnadiendo corte por factibilidad...')
# 		master.addConstr(dualVariables <= 0) #quicksum(Fy[client,i] for client in l for bg in i)
# 		print('\nResolviendo problema maestro...')
# 		optimizeMaster()
# 		solutionMaster()


