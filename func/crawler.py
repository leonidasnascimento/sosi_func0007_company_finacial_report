import urllib3
import requests
import re

from datetime import datetime
from .model.company import (Company) 
from .parser import Parser
from bs4 import (BeautifulSoup, Tag)
from typing import List

class Crawler:
    #Properties
    url_key_statistics: str = ''
    url_gross_debit_over_ebitida: str = ''
    url_return_equity_dividend_yield: str

    def __init__(self, _url_key_statistics: str, _url_gross_debit_over_ebitida: str, _url_return_equity_dividend_yield: str):
        self.url_key_statistics = _url_key_statistics
        self.url_gross_debit_over_ebitida = _url_gross_debit_over_ebitida
        self.url_return_equity_dividend_yield = _url_return_equity_dividend_yield        
        pass

    def get_data(self, _stock_code: str) -> Company:
        comp_obj: Company = Company(_stock_code)
        
        headers = {
            'upgrade-insecure-requests': "1",
            'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36",
            'accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            'cache-control': "no-cache",
            'postman-token': "146ba02b-dc25-fb1a-9fbc-a8df1248db26"
        }

        url: str = ""
        page: BeautifulSoup = None
        avg3MonthsVolume: str = ""
        avg10DaysVolume: str = ""
        roe: str = ""
        grossDebitEbitida: str = ""
        payoutRatio: str = ""
        roe_avg5yrs: str = ""
        dy: str = ""
        dy_avg5yrs: str = ""
        valuation: str = ""

        ######################
        ##  KEY STATISTICS  ##
        ######################
        url = self.url_key_statistics.format(_stock_code)
        res = requests.get(url, headers=headers)
        page = BeautifulSoup(res.content)

        if page:
            pgAvgVolume3Mos: Tag = page.find(text=re.compile('^Volume Médio \(3 meses\)'))
            pgAvgVolume10Days: Tag = page.find(text=re.compile('^Volume Médio \(10 dias\)'))
            pRoe: Tag = page.find(text=re.compile('^Retorno Sobre o Patrimônio Líquido'))
            pPayoutRatio: Tag = page.find(text=re.compile('^Índice de Payout'))
            pValuation: Tag = page.find(text=re.compile('^Valor da Empresa'))

            if pgAvgVolume10Days:
                avg10DaysVolume = pgAvgVolume10Days.parent.parent.find_next_sibling("td").get_text()
            
            if pgAvgVolume3Mos:
                avg3MonthsVolume = pgAvgVolume3Mos.parent.parent.find_next_sibling("td").get_text()

            if pRoe:
                roe = pRoe.parent.parent.find_next_sibling("td").get_text()

            if pPayoutRatio:
                payoutRatio = pPayoutRatio.parent.parent.find_next_sibling("td").get_text()
        
            if pValuation:
                valuation = pValuation.parent.parent.find_next_sibling("td").get_text()

        ################################
        ##  GROSS DEBIT OVER EBITIDA  ##
        ################################
        url = self.url_gross_debit_over_ebitida.format(_stock_code)
        res = requests.get(url, headers=headers)
        page = BeautifulSoup(res.content)

        if page:
            pGrossDebitEbitida: Tag = page.find(text=re.compile('^Dívida Líquida \/ EBITDA'))

            if not (pGrossDebitEbitida is None):
                grossDebitEbitida = pGrossDebitEbitida.parent.find_next_sibling("td").get_text()

        #########################################
        ##  Return On Equity & Dividend Yield  ##
        #########################################
        url = self.url_return_equity_dividend_yield.format(_stock_code)
        res = requests.get(url, headers=headers)
        page = BeautifulSoup(res.content)

        if page:
            pRoe_avg5yrs = page.find("td", text=re.compile('Return on Equity - 5 Yr\. Avg\.'))
            pDy = page.find("td", text=re.compile('Dividend Yield'))
            pDy_avg5yrs = page.find("td", text=re.compile('Dividend Yield - 5 Year Avg'))

            if not (pRoe_avg5yrs is None):
                roe_avg5yrs = str(pRoe_avg5yrs.find_next_sibling("td").get_text()).replace(",", "")
            
            if not (pDy is None):
                dy = str(pDy.find_next_sibling("td").get_text()).replace(",", "")
            
            if not (pDy_avg5yrs is None):
                dy_avg5yrs = str(pDy_avg5yrs.find_next_sibling("td").get_text()).replace(",", "")

        # filling the properties
        comp_obj.AvgVolume10Days = Parser.ParseOrdinalNumber(avg10DaysVolume)
        comp_obj.AvgVolume3Months = Parser.ParseOrdinalNumber(avg3MonthsVolume)
        comp_obj.ReturnOnEquity = Parser.ParseFloat(roe)
        comp_obj.GrossDebitOverEbitida = Parser.ParseFloat(grossDebitEbitida) / 100 
        comp_obj.PayoutRatio = Parser.ParseFloat(payoutRatio)
        comp_obj.Valuation = Parser.ParseOrdinalNumber(valuation)
        comp_obj.ReturnOnEquity_5yrAvg = float(roe_avg5yrs if roe_avg5yrs != "" and roe_avg5yrs != "--" and roe_avg5yrs != "-" else "0.00") / 100
        comp_obj.DividendYeld = float(dy if dy != "" and dy != "--" and dy != "-" else "0.00") / 100
        comp_obj.DividendYeld_5yrAvg = float(float(dy_avg5yrs if dy_avg5yrs != "" and dy_avg5yrs != "--" and dy_avg5yrs != "-" else "0.00")) / 100

        return comp_obj