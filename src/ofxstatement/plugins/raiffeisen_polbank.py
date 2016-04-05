import csv
from datetime import datetime
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement


class RaiffeisenPolbankPlugin(Plugin):
    """Raiffeisen-Polbank (www.raiffeisenpolbank.com) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'cp1250')
        f = open(filename, "r", encoding=encoding)
        parser = RaiffeisenPolbankParser(f)
        parser.statement.bank_id = self.settings.get('bank', 'RCBWPLPW')
        parser.statement.account_id = self.settings.get('account', '')
        parser.statement.currency = self.settings.get('currency', 'PLN')
        parser.swap_payee_and_memo = self.settings.get('swap-payee-and-memo', True)
        return parser


class RaiffeisenPolbankParser(CsvStatementParser):
    mappings = {"date_user":0,
                "date": 1,
                "memo": 2,
                "payee": 3,
                "amount": 5, }
    
    date_format = "%d-%m-%Y"
    
    def parse(self):
        self.parsing_header = True
        self.last_line = None
        return super(RaiffeisenPolbankParser, self).parse()
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=';')
    
    def parse_record(self, line):
        if self.cur_record == 1:
            return None
        
        if not getattr(self.statement, 'currency', None):
            self.statement.currency = line[6]
        
        sl = super(RaiffeisenPolbankParser, self).parse_record(line)
        sl.date_user = datetime.strptime(sl.date_user, self.date_format)

        if line[4]:
            sl.memo += " - " + line[4]  

        sl.id = statement.generate_transaction_id(sl)
        
        if line[2].startswith("Polecenie przelewu"):
            sl.trntype = "XFER"
        elif line[2].startswith("Podatek"):
            sl.trntype = "FEE"
        elif line[2].startswith("Opłata"):
            sl.trntype = "SRVCHG"
        elif line[2].startswith("Odsetki"):
            sl.trntype = "INT"
        else:
            sl.trntype = "XFER"

        if getattr(self, 'swap_payee_and_memo', True):
            sl.memo, sl.payee = sl.payee, sl.memo
            
        return sl
    
    def parse_float(self, value):
        return super(RaiffeisenPolbankParser, self).parse_float(re.sub("[ .a-zA-Z]", "", value).replace(",", "."))