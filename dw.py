import pandas as pd
import psycopg2 as pg
# Postgres connection variables
hostname = 'localhost'
database = 'erp dw'
username = 'postgres'
pwd = '123'
port_id = 5432
conn = None
cur = None

# Sql Statement to define Profit Margin
profitMargenSql = '''select q2.location_name,q2.time_year,
sum (SumInvoiceAmt - total_costs)/ SUM(SumInvoiceAmt)*100  as profit_margin
from (	SELECT s.job_id,l.location_id,l.location_name,j.quantity_ordered,j.unit_price,
    	t.time_year,t.time_month,sum(i.invoice_quantity) AS suminvoiceqty
	    ,sum(i.invoice_amount) AS suminvoiceamt
   		FROM w_job_shipment_f sh,w_sub_job_f s,w_location_d l,
    	w_time_d t,w_invoiceline_f i,w_job_f j
  		WHERE s.sub_job_id = sh.sub_job_id AND sh.invoice_id = i.invoice_id 
	  	AND t.time_id = j.contract_date AND l.location_id = i.location_id AND j.job_id = s.job_id
  		GROUP BY s.job_id, l.location_id, l.location_name, j.quantity_ordered, j.unit_price, t.time_year, t.time_month) q2,
  
  ( 	SELECT j.job_id,l.location_id,l.location_name,t.time_year,
    	t.time_month,sum(s.cost_labor) AS cost_labor,
    	sum(s.cost_material) AS cost_material,
    	sum(s.machine_hours * m.rate_per_hour) AS machine_costs,
    	sum(s.cost_overhead) AS cost_overhead,
    	sum(s.cost_labor + s.cost_material + s.machine_hours * m.rate_per_hour + s.cost_overhead) AS total_costs,
    	sum(s.quantity_produced) AS quantity_produced,
    	sum(s.cost_labor + s.cost_material + s.machine_hours * m.rate_per_hour + s.cost_overhead) / sum(s.quantity_produced)::numeric AS unit_cost
   		FROM w_job_f j,w_time_d t,w_sub_job_f s,w_location_d l,w_machine_type_d m
  		WHERE j.contract_date = t.time_id AND j.location_id = l.location_id 
   		AND j.job_id = s.job_id AND s.machine_type_id = m.machine_type_id
  		GROUP BY j.job_id, l.location_id, l.location_name, t.time_year, t.time_month) q3
  where q2.job_id = q3.job_id
  group by q2.location_name,q2.time_year
  order by q2.time_year,profit_margin
'''

topCustomerSql = '''
select time_year,cust_key,cust_name,suminvoiceamt,PercentRank
from (SELECT c.cust_key, cust_name,time_year,
    sum(i.invoice_amount) AS suminvoiceamt,
    percent_rank() over(order by(sum(i.invoice_amount))) as PercentRank
   FROM w_invoiceline_f i, w_customer_d c, w_time_d t
   where i.cust_key = c.cust_key and i.invoice_due_date = t.time_id

   GROUP BY c.cust_key,cust_name,time_year
     order by suminvoiceamt DESC) x
     where PercentRank >=
'''
invoiceAmountByProductSql = '''
select sales_class_desc,t.time_year as year, sum(invoice_amount) as "Invoice Amount"
from w_invoiceline_f i  inner join w_sales_class_d s
on s.sales_class_id = i.sales_class_id
inner join w_time_d t on t.time_id = i.invoice_due_date
group by sales_class_desc,t.time_year
order by sales_class_desc,year DESC,"Invoice Amount" DESC

'''
invoiceAmountBylocationSql = '''
select location_name,time_year as year,
sum(invoice_amount) as "Invoice Amount"
from  w_location_d l inner join w_invoiceline_f i
on l.location_id = i.location_id
inner join w_time_d t on t.time_id = i.invoice_due_date
group by location_name,time_year
order by "Invoice Amount" DESC

'''

shipmentDelaysSql = '''
SELECT l.location_name,time_year,
    Round(avg(getbusdaysdiff(x1.first_shipment_date, j.date_promised)),0) AS busdaysdiff
    , dense_rank() over(Partition by time_year order by Round(avg(getbusdaysdiff(x1.first_shipment_date, j.date_promised)),0)) as rank
    FROM w_job_f j,w_location_d l, w_time_d t,
    ( SELECT w_sub_job_f.job_id,
            min(w_job_shipment_f.actual_ship_date) AS first_shipment_date
           FROM w_job_shipment_f,
            w_sub_job_f,
            w_job_f
          WHERE w_sub_job_f.sub_job_id = w_job_shipment_f.sub_job_id AND w_job_f.job_id = w_sub_job_f.job_id AND w_job_shipment_f.actual_ship_date > w_job_f.date_promised
          GROUP BY w_sub_job_f.job_id) x1 
  WHERE  j.job_id = x1.job_id AND j.location_id = l.location_id AND 
  t.time_id=j.date_promised And j.date_promised < x1.first_shipment_date
  group by  time_year,l.location_name
  order by time_year,Rank,busdaysdiff DESC
'''

topSalesAgentSql = '''
select location_name, sales_agent_name, time_year, success_lead
from (
select location_name, sales_agent_name, time_year,count(*) as success_lead,
percent_rank() over(order by count(*)) as PercentRank
from w_lead_f lead 
inner join w_location_d l
on lead.location_id = l.location_id
inner join w_sales_agent_d s 
on lead.sales_agent_id = s.sales_agent_id
inner join w_time_d t on lead.created_date = t.time_id
where lower(lead_success) = 'y'
group by location_name, time_year, sales_agent_name
order by location_name,time_year,success_lead desc ) x
where PercentRank >= 
'''
getShipmentYearsSql='''
select Distinct time_year as year
from w_lead_f le inner join w_time_d t 
on t.time_id = le.created_date
order by year
'''

getInvoiceYearsSql = '''
select Distinct time_year as year
from w_invoiceline_f i inner join w_time_d t 
on t.time_id = i.invoice_due_date
order by year
'''

totalInvoiceSql = '''
select time_year as year,SUM(invoice_amount),count(*)
from w_invoiceline_f i inner join w_time_d t 
on t.time_id = i.invoice_due_date
group by time_year
order by year
'''
locationSql = '''
select distinct location_name from w_location_d;
'''
salesVarianceAnalysisSql = '''
select l.location_name,sales_class_desc,actual.time_year,
Round(((actual_amount / forcast_amount)-1) *100,0)  as "Amount Variance"
from (select location_id,sales_class_id,time_year,sum(actual_units) actual_units, sum(actual_amount) actual_amount
from w_financial_summary_sales_f s , w_time_d t
where s.report_begin_date_id = t.time_id      
group by location_id,time_year,sales_class_id
order by location_id DESC,time_year DESC,sales_class_id DESC) actual,
(select Distinct location_id,sales_class_id,time_year,forcast_unit,forcast_amount
from w_financial_summary_sales_f s, w_time_d t
where s.report_begin_date_id = t.time_id 
order by location_id,sales_class_id,forcast_amount) forcast,
w_location_d l, w_sales_class_d sc
where actual.location_id = forcast.location_id 
and sc.sales_class_id = actual.sales_class_id 
and actual.location_id = l.location_id
and   actual.sales_class_id = forcast.sales_class_id
and   actual.time_year = forcast.time_year
order by time_year,"Amount Variance"
'''
getProductsSql = '''
select sales_class_desc from w_sales_class_d
'''
def connOpen():
    try:
        global conn
        conn = pg.connect(
            host=hostname,
            dbname=database,
            user=username,
            password=pwd,
            port=port_id)
        global cur
        cur = conn.cursor()
        return cur
    except Exception as error:
        print(error)


def connClose():
    global cur
    if cur is not None:
        cur.close()
    global conn
    if conn is not None:
        conn.close()


def TopCustomer(number):
    x = connOpen()
    x.execute(topCustomerSql + str(number / 100))
    res = x.fetchall()
    topCustomerDf = pd.DataFrame(res, columns=['year','cust_key', 'cust_name', 'suminvoiceamt', 'PercentRank'])
    connClose()
    return topCustomerDf

def getshYears():
    x= connOpen()
    x.execute(getShipmentYearsSql)
    res = x.fetchall()
    connClose()
    return res
def getYears():
    x = connOpen()
    x.execute(getInvoiceYearsSql)
    res = x.fetchall()
    connClose()
    return res


def invoiceAmountByProduct():
    x = connOpen()
    x.execute(invoiceAmountByProductSql)
    res = x.fetchall()
    invoiceAmountByProductDf = pd.DataFrame(res, columns=['sales_class_desc', 'year', 'Invoice Amount'])
    connClose()
    return invoiceAmountByProductDf


def invoiceAmountBylocation():
    x = connOpen()
    x.execute(invoiceAmountBylocationSql)
    res = x.fetchall()
    invoiceAmountBylocationDf = pd.DataFrame(res, columns=['location_name', 'year', 'Invoice Amount'])
    connClose()
    return invoiceAmountBylocationDf


def shipmentDelays():
    x = connOpen()
    x.execute(shipmentDelaysSql)
    res = x.fetchall()
    shipmentDelaysDf = pd.DataFrame(res, columns=['location_name', 'year', 'Delays', 'rank'])
    connClose()
    return shipmentDelaysDf


def topSalesAgent(number):
    x = connOpen()
    x.execute(topSalesAgentSql + str(number / 100))
    res = x.fetchall()
    topSalesAgentDf = pd.DataFrame(res, columns=['location', 'agent_name', 'year', 'success_lead'])
    connClose()
    return topSalesAgentDf


def totalInvoice():
    x = connOpen()
    x.execute(totalInvoiceSql)
    res = x.fetchall()
    totalInvoice = pd.DataFrame(res, columns=['year', 'invoice Amount', 'count'])
    connClose()
    return totalInvoice


def getLocations():
    x = connOpen()
    x.execute(locationSql)
    locations = x.fetchall()
    connClose()
    return locations
    connClose()
    return sales


def getProducts():
    x = connOpen()
    x.execute(getProductsSql)
    products = x.fetchall()
    connClose()
    return products


def salesVarianceAnalysis():
    x = connOpen()
    x.execute(salesVarianceAnalysisSql)
    res = x.fetchall()
    sales = pd.DataFrame(res, columns=['location name', 'product', 'year', 'amount variance'])
    return sales



def profitMargin():
    x = connOpen()
    x.execute(profitMargenSql)
    res = x.fetchall()
    profitMarginDf = pd.DataFrame(res, columns=['location_name','year', 'profit_margin'])
    connClose()
    return profitMarginDf