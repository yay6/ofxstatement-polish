import csv
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, StatementLine, recalculate_balance


class DBPLPlugin(Plugin):
    """Deutsche Bank Polska (www.deutschebank.pl) bank CSV history plugin 
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'cp1250')
        f = open(filename, "r", encoding=encoding)
        parser = DBPLParser(f)
        parser.statement.currency = self.settings.get('currency', 'PLN')
        parser.statement.account_id = self.settings.get('account', '')
        parser.statement.bank_id = self.settings.get('bank', 'DEUTPLPK')
        return parser

class DBPLParser(CsvStatementParser):
    mappings = {"date": 0,
                "amount": 3}
    
    date_format = "%Y-%m-%d"
    regex = re.compile('^(.*);.* (Adresat|Nadawca): (.*) Treść:(.*)')
    
    def parse(self):
        stmt = super(DBPLParser, self).parse()
        recalculate_balance(stmt)
        return stmt
        
    def split_records(self):
        return csv.reader(self.fin, delimiter=';', quotechar='"')
    
    def parse_record(self, line):
        
        if not self.statement.currency:
            self.statement.currency = line[4]
        
        sl = super(DBPLParser, self).parse_record(line)
        
        opis = line[2]
        for n in (242, 179, 161, 132, 80):
            if n < len(opis) and opis[n] == ' ':
                #print(str(n) + ": " + opis[:n] + "~" + opis[n+1:])
                opis = opis[:n] + opis[n+1:]
        
        opis = re.sub("\s+", " ", opis).strip()
        m = self.regex.match(opis)
        if m:
            sl.payee = ' - '.join([m.group(1), m.group(4)])
            sl.memo = m.group(3)
        else:
            sl.payee = opis
        
        sl.id = statement.generate_transaction_id(sl)
        
        if opis.startswith("PRZELEW"):
            sl.trntype = "XFER"
        elif opis.startswith("OPERACJA KARTĄ Treść: Wypłata"):
            sl.trntype = "ATM"
        elif opis.startswith("OPERACJA KARTĄ Treść: Zakup"):
            sl.trntype = "DEBIT"
        elif opis.startswith("Podatek"):
            sl.trntype = "FEE"
        elif opis.startswith("OPŁAT"):
            sl.trntype = "SRVCHG"
        elif opis.startswith("Kapitalizacja"):
            sl.trntype = "INT"
   
        return sl
    
    def parse_float(self, value):
        return super(DBPLParser, self).parse_float(re.sub("[ .a-zA-Z]", "", value).replace(",", "."))