import csv
from datetime import datetime
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement


class BankSMARTPlugin(Plugin):
    """Bank SMART (www.banksmart.pl) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'utf8')
        f = open(filename, "r", encoding=encoding)
        parser = BankSMARTParser(f)
        parser.statement.currency = self.settings.get('currency', '')
        parser.statement.bank_id = self.settings.get('bank', 'PBPBPLPWFMB')
        parser.statement.account_id = self.settings.get('account', '')
        parser.swap_payee_and_memo = self.settings.get('swap-payee-and-memo', True)
        return parser

class BankSMARTParser(CsvStatementParser):
    mappings = {"date_user": 0,
                "date": 1,
                "payee": 2,
                "memo": 3,
                "amount": 4 }
    
    date_format = "%Y-%m-%d"
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=',', quotechar='"')
    
    def parse_record(self, line):
        if self.cur_record == 1:
            return None
        if not self.statement.currency:
            self.statement.currency = line[4].split()[-1]
        if not self.statement.account_id:
            self.statement.account_id = line[6].split()[-1]
            
        sl = super(BankSMARTParser, self).parse_record(line)
        sl.date_user = datetime.strptime(sl.date_user, self.date_format)
        
        sl.id = statement.generate_transaction_id(sl)
        
        if getattr(self, 'swap_payee_and_memo', False):
            sl.memo, sl.payee = sl.payee, sl.memo

        return sl
    
    def parse_float(self, value):
        return super(BankSMARTParser, self).parse_float(re.sub("[ ,a-zA-Z]", "", value))
    