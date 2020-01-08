class Company():
    code: ""
    avgVolume3Months: 0.00
    avgVolume10Days: 0.00
    returnOnEquity: 0.00
    grossDebitOverEbitida: 0.00
    returnOnEquity_5yrAvg: 0.00
    payoutRatio: 0.00
    dividendYeld: 0.00
    dividendYeld_5yrs: 0.00
    valuation: 0.00 
    dt_processing: ""  
    
    def __init__(self, _code: str, _dt_processing: str):
        self.code = _code
        self.dt_processing = _dt_processing
        pass
    pass