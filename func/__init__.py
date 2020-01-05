import datetime
import logging
import azure.functions as func
import json
import pathlib
import threading
import time
import array
import requests

from .crawler import Crawler
from .model.company import Company
from typing import List
from dateutil.relativedelta import relativedelta
from configuration_manager.reader import reader

SETTINGS_FILE_PATH = pathlib.Path(
    __file__).parent.parent.__str__() + "//local.settings.json"

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    try:
        logging.info("Timer job 'sosi_func0007_company_statistics' has begun")

        config_obj: reader = reader(SETTINGS_FILE_PATH, 'Values')
        stock_code_list_service_url: str = config_obj.get_value("stock_code_list_service_url")
        post_service_url: str = config_obj.get_value("post_service_url")
        url_key_statistics: str = config_obj.get_value("url_key_statistics")
        url_gross_debit_over_ebitida: str = config_obj.get_value("url_gross_debit_over_ebitida")
        url_return_equity_dividend_yield: str = config_obj.get_value("url_return_equity_dividend_yield")
        
        # Getting stock code list
        response = requests.request("GET", stock_code_list_service_url)
        stk_codes = json.loads(response.text)
        thread_lst: List[threading.Thread] = []
        
        for code in stk_codes:
            logging.info(code['stock'])
            
            process_crawling(code['stock'], url_key_statistics, url_gross_debit_over_ebitida, url_return_equity_dividend_yield, post_service_url)

            # t_aux: threading.Thread = threading.Thread(target=process_crawling, args=(code['stock'], url_key_statistics, url_gross_debit_over_ebitida, url_return_equity_dividend_yield))            
            # thread_lst.append(t_aux)
        
            # t_aux.start()
            pass
            
        # Wait 'till all threads are done
        for thread in thread_lst:
            if thread and thread.is_alive():    
                thread.join()

        logging.info("Timer job is done. Waiting for the next execution time")

        pass
    except Exception as ex:
        error_log = '{} -> {}'
        logging.exception(error_log.format(utc_timestamp, str(ex)))
        pass
    pass

def process_crawling(stock_code: str, url_key_statistics: str, url_gross_debit_over_ebitida: str, url_return_equity_dividend_yield: str, post_service_url: str):
    try:
        crawler_obj: Crawler = Crawler(url_key_statistics, url_gross_debit_over_ebitida, url_return_equity_dividend_yield)
        company_data: Company = crawler_obj.get_data(stock_code)

        if company_data:
            json_obj = json.dumps(company_data.__dict__, default=lambda o: o.__dict__)

            threading.Thread(target=post_data, args=(post_service_url, json_obj)).start()                
            pass
    except Exception as e:
        logging.error(e)
        pass
    pass

def post_data(url, json):
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'content-length': str(len(str(json).encode('utf-8')))
    }

    requests.request("POST", url, data=json, headers=headers)
    pass