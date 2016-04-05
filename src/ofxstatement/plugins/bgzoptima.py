import csv
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement


class BGZOptimaPlugin(Plugin):
    """Polish BGŻ Optima (www.bgzoptima.pl) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'utf16')
        f = open(filename, "r", encoding=encoding)
        parser = BGZOptimaParser(f)
        parser.statement.currency = self.settings.get('currency', 'PLN')
        parser.statement.bank_id = self.settings.get('bank', 'GOPZPLPW')
        parser.swap_payee_and_memo = self.settings.get('swap-payee-and-memo', True)
        return parser

class BGZOptimaParser(CsvStatementParser):
    mappings = {"id": 0,
                "date": 1,
                "amount": 3, }
    
    date_format = "%d-%m-%Y"
    
    def split_records(self):
        return csv.reader(self.fin, delimiter='\t', quotechar='"')
    
    def parse_record(self, line):
        if self.cur_record == 1:
            self.statement.account_id = "PL" + line[1].strip(" ")
            return None
        elif self.cur_record == 2:
            return None
        
        sl = super(BGZOptimaParser, self).parse_record(line)

        if ''.join(line[7:10]).strip():
            sl.memo = ' - '.join(filter(None, [line[2]] + line[9:10]))
            sl.payee = ' '.join(filter(None, line[6:8] + [line[10]]))
        else:
            sl.memo = ' - '.join(filter(None, [line[2], line[10]]))
            sl.payee = ' '.join(filter(None, line[6:8]))
        
        
        if getattr(self, 'swap_payee_and_memo', False):
            sl.memo, sl.payee = sl.payee, sl.memo
        
        if line[2].startswith("Przelew"):
            sl.trntype = "XFER"
        elif line[2].startswith("Podatek"):
            sl.trntype = "FEE"
        elif line[2].startswith("Odsetki"):
            sl.trntype = "INT"
        elif line[2].startswith("Zasilenie Lokaty Terminowej"):
            sl.trntype = "DEP"

        return sl
    
    def parse_float(self, value):
        return super(BGZOptimaParser, self).parse_float(re.sub("[ .a-zA-Z]", "", value).replace(",", "."))
    