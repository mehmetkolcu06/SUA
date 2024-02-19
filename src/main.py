
import argparse
import numpy as np
import scipy.stats as stats
import pandas as pd
from gurobipy import *

np.random.seed(123)


def Load_Data():

    global Demand_Variance,Product_Details

    # Read data from Excel file
    Input_File_Path = "Data/Input_SUA - orig.xlsx"
    # Input_File_Path = "Data/Input_SUA.xlsx"
    Demand_Variance_Sheet_Name = "Demand Variance"
    Product_Details_Sheet_Name = "Demand"
    Demand_Variance = pd.read_excel(Input_File_Path, sheet_name=Demand_Variance_Sheet_Name)
    Product_Details = pd.read_excel(Input_File_Path, sheet_name=Product_Details_Sheet_Name, header=None)
    Product_Details = Product_Details.T.reset_index(drop=True)
    Product_Details.columns = Product_Details.iloc[0]
    Product_Details = Product_Details.drop(0).reset_index(drop=True)
    Product_Details[["Product", "Substitutability group", "Variance group"]] = Product_Details[["Product", "Substitutability group", "Variance group"]].astype(int)




def Generate_Random_vars(generate_random_values):
    global random_values
    # file_random_values = 'Data/random_values_sample.xlsx'
    file_random_values = 'Data/random_values.xlsx'
    num_random_values = 50000
    Products = list(Product_Details["Product"])
    if generate_random_values:
        random_values=[]
        for i in Products:
            Var_Grp=Product_Details[Product_Details['Product'] == i]['Variance group'].iloc[0]
            c = Demand_Variance[Demand_Variance["Demand Var Group"]==Var_Grp]["c"]  # Shape parameter 1
            d = Demand_Variance[Demand_Variance["Demand Var Group"]==Var_Grp]["d"]  # Shape parameter 2
            loc = Demand_Variance[Demand_Variance["Demand Var Group"]==Var_Grp]["loc"]  # Location parameter
            scale = Demand_Variance[Demand_Variance["Demand Var Group"]==Var_Grp]["scale"]  # Scale parameter
            burr_dist = stats.burr12(c=c, d=d, loc=loc, scale=scale)
            random_values.append([rv for rv in burr_dist.rvs(size=num_random_values) if rv > 0][:num_scenario])

        random_values = pd.DataFrame(random_values).T
        random_values.to_excel(file_random_values,sheet_name='random_values', index=False, header=False)
        print("Generation new random data from burr 12 distribution for each product is completed \n")

    else:
        random_values = pd.read_excel(file_random_values,sheet_name='random_values', header=None).values.tolist()
        print("Reading existing random data from burr 12 distribution for each product is completed \n")




# sensitivity analysis
# for macro_target_percentage in range(10, 16, 1):
#     # print(macro_target_percentage)
#     mtp=macro_target_percentage/100
#     print("mtp=",mtp)
#     capacity_constraint = model.getConstrByName("Agg_Cap")
#     for i in Products:
#         model.chgCoeff(capacity_constraint, y[i], -mtp)
#
#     model.update()
#     model.optimize()
#     model.write("toy_example_mtp="+str(mtp)+".lp")
#
#     Obj=model.objVal
#     Y_Values = []
#     for i in Products:
#         Y_Values.append(y[i].x)
#     print(Y_Values)
#
#     Z_Values = []
#     for g in Product_Groups:
#         for i in Product_Details[Product_Details['Substitutability group']==g]['Product']:
#             # for j in Product_Details[Product_Details['Substitutability group']==g]['Product']:
#             Z_Values.append(sum(z[i,j].x for j in Product_Details[Product_Details['Substitutability group']==g]['Product']))
#     print(Z_Values)





def Run_Stochastic_Model():

    model = Model("Surplus_Allocation")
    model.setParam('OutputFlag', False)

    y = {}
    for i in Products:
        y[i] = model.addVar(name="y_"+str(i))
    print("Defining variables for regular production amount for each product is completed \n")

    z = {}
    for g in Product_Groups:
        for i in Product_Details[Product_Details['Substitutability group']==g]['Product']:
            for j in Product_Details[Product_Details['Substitutability group']==g]['Product']:
                z[i,j] = model.addVar(name="z_"+str(i)+"_"+str(j))
    print("Defining variables for substitution production amount for each product in the same product category is completed \n")

    s = {}
    for n in Scenarios:
        for i in Products:
            s[n,i] = model.addVar(name="s_"+str(n)+"_"+str(i))
    print("Defining variables for Shortage production amount for each product and each scenario is completed \n")

    k = {}
    for n in Scenarios:
        for i in Products:
            k[n,i] = model.addVar(name="k_"+str(n)+"_"+str(i))
    print("Defining variables for Surplus production amount for each product and each scenario is completed \n")


    model.setObjective(quicksum(Product_Details[Product_Details["Product"]==i]["Margin"].iloc[0] * s[n,i]+Product_Details[Product_Details["Product"]==i]["COGS"].iloc[0] * k[n,i] for i in Products for n in Scenarios)/num_scenario,GRB.MINIMIZE)
    print("Setting objective function is completed \n")

    [model.addConstr(quicksum(z[i,j] for j in Product_Details[Product_Details['Substitutability group']==Product_Details[Product_Details['Product']==i]['Substitutability group'].iloc[0]]['Product'])<=Product_Details[Product_Details["Product"]==i]["Capacity"].iloc[0]*y[i],name="Cap_"+str(i)) for i in Products if Product_Details[Product_Details["Product"]==i]["Capacity"].notna().iloc[0]]
    print("Adding Capacity constraints for each product is completed \n")

    model.addConstr(quicksum(z[i,j]  for g in Product_Groups for i in Product_Details[Product_Details['Substitutability group']==g]['Product'] for j in Product_Details[Product_Details['Substitutability group']==g]['Product'])<=(macro_target_percentage)*quicksum(y[i] for i in Products),name="Agg_Cap")
    print("Adding Aggregate Capacity constraints for all product is completed \n")

    [model.addConstr(s[n,i]>=Product_Details[Product_Details["Product"] == i]["Demand"].iloc[0]*random_values[n][i]-y[i]-quicksum(z[j,i] for j in Product_Details[Product_Details['Substitutability group']==Product_Details[Product_Details['Product']==i]['Substitutability group'].iloc[0]]['Product']),name="Shortage_"+str(n)+"_"+str(i)) for i in Products for n in Scenarios]
    print("Adding Shortage constraints for each product and each scenario is completed \n")

    [model.addConstr(k[n,i]>=quicksum(z[j,i] for j in Product_Details[Product_Details['Substitutability group']==Product_Details[Product_Details['Product']==i]['Substitutability group'].iloc[0]]['Product'])+y[i]-Product_Details[Product_Details["Product"] == i]["Demand"].iloc[0]*random_values[n][i],name="Surplus_"+str(n)+"_"+str(i)) for i in Products for n in Scenarios]
    print("Adding Surplus constraints for each product and each scenario is completed \n")

    model.update()
    model.optimize()
    model.write("Output/Surplus_Allocation_Model_with_"+str(num_scenario)+"_Scenario_macro_target_percentage_"+str(macro_target_percentage)+".lp")

    Y_Values = []
    for i in Products:
        Y_Values.append(y[i].x)

    Z_Values = [[0]*len(Products) for _ in range(len(Products))]
    for g in Product_Groups:
        for i in Product_Details[Product_Details['Substitutability group']==g]['Product']:
            for j in Product_Details[Product_Details['Substitutability group']==g]['Product']:
                Z_Values[i][j]=z[i,j].x

    output_file = "Output/Production_Amount_with_"+str(num_scenario)+"_Scenario_macro_target_percentage_"+str(macro_target_percentage)+".xlsx"

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df_Y_Values= pd.DataFrame(Y_Values,columns=["Regular Production Amount"])
        df_Y_Values.index = [f"Product_{i}" for i in range(len(Products))]
        df_Y_Values.to_excel(writer, index=False, header=True, sheet_name='Production Amount')

        df_Z_Values= pd.DataFrame(Z_Values,columns=[f"Surplus Amount to Product_{i}" for i in range(len(Products))])
        df_Z_Values.index = [f"Surplus Amount from Product_{i}" for i in range(len(Products))]
        df_Z_Values.to_excel(writer, index=False, header=True, sheet_name='Production Amount Transition')



def str_to_bool(s):
    if s.lower() in ('true', 't', 'yes', 'y', '1'):
        return True
    elif s.lower() in ('false', 'f', 'no', 'n', '0'):
        return False
    else:
        raise ValueError("Invalid boolean value: " + s)


def Read_Args():

    global num_scenario,macro_target_percentage,generate_random_values

    parser = argparse.ArgumentParser()

    # Add arguments
    parser.add_argument('--num_scenario', type=int, default=1000, help='Int argument')
    parser.add_argument('--macro_target_percentage', type=float, default=0.3, help='Float argument')
    parser.add_argument('--generate_random_values', type=str_to_bool, default=False, help='Boolean argument')

    # Parse arguments
    args = parser.parse_args()

    # Retrieve arguments
    num_scenario = args.num_scenario
    macro_target_percentage = args.macro_target_percentage
    generate_random_values = args.generate_random_values

    if num_scenario>10000 and generate_random_values==False:
        print("\nPlease enter less than 10000 as number of scenario to use existing random variables")
        exit()

    print("\nCreating a stochastic optimization with scenario size:", num_scenario,"\n")
    print("Macro target percentage equals to:", macro_target_percentage,"\n")
    print("Use pre-generated random variables for demand variability:", generate_random_values,"\n")


def Set_Constanst():
    global Scenarios,Products,Product_Groups
    Scenarios = list(range(num_scenario))
    Products = list(Product_Details["Product"])
    Product_Groups = Product_Details['Substitutability group'].unique()


def main():

    Read_Args()

    Load_Data()

    Set_Constanst()

    Generate_Random_vars(generate_random_values)

    Run_Stochastic_Model()


if __name__ == '__main__':
    main()
