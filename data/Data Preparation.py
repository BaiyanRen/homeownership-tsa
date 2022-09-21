import json
import pandas as pd
import requests
import openpyxl
import nasdaqdatalink
import numpy as np

# load the api key

with open('api.json', 'r') as f:
    api_json = json.load(f)

api = api_json['fred_api_key']


# FRED class to obtain observations
class FRED:
    def __init__(self, token=None):
        self.token = token
        self.url = 'https://api.stlouisfed.org/fred/series/observations' \
                   '?series_id={seriesID}' \
                   '&api_key={token}&file_type=json' \
                   '&observation_start={start}&observation_end={end}&units={units}'

    def set_token(self, token):
        self.token = token

    def get_series(self, seriesID, start, end, units):

        # the url string with the values inserted into it
        url_formatted = self.url.format(seriesID=seriesID, token=self.token, start=start, end=end, units=units)
        response = requests.get(url_formatted)

        if self.token:
            # in the response was successful, extract the data from it
            if response.status_code == 200:
                data = pd.DataFrame(response.json()['observations'])[['date', 'value']] \
                    .assign(date=lambda cols: pd.to_datetime(cols['date'])) \
                    .rename(columns={'value': seriesID})

                return data

            else:
                raise Exception('Bad response from API, status code {}'.format(response.status_code))
        else:
            raise Exception('You did not specify an API Key')


variables = pd.read_excel('/Users/liangquchen/Documents/GitHub/homeownership-tsa/data/metadata.xlsx', 'Sheet1')
fred_vars = variables[variables['API'] == 'FRED']['FRED Code'].reset_index()
fred = FRED()
fred.set_token(api)

start_date = '1979-01-01'
end_date = '2022-03-31'

macro = pd.DataFrame(data=pd.date_range(start_date, end_date, freq='d'), columns=['date'])

# join all the fred data
for index in fred_vars['FRED Code']:
    other_var = fred.get_series(index, start_date, end_date, units='lin')
    macro = macro.merge(other_var, left_on='date', right_on='date', how='left')


# data source: WSJ+kaggle
# kaggle : https://www.kaggle.com/datasets/henryhan117/sp-500-historical-data
# wsj : https://www.wsj.com/market-data/quotes/index/SPX/historical-prices

sp500 = pd.read_csv('SPX.csv')[['Date', 'Close']].assign(Date=lambda cols: pd.to_datetime(cols['Date'])) \
    .rename(columns={'Close': 'SP500', 'Date': 'date'})
    
# merge data
macro = macro.merge(SP500, left_on='date', right_on='date', how='left')

# convert values to float type
macro.loc[:, macro.columns != 'date'] = macro.loc[:, macro.columns != 'date'].astype('float')

# group by quarter
macro_q = macro.groupby(pd.Grouper(key='date', freq='Q')).agg(np.nanmean).reset_index()

# add one day to match project date
macro_q["date"] = pd.DatetimeIndex(macro_q["date"])+pd.DateOffset(1)

# change the format to YYYY-MM-DD as the project date
macro_q["date"] = macro_q["date"].dt.strftime("%Y-%m-%d")

# read project data
hosr = pd.read_csv("Homeownership Rate-1.csv", skiprows = 6) 
ir = pd.read_csv("Interest Rate.csv")
msp = pd.read_csv("Median Sales Price of Houses Sold by Quarter.csv")
gdp = pd.read_csv("Real GDP by Quarter.csv")

# rename the homeownership rate
hosr.rename(columns = {"Value":"hosr"}, inplace=True)

# merge project data
project_data = ir.merge(msp, on="DATE")
project_data = project_data.merge(gdp, on="DATE")

# merge macro data with project data
var = macro_q.merge(project_data, left_on = "date", right_on = "DATE")

# convert to year and period, eg: 2000, Q1
def convert_yq(dates):
  years = []
  quarters = []
  quarter_dict={"04":"Q1","07":"Q2","10":"Q3","01":"Q4"}

  for date in dates:
    year = int(date.split("-")[0])
    quarter = quarter_dict[date.split("-")[1]]
    quarters.append(quarter)
    if quarter == "Q4":
      year = year -1
    years.append(year)
    
  return years, quarters

var["year"],var["quarter"] = convert_yq(var["date"])
var["year"] = var["year"].astype(int)

# convert homeownership data to year+quarter
hosr["quarter"]= hosr["Period"].str.split("-",expand=True)[0]
hosr["year"]= hosr["Period"].str.split("-",expand=True)[1]
hosr["year"] = hosr["year"].astype(int)


# merge homeownership rate data with variables
hosr_var = pd.merge(hosr,var,on=["year","quarter"])

# remove NA and duplicate columns
hosr_var = hosr_var.dropna()
hosr_var = hosr_var.drop(["Period","DATE"], axis = 1)

# shift column orders
cols = ['date', 'year', 'quarter', 'hosr', 'FEDFUNDS', 'MSPUS','GDPC1','PAYEMS', 
        'CPIAUCSL', 'UNRATE','UMCSENT', 'DSPIC96', 'PERMIT', 'ICSA', 'SP500']
hosr_var = hosr_var[cols]

# save to a csv file
hosr_var.to_csv('hosr_var.csv')

