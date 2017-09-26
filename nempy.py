import pandas as pd
import db_interface as dbi
import pulp
import matplotlib.pyplot as plt
import datetime

def load_sample(day = datetime.datetime(2016,11,1)):
	day_n = day + datetime.timedelta(1)
	sql =	"SELECT SETTLEMENTDATE,TOTALDEMAND "\
			"FROM TRADING_REGIONSUM "\
			"WHERE REGIONID = 1 AND "\
				"SETTLEMENTDATE > '2016-11-1' "\
				"AND SETTLEMENTDATE <= '2016-11-2'"
	return dbi.data_framer("nemweb",sql,index_col=None)
	
offers = {	"coal":{"capacity":2000,"price":32,"color":'#323232',"ramp":50},
			"coal2":{"capacity":2000,"price":35,"color":'#424242',"ramp":50},
			"coal3":{"capacity":2000,"price":9,"color":'#662506',"ramp":50},
			"gas1":{"capacity":2000,"price":40,"color":'#CC4C02',"ramp":200},
			"gas2":{"capacity":2000,"price":45,"color":'#EC7014',"ramp":500},
			"gas3":{"capacity":2000,"price":50,"color":'#FB9A29',"ramp":1000}	}			
	
def solve_dispatch(df):
	for offer in offers:
		df[offer] = df.SETTLEMENTDATE.apply(lambda x: pulp.LpVariable("{0}_{1}".format(offer,x),0,offers[offer]['capacity']))

	prob = pulp.LpProblem("Optimal dispatch", pulp.LpMinimize)
	
	prob += pulp.lpSum([(df[offer] * offers[offer]['price']).values.tolist() for offer in offers])
	
	for i,row in df.iterrows():
		prob += pulp.lpSum(row[offers.keys()].values.tolist()) == row['TOTALDEMAND']
	
	prob.solve()
	
	for offer in offers:
		df[offer] = df[offer].apply(lambda x: x.value())
	
	
def plot_results(df):
	fig, ax = plt.subplots()
	
	order = sorted(offers, key= lambda x: offers[x]['price'])

	ax.stackplot(df.SETTLEMENTDATE.values, [df[i].values for i in order], colors=[offers[offer]['color'] for offer in order])	
	ax.grid()
	ax.legend()		

	plt.show()
