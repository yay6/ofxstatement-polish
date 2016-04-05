import csv
from datetime import datetime
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement


class MBankPLPlugin(Plugin):
    """Polish mBank (www.mbank.pl) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'cp1250')
        f = open(filename, "r", encoding=encoding)
        parser = MBankPLParser(f)
        parser.statement.bank_id = self.settings.get('bank', 'BREXPLPWMUL')
        return parser


class MBankPLParser(CsvStatementParser):
    mappings = {"date_user":0,
                "date": 1,
                "amount": 6, }
    
    date_format = "%Y-%m-%d"
    
    def parse(self):
        self.parsing_header = True
        self.last_line = None
        return super(MBankPLParser, self).parse()
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=';', quotechar='"')
    
    def parse_record(self, line):
        
        if self.parsing_header:
            return self.parse_header(line)
        
        if len(line) != 9:
            return None
        
        # footer
        if line[6] == "#Saldo końcowe":
            self.statement.end_balance = self.parse_float(line[7])
            return None
        
        sl = super(MBankPLParser, self).parse_record(line)
        sl.date_user = datetime.strptime(sl.date_user, self.date_format)

        # account number and name
        sl.memo = re.sub("\s+", " ", ' '.join([line[5].strip("'"), line[4]]))
        
        # type - description
        sl.payee = re.sub("\s+", " ", ' - '.join(line[2:4]))

        # generate transaction id out of available data
        sl.id = statement.generate_transaction_id(sl)
        
        if line[2].startswith("PRZ"):
            sl.trntype = "XFER"
        elif line[2].startswith("WYPŁATA"):
            sl.trntype = "ATM"
        elif line[2].startswith("ZAKUP"):
            sl.trntype = "DEBIT"
        elif line[2].startswith("PODATEK"):
            sl.trntype = "FEE"
        elif line[2].startswith("OPŁATA"):
            sl.trntype = "SRVCHG"
        elif line[2].startswith("KAPITALIZACJA"):
            sl.trntype = "INT"

        return sl
    
    def parse_float(self, value):
        return super(MBankPLParser, self).parse_float(re.sub("[ .a-zA-Z]", "", value).replace(",", "."))
    
    def parse_header(self, line):
        
        stmt = self.statement
        last = self.last_line
        
        if not line:
            pass
        elif line[0] == "Łącznie":
            stmt.total_amount = self.parse_float(line[2])
        elif line[0] == "#Saldo początkowe":
            stmt.start_balance = self.parse_float(line[1])
        elif line[0] == "#Data operacji":
            stmt.end_balance = stmt.start_balance + stmt.total_amount
            self.parsing_header = False
        elif not last:
            pass
        elif last[0] == "#Za okres:":
            stmt.start_date = datetime.strptime(line[0], "%d.%m.%Y")
            stmt.end_date = datetime.strptime(line[1], "%d.%m.%Y")
        elif last[0] == "#Waluta":
            stmt.currency = line[0].strip()
        elif last[0] == "#Numer rachunku":
            stmt.account_id = "PL" + line[0].replace(" ", "")

        self.last_line = line
        
        return None