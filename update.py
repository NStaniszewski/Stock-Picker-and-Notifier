from pymongo import mongo_client
import os
import datetime
import wallstreet
import time
import numpy
import scipy.stats
import pandas
import matplotlib.pyplot


#FOR THE EMAIL NOTIFIER STOCKS, BLACK SCHOLES GREEKS ARE JUST USED TO ADVISE BUY/SELL ON THE STOCK/ETF ITSELF, NOT BUYING ACTUAL OPTIONS
#only checking options because can generally assume things will appreciate over time generally
#not doing options themselves because this focuses on high volatility stocks/etf and i dont like options for high volatility stuff
#for options, assume we just execute them on expiration date

def calc_probability_profit(price_list:pandas.DataFrame):
    start_point=price_list.iloc[0,0]
    price_list=list(price_list.iloc[-1])
    profit_nums=0
    loss_nums=0
    for price in price_list:
        if ((price-start_point)*100)/start_point>=0:
            profit_nums+=1
        else:
            loss_nums+=1
    return round(profit_nums/(profit_nums+loss_nums),4)

def monte_carlo(ticker:wallstreet.Stock):
    buy_ind=True
    days_future=101
    i=1
    ticker_history=ticker.historical(days_back=1825,frequency='d')['Close']
    
    percent_changes=numpy.log(1+ticker_history.pct_change())

    #find expected general stock direction
    expected_price_changes=numpy.exp((percent_changes.mean()-(.5*percent_changes.var()))+percent_changes.std()*scipy.stats.norm.ppf(numpy.random.rand(days_future,1000)))
    expected_prices=numpy.zeros_like(expected_price_changes) #stops it from crashing idk why
    expected_prices[0]=ticker_history.iloc[-1] #overwrite first item because its not making a prediction with the stock price the prediction will be built off


    while i<days_future: #<- number of lists generated in the 'scipy.stats.norm.ppf(numpy.random.rand(x,1000)))' , where i<x
        expected_prices[i]=expected_prices[i-1]*expected_price_changes[i]
        i+=1
    #iterate through both lists to create list of expected future price lists
    
    days_future-=1
    expected_price=round(pandas.DataFrame(expected_prices).iloc[-1].mean(),2)
    profit_prob=calc_probability_profit(pandas.DataFrame(expected_prices))
    profit_percent=round((expected_price-expected_prices[0,1])/expected_price*100,4)
    return [days_future,expected_price,profit_percent,profit_prob]

def new_options(safe_portfolio,safe_picks,aggressive_portfolio,aggressive_picks,ticker_name):
    ticker=wallstreet.Stock(ticker_name)
    ticker_info=monte_carlo(ticker)
    
    #use this call for checks
    check_call=wallstreet.Call(ticker_name,y=datetime.date.today().year+1,strike=ticker_info[1])
    delta=check_call.delta()
    vega=check_call.vega()
    if delta>=.5 and ticker_info[2]>0: #calls
        if check_call.gamma()>=.4:
            if vega>=.1 and vega<=.4: #safe
                buy_num=int(100*(vega*delta)*ticker_info[3])
                safe_picks.insert_one({"Move":"Call for "+ticker_name+" @ "+str(check_call.underlying.price)+" with a premium of " +str(check_call.price)}) 
                safe_portfolio.insert_one({"Move":"Call","Stock_Price":check_call.underlying.price,"Option_Premium":check_call.price,"Expiration":check_call.expiration,"Ticker":ticker_name,"Buy_Number":buy_num})
            elif vega<=.9: #aggressive
                buy_num=int(100*((vega+delta)/ticker_info[3]))
                aggressive_picks.insert_one({"Move":"Call for "+ticker_name+" @ "+str(check_call.underlying.price)+" with a premium of " +str(check_call.price)}) 
                aggressive_portfolio.insert_one({"Move":"Call","Stock_Price":check_call.underlying.price,"Option_Premium":check_call.price,"Expiration":check_call.expiration,"Ticker":ticker_name,"Buy_Number":buy_num})

    elif delta<.5 and ticker_info[2]<0:  #puts
        check_put=wallstreet.Put(ticker_name,y=datetime.date.today().year+1,strike=ticker_info[1])
        if check_put.gamma()>=.4:
            if vega<=.4: #safe
                buy_num=int(100*(vega*delta)*ticker_info[3])
                safe_picks.insert_one({"Move":"Put for "+ticker_name+" @ "+str(check_put.underlying.price)+" with a premium of " +str(check_put.price)}) 
                safe_portfolio.insert_one({"Move":"Put","Stock_Price":check_put.underlying.price,"Option_Premium":check_put.price,"Expiration":check_put.expiration,"Ticker":ticker_name,"Buy_Number":buy_num})
            elif vega<=.9: #aggressive
                buy_num=int(100*((vega+delta)/ticker_info[3]))
                aggressive_picks.insert_one({"Move":"Put for "+ticker_name+" @ "+str(check_put.underlying.price)+" with a premium of " +str(check_put.price)}) 
                aggressive_portfolio.insert_one({"Move":"Put","Stock_Price":check_put.underlying.price,"Option_Premium":check_put.price,"Expiration":check_put.expiration,"Ticker":ticker_name,"Buy_Number":buy_num})
  

def execute_options(portfolio,graphs):
    stock_options=portfolio.find()
    id_list=[]
    today=str(datetime.date.today().day).zfill(2)+'-'+str(datetime.date.today().month).zfill(2)+'-'+str(datetime.date.today().year) #need this to match formattings so i can do equivalency check
    for item in stock_options:
        if item['Expiration']==today:
            id_list.append(item['_id'])
            stock=wallstreet.Stock(item['Ticker'])
            most_recent_graph=graphs.find({}).sort({'_id':-1}).limit(1)
            curr_money=float(most_recent_graph['Total_Money'])
            if item['Move']=='Call':
                curr_money+=(stock.price-item['Stock_Price']-item['Option_Premium'])*item['Buy_Number']
            else:
                curr_money+=(item['Stock_Price']-item['Option_Premium']-stock.price)*item['Buy_Number']
            graphs.insert_one({'Total_Money':str(curr_money),'Timestamp':str(int(datetime.datetime.today().timestamp()))})

    for item in id_list:
        portfolio.delete_one({'_id':item})

def update_graph(stock_history_collection,graph_name):
    stock_hist=stock_history_collection.find()
    graph_list=[]
    for item in stock_hist:
        graph_list.append([float(item['Total_Money']),int(item['Timestamp'])])
    graph_list.sort(key = lambda x:x[1])
    
    x=[]
    y=[]
    day_count=0
    for item in graph_list:
        x.append(day_count)
        y.append(item[0])
        day_count+=1

    matplotlib.pyplot.plot(x,y)
    matplotlib.pyplot.xlabel('Days')
    matplotlib.pyplot.ylabel('Profit/Loss')
    matplotlib.pyplot.title(graph_name)
    matplotlib.pyplot.savefig('./views/graphs/'+graph_name+'.jpg')
    print(graph_name + ' Graph Made')

def buy(ticker,buy_price,reason,stock_collection):
    try:
        stock_collection.insert_one({"Move":"BUY","Ticker":ticker,"Price":str(buy_price),"Reason":reason})
        print('Buy Order Sent')
    except:
        print('Failed to Send Buy Order')

def sell(ticker,sell_price,reason,stock_collection):
    try:
        stock_collection.insert_one({"Move":"SELL","Ticker":ticker,"Price":str(sell_price),"Reason":reason})
        print('Sell Order Sent')
    except:
        print('Failed to Send Sell Order')

def validate_pick(call: wallstreet.Call,stock_collection):
    #BUY STUFF
    if call.delta()>=.7:  #high enough that the 2x current price or close is likely within the year span, higher than that is probably likely
        buy(call.underlying.ticker,call.underlying.price,'Reason: Delta',stock_collection)
    elif call.underlying.price<25 and call.underlying.ticker=='TQQQ': #manually set in and outs alongside the delta check for each in the mailing list based on personal analysis
        buy(call.underlying.ticker,call.underlying.price,'Reason: Manual IN',stock_collection)

    #SELL STUFF
    elif call.delta()<=.2: #with this low of a delta on a 2x current price call, not likely to beat a lot of safer options
        sell(call.underlying.ticker,call.underlying.price,'Reason: Delta',stock_collection)
    elif call.underlying.price>50 and call.underlying.ticker=='TQQQ':
        sell(call.underlying.ticker,call.underlying.price,'Reason: Manual OUT',stock_collection)
    else:
        print("No buy/sell executed")

def update():
    try:
        client=mongo_client.MongoClient("mongodb+srv://")
        stock_database=client['stocky']
        stock_collection=stock_database['notif_stock_indicators']
        aggressive_graph_collection=stock_database['aggressive_historys']
        safe_graph_collection=stock_database['safe_historys']
        agg_port_collection=stock_database['aggressive_portfolios']
        safe_port_collection=stock_database['safe_portfolios']
        agg_pick_collection=stock_database['aggressive_picks']
        safe_pick_collection=stock_database['safe_picks']
        print("Connected")
    except:
        print("Failed to Connect")
        os._exit(0)
    email_stock_tickers=['TQQQ']
    website_stock_tickers=['GOOG']
    old_date=datetime.datetime.today().date()

    for ticker in email_stock_tickers:
        call=wallstreet.Call(ticker,y=datetime.date.today().year+1,strike=wallstreet.Stock(ticker).price*2)
        print(old_date,ticker)
        print(call.price)
        print(call.underlying.price)
        print(call.implied_volatility())
        print(call.delta())
        print(call.theta())
        validate_pick(call,stock_collection)

    update_graph(aggressive_graph_collection,'Aggressive History')
    update_graph(safe_graph_collection,'Safe History')
    while True:
        if datetime.datetime.today().date()>old_date: #set to update once a day for testing so i dont use all my free api calls up for the day
            old_date=datetime.datetime.today().date()

            #email notifier stuff
            for ticker in email_stock_tickers:
                call=wallstreet.Call(ticker,y=datetime.date.today().year+1,strike=wallstreet.Stock(ticker).price*2)
                print(old_date,ticker)
                print(call.price)
                print(call.underlying.price)
                print(call.implied_volatility())
                print(call.delta())
                print(call.theta())
                validate_pick(call,stock_collection)

            #clear picks databases
            safe_pick_collection.delete_many({})
            agg_pick_collection.delete_many({})

            #execute on options
            execute_options(safe_port_collection,safe_graph_collection)
            execute_options(agg_port_collection,aggressive_graph_collection)

            #gain/loss graphs stuff
            update_graph(aggressive_graph_collection,'Aggressive History')
            update_graph(safe_graph_collection,'Safe History')

            #pick new options for today
            for stock_ticker in website_stock_tickers:
                new_options(safe_port_collection,safe_pick_collection,agg_port_collection,agg_pick_collection,stock_ticker)
        time.sleep(3600)
    
def fill_test_data():
    client=mongo_client.MongoClient("mongodb+srv://")
    stock_database=client['stocky']
    safe_graph_collection=stock_database['aggressive_historys']
    print("Connected")
    safe_graph_collection.insert_one({'Total_Money':'0','Timestamp':str(int(datetime.datetime.today().timestamp()))})

def test_graph_making():
    client=mongo_client.MongoClient("mongodb+srv://")
    stock_database=client['stocky']
    safe_graph_collection=stock_database['safe_historys']
    update_graph(safe_graph_collection,'safe')

def making_portfolios():
    client=mongo_client.MongoClient("mongodb+srv://")
    stock_database=client['stocky']
    aggressive_portfolio=stock_database['aggressive_portfolios']
    safe_portfolio=stock_database['safe_portfolios']

    buy_num=102
    check_call=wallstreet.Call('AMZN',y=datetime.date.today().year+1,strike=wallstreet.Stock('AMZN').price*2)
    aggressive_portfolio.insert_one({"Move":"Put","Stock_Price":check_call.underlying.price,"Option_Premium":check_call.price,"Expiration":check_call.expiration,"Ticker":'AMZN',"Buy_Number":buy_num})
    safe_portfolio.insert_one({"Move":"Put","Stock_Price":check_call.underlying.price,"Option_Premium":check_call.price,"Expiration":check_call.expiration,"Ticker":'AMZN',"Buy_Number":buy_num})
#test_graph_making()
#fill_test_data()
#making_portfolios()
update()

