import csv
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine, recalculate_balance


class MillenniumPlugin(Plugin):
    """Millennium (www.bankmillennium.pl) bank CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'utf8')
        f = open(filename, "r", encoding=encoding)
        parser = MillenniumParser(f)
        parser.statement.currency = self.settings.get('currency', 'PLN')
        parser.statement.account_id = self.settings.get('account', '')
        parser.statement.bank_id = self.settings.get('bank', 'BIGBPLPW')
        return parser

class MillenniumParser(CsvStatementParser):
    mappings = {"date": 1}
    
    date_format = "%Y-%m-%d"
    
    def parse(self):
        stmt = super(MillenniumParser, self).parse()
        recalculate_balance(stmt)
        return stmt
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=',', quotechar='"')
    
    def parse_record(self, line):
        
        if self.cur_record < 2:
            return
        acc = re.sub("\s", "", line[0]) 
        if not self.statement.account_id:
            self.statement.account_id = acc
        elif acc != self.statement.account_id:
            return
        
        sl = super(MillenniumParser, self).parse_record(line)
        
        sl_type = line[3]
        sl_acc_no = re.sub("\s|[a-zA-Z]", "", line[4])
        sl_name = line[5]
        sl_desc = line[6]
        sl_charge = line[7]
        sl_credit = line[8]
        #sl_saldo = line[9]
        
        if sl_charge:
            sl.amount = self.parse_float(sl_charge)
        elif sl_credit:
            sl.amount = self.parse_float(sl_credit)
            
        if not sl.amount:
            raise ValueError("Could not parse transaction amount")
        
        sl.memo = re.sub("\s+", " ", ' '.join([sl_acc_no, sl_name]).strip())
        sl.payee = re.sub("\s+", " ", ' - '.join([sl_type, sl_desc]).strip())
        
        if sl_type.startswith("PRZELEW"):
            sl.trntype = "XFER"
        elif sl_type.startswith("WYPŁATA"):
            sl.trntype = "ATM"
        elif sl_type.startswith("TRANSAKCJA KARTĄ"):
            sl.trntype = "DEBIT"
        elif sl_type == "OBCIĄŻENIE":
            if sl_desc.startswith("PODATEK"):
                sl.trntype = "FEE"
            elif sl_desc.startswith("OPŁATA"):
                sl.trntype = "SRVCHG"
            else:
                sl.trntype = "DEBIT"
        elif sl_type == "UZNANIE":
            if sl_desc.startswith("KAPITALIZACJA"):
                sl.trntype = "INT"
            else:
                sl.trntype = "CREDIT"
        
        sl.id = statement.generate_transaction_id(sl)
        
        return sl
    