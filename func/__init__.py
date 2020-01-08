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
from .model.status_processing import StatusProcessing
from typing import List
from dateutil.relativedelta import relativedelta
from configuration_manager.reader import reader

SETTINGS_FILE_PATH = pathlib.Path(
    __file__).parent.parent.__str__() + "//local.settings.json"

def main(req: func.HttpRequest) -> func.HttpResponse:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    try:
        logging.info("Timer job 'sosi_func0007_company_statistics' has begun")

        config_obj: reader = reader(SETTINGS_FILE_PATH, 'Values')
        post_service_url: str = config_obj.get_value("post_service_url")
        url_key_statistics: str = config_obj.get_value("url_key_statistics")
        url_gross_debit_over_ebitida: str = config_obj.get_value("url_gross_debit_over_ebitida")
        url_return_equity_dividend_yield: str = config_obj.get_value("url_return_equity_dividend_yield")
        
        # Messages
        ERR_CODE_REQUIRED = "Stock code is required"
        ERR_STOCK_NOT_PROCESSED = "{} was not processed"
        SUCCESS_STOCK_PROCESSED = "{} processed"

        if (not req) or len(req.params) == 0 or (not req.params.get("code")):
            logging.error(ERR_CODE_REQUIRED)
            return func.HttpResponse(body=json.dumps(StatusProcessing(False, ERR_CODE_REQUIRED).__dict__), status_code=204)
            
        stock_code: str = str(req.params.get("code"))

        crawler_obj: Crawler = Crawler(url_key_statistics, url_gross_debit_over_ebitida, url_return_equity_dividend_yield, utc_timestamp)
        company_data: Company = crawler_obj.get_data(stock_code)

        if company_data:
            json_obj = json.dumps(company_data.__dict__, default=lambda o: o.__dict__)

            # TODO: At the time, we're not caring about the microservice response here 
            threading.Thread(target=post_data, args=(post_service_url, json_obj)).start()                
            return func.HttpResponse(body=json.dumps(StatusProcessing(True, SUCCESS_STOCK_PROCESSED.format(stock_code)).__dict__), status_code=200)
        else:
            logging.warn(ERR_STOCK_NOT_PROCESSED.format(stock_code))
            return func.HttpResponse(body=json.dumps(StatusProcessing(False, ERR_STOCK_NOT_PROCESSED.format(stock_code)).__dict__), status_code=500)    
        pass
    except Exception as ex:
        error_log = '{} -> {}'.format(utc_timestamp, str(ex))
        logging.exception(error_log)
        return func.HttpResponse(body=json.dumps(StatusProcessing(False, error_log, ex).__dict__), status_code=500)
    pass

def post_data(url, json):    
    headers = {
        'content-type': "application/json",
        'cache-control': "no-cache",
        'content-length': str(len(str(json).encode('utf-8')))
    }

    requests.request("POST", url, data=json, headers=headers)
    pass