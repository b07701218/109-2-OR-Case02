def heuristic_algorithm(file_path):

    '''
    1. Write your heuristic algorithm here.
    2. We would call this function in CS2_graded_program.py to evaluate your algorithm.
    3. Please do not change the function name and the file name.
    4. The parameter is file path of data file.
    5. You need to return the order plan in list in order.
            order[i][j][t] is amount of product i ordered in the beginning of month t with shipping method j.
            i = 1, ..., |number of product|, j = 1, 2, 3, and t = 1, ..., 26.
       Note that the indice of list need to be in order, that is , return order[i][j][t] rather than order[t][j][i]
    6. You only need to submit this algorithm_module.py.
    '''

    # import pandas as pd

    # read data (need to install openpyxl)
    # xls = pd.ExcelFile(file_path, engine='openpyxl')

    import pandas as pd
    import numpy as np
    
    url = file_path

    ## 所有資訊前處理
    # D_it
    Demand_info = pd.read_excel(url, 'Demand').iloc[:,1:]
    Demand = []
    for i in Demand_info.index:
        Demand.append(list(Demand_info.loc[i]))

    # I_it
    Init_inv_info = pd.read_excel(url, 'Initial inventory')
    In_transit_info = pd.read_excel(url, 'In-transit').iloc[:,2:]
    In_transit = []
    for i in In_transit_info.index:
        In_transit.append([list(Init_inv_info['Initial inventory'])[i]] + list(In_transit_info.loc[i]) + [0] * (26 - 3))

    # C^V_ij
    Shipping_cost_info = pd.read_excel(url, 'Shipping cost').iloc[:,1:]
    Shipping_cost = []
    for i in Shipping_cost_info.index:
        Shipping_cost.append(list(Shipping_cost_info.loc[i]) + [0])

    Price_and_cost_info = pd.read_excel(url, 'Price and cost').iloc[:,1:]
    # C^P_i
    Purchasing_cost = list(Price_and_cost_info['Purchasing cost'])
    # C^H_i
    Holding_cost = list(Price_and_cost_info['Holding cost'])

    # C^F_j
    Fixed_cost_shipping_method = [100, 80, 50]

    # T_j
    Lead_time = [1, 2, 3]

    # V_i
    Product_size_info = pd.read_excel(url, 'Size')
    Product_size = list(Product_size_info['Size'])

    Shortage_info = pd.read_excel(url, 'Shortage')
    # C^L_i
    Lost_sales_cost = list(Shortage_info['Lost sales'])
    # C^B_i
    Backorder_cost = list(Shortage_info['Backorder'])
    # beta_i
    Backorder_percentage = list(Shortage_info['Backorder percentage'])

    Vendor_product_info = pd.read_excel(url, 'Vendor-Product')
    Vendor_product = list(Vendor_product_info['Vendor'])

    Vendor_cost_info = pd.read_excel(url, 'Vendor cost')
    Vendor_cost = list(Vendor_cost_info['Ordering cost'])

    Bounds_info = pd.read_excel(url, 'Bounds')
    Bounds = list(Bounds_info['Minimum order quantity (if an order is placed)'])

    Conflict_info = pd.read_excel(url, 'Conflict')

    product1_list = list(Conflict_info['Product 1'] - 1)
    product2_list = list(Conflict_info['Product 2'] - 1)

    Conflict = []
    for i in range(len(product1_list)):
        Conflict.append(tuple([(int(product1_list[i])), (int(product2_list[i]))]))

    S_I = len(Product_size)  # Set of products
    S_J = 3                  # Set of shipping methods
    S_T = 26                 # Set of months
    S_V = len(Vendor_cost)   # Set of vendors

    order = []
    for i in range(S_I):
        order.append([])
        for j in range(S_J):
            order[i].append([])
            for t in range(S_T):
                order[i][j].append(0)

    ## 決定運送方式

    # variable shipping cost
    ocean_shipping_cost = []
    for i in range(S_I):
        unit_cost = Product_size[i] / 0.5 * 1500
        ocean_shipping_cost.append(unit_cost)

    product_demand = []
    product_demand_from4 = []
    for i in range(S_I):    
        product_demand.append(sum(Demand[i]))
        product_demand_from4.append(product_demand[i] - max(sum(In_transit[i]), sum(Demand[i][0:3])))

    ocean_cost_sum_from4 = 0
    for i in range(len(ocean_shipping_cost)):
        ocean_cost_sum_from4 += product_demand_from4[i]*ocean_shipping_cost[i]
    ocean_cost_sum_from4 += 50 * len(Demand[0])

    express_cost_sum_from4 = 0
    for i in range(len(Shipping_cost)):
        express_cost_sum_from4 += product_demand_from4[i]*Shipping_cost[i][0]
    express_cost_sum_from4 += 100*len(Demand[0])

    air_cost_sum_from4 = 0
    for i in range(len(Shipping_cost)):
        air_cost_sum_from4 += product_demand_from4[i]*Shipping_cost[i][1]
    air_cost_sum_from4 += 80*len(Demand[0])

    if express_cost_sum_from4 <= air_cost_sum_from4 and express_cost_sum_from4 <= ocean_cost_sum_from4:
        shipping_method = 0
    elif air_cost_sum_from4 <= express_cost_sum_from4 and air_cost_sum_from4 <= ocean_cost_sum_from4:
        shipping_method = 1
    else:
        shipping_method = 2

    ## 衝突產品字典

    conflict_dict = dict()

    for i in range(len(Conflict)):
        for j in range(len(Conflict[i])):
            if Conflict[i][j] not in conflict_dict:
                conflict_dict[Conflict[i][j]] = [Conflict[i][j-1]]
            else:
                conflict_dict[Conflict[i][j]].append(Conflict[i][j-1])


    # 要檢查是否有衝突的產品清單
    # 檢查順序按照有關聯的商品數排序
    # 例如 conflict_dict[31] ＝ [78, 23] 因為跟 31 產品有關聯的產品有兩個所以要先檢查
    check_conflict = list(conflict_dict.keys())
    check_conflict = sorted(check_conflict, reverse=True, key=lambda d: len(conflict_dict[d]))

    ## 計算每期短缺量並比較

    # 該訂購方式的 leadtime
    S_L = Lead_time[shipping_method]

    # 最後 S_L 期理論上不會訂貨
    for t in range(S_T - S_L):

        inv_level = []
        lostcost = []

        # 計算若當期不訂購，則未來 S_L+1 期內的存貨水準
        for i in range(S_I):
            inv_level.append(sum(In_transit[i][t:(t+S_L+1)]) - sum(Demand[i][t:(t+S_L+1)]))

            # 如果有缺貨
            if inv_level[i] < 0:
                # 計算當期訂購量
                order[i][shipping_method][t] = int(-inv_level[i])
                # 計算當期缺貨損失
                lostcost.append(-(inv_level[i] * Backorder_percentage[i] * Backorder_cost[i] + inv_level[i] * (1-Backorder_percentage[i]) * Lost_sales_cost[i]))
            else:
                # 計算當期訂購量（沒有缺貨設為 0）
                order[i][shipping_method][t] = 0 
                # 計算當期缺貨損失（沒有缺貨設為 0）
                lostcost.append(0)

        # 檢查衝突問題   
        for i in check_conflict:
            # 要比較的對象
            temp_compare_index = [i] + conflict_dict[i]
            # 要比較的對象的訂購量
            temp_compare_order = []
            for k in temp_compare_index:
                 temp_compare_order.append(order[k][shipping_method][t])

            # 如果組內有兩個產品以上要訂購，必須做處理
            if temp_compare_order.count(0) < (len(temp_compare_index) - 1):
                temp_compare_lostcost = []
                for k in temp_compare_index:
                    temp_compare_lostcost.append(lostcost[k])

                # 要訂購的產品
                trgt = temp_compare_index[temp_compare_lostcost.index(max(temp_compare_lostcost))]

                # 把其他不要訂購的產品的訂購量設為 0
                for k in temp_compare_index:
                    if k != trgt:
                        order[k][shipping_method][t] = 0
        
        # 可能衝突商品處理完成
       
        # 處理其他部分
        for i in range(S_I):
            # 處理最低訂購量
            if (order[i][shipping_method][t] > 0) and (order[i][shipping_method][t] < Bounds[i]):
                order[i][shipping_method][t] = Bounds[i]
            
            # 更新下期實際期初存貨（也可以說是在途存貨）
            # 當期就有缺貨的話則更新 backorder 量到下期需求
            if (In_transit[i][t] - Demand[i][t]) > 0:
                In_transit[i][t+1] += (In_transit[i][t] - Demand[i][t])
            
            else:
                Demand[i][t+1] += int((Demand[i][t] - In_transit[i][t]) * Backorder_percentage[i])

            # 把訂購量更新到 S_L 期後的在途存貨
            In_transit[i][t+S_L] += order[i][shipping_method][t]

    return order