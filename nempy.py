import os
import pandas as pd
import pulp
import matplotlib.pyplot as plt
import datetime

data_dir = os.path.join(os.path.dirname(__file__), 'data')

offers = {	"wind":{"capacity":10000,"price":0,"color":'#117733',"cost":0},
			"solar":{"capacity":10000,"price":0,"color":'#FFCC66',"cost":0},
			"new_black_coal":{"capacity":2000,"price":32,"color":'#323232',"cost":40},
			"old_black_coal":{"capacity":2000,"price":35,"color":'#424242',"cost":45},
			"brown_coal":{"capacity":2000,"price":9,"color":'#662506',"cost":20},
			"gas_new":{"capacity":1500,"price":40,"color":'#CC4C02',"cost":50},
			"gas_old":{"capacity":1000,"price":45,"color":'#EC7014',"cost":60},
			"hydro":{"capacity":1000,"price":50,"color":'#3F60AE',"cost":0}	}			
			
def load_scenario(scen=1,solar=1000,wind=1000):
	#loads a scenario (each scenario is a different day)
	#specify installed solar/wind installed capacity using kwargs `wind` and `solar
	df = pd.read_csv("{0}/scenario_{1}.csv".format(data_dir,scen),parse_dates=['SETTLEMENTDATE'])
	df.WIND = df.WIND * wind
	df.SOLAR = df.SOLAR * solar
	return df
	
		
def solve_dispatch(df, offers=offers):
	#solve dispatch problem of scenario dataframe (loaded with 'load_sceanrio' and offer dictionary (above)
	for offer in offers:
		df[offer] = df.SETTLEMENTDATE.apply(lambda x: pulp.LpVariable("{0}_{1}".format(offer,x),0,offers[offer]['capacity']))

	prob = pulp.LpProblem("Optimal dispatch", pulp.LpMinimize)
	
	prob += pulp.lpSum([(df[offer] * offers[offer]['price']).values.tolist() for offer in offers])
	
	for i,row in df.iterrows():
		prob += pulp.lpSum(row[offers.keys()].values.tolist()) == row['TOTALDEMAND']
		
	for re_var,re_res in zip(['wind','solar'],['WIND', 'SOLAR']):
		for i,row in df.iterrows():
			prob += row[re_var] <= row[re_res]
	
	prob.solve()
	
	for offer in offers:
		df[offer] = df[offer].apply(lambda x: x.value())
		
	df['price'] = df[offers.keys()].apply(lambda x: max([offers[key]['price'] for key in offers if x.ix[key]>0]), axis=1)
	
	if prob.status !=1:
		print "No solution"		

	
def plot_results(df, offers=offers,price=False,ylim=50):
	#plot dispatch solution (after solving the dispatch problem)
	fig  = plt.figure(figsize=(10,5))
	ax = fig.add_axes([0.1, 0.12, 0.65, 0.8])
	
	order = sorted(offers, key= lambda x: offers[x]['price'])
	
	ax.plot(df.SETTLEMENTDATE, df.TOTALDEMAND,lw=2,color='k')

	ax.stackplot(df.SETTLEMENTDATE.values, [df[i].values for i in order], colors=[offers[offer]['color'] for offer in order], labels=["{0} - ${1}".format(offer,offers[offer]['price']) for offer in order])	
	ax.grid()
	
	handles, labels = ax.get_legend_handles_labels()
	ax.legend(handles[::-1], labels[::-1], frameon=False, bbox_to_anchor = (1.45, 1))			
	
	if price:
		ax2 = ax.twinx()
		ax2.plot(df.SETTLEMENTDATE,df.price, lw=2, color='#CC6677')
		ax2.set_ylim(0,ylim)

	plt.show()
	
#print market revenue to screen	
def market_revenue(df):
	for tech in offers:
		print "{0}:\t ${1:.02f}m".format(tech, (df.price*df[tech]).sum()/2000000)

#print revenue minus costs to screen
def daily_revenue(df,offers=offers):
	for tech in offers:
		print "{0}:\t ${1:.02f}m".format(tech, (df.price*df[tech]).sum()/2000000 - df[tech].sum()/2000000*offers[tech]['cost'])
	
