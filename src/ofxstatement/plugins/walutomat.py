import csv
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement


class WalutomatPlugin(Plugin):
    """Walutomat (www.walutomat.pl) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'utf8')
        f = open(filename, "r", encoding=encoding)
        parser = WalutomatParser(f)
        parser.statement.currency = self.settings.get('currency', '')
        parser.statement.bank_id = self.settings.get('bank', 'walutomat')
        parser.statement.account_id = self.settings.get('account', '')
        parser.swap_payee_and_memo = self.settings.get('swap-payee-and-memo', True)
        return parser

class WalutomatParser(CsvStatementParser):
    mappings = {"id": 0,
                "date": 1,
                "amount": 2,
                "memo": 5 }
    
    date_format = "%Y-%m-%d %H:%M:%S"
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=';', quotechar='"')
    
    def parse_record(self, line):
        if self.cur_record == 1:
            return None
        if not self.statement.currency:
            self.statement.currency = line[4]
            if not self.statement.account_id:
                self.statement.account_id = line[4]
        if self.statement.currency != line[4]:
            return None
            
        sl = super(WalutomatParser, self).parse_record(line)
        
        if getattr(self, 'swap_payee_and_memo', False):
            sl.memo, sl.payee = sl.payee, sl.memo

        return sl
    
    def parse_float(self, value):
        return super(WalutomatParser, self).parse_float(re.sub("[ ,a-zA-Z]", "", value))
    