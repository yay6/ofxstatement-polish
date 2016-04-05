import csv
import re

from ofxstatement import statement
from ofxstatement.parser import CsvStatementParser
from ofxstatement.plugin import Plugin
from ofxstatement.statement import Statement, recalculate_balance


class PaypalPlugin(Plugin):
    """Paypal (www.paypal.com) CSV history plugin
    """

    def get_parser(self, filename):
        encoding = self.settings.get('charset', 'cp1250')
        f = open(filename, "r", encoding=encoding)
        parser = PaypalParser(f)
        parser.statement.currency = self.settings.get('currency', 'PLN')
        parser.statement.account_id = self.settings.get('account', '')
        parser.statement.bank_id = self.settings.get('bank', 'PPAL')
        return parser


class PaypalParser(CsvStatementParser):
    mappings = {"date": 0,
                "amount": 7,
                "id": 12 }
    
    encoding = 'windows-1250'
    date_format = "%d-%m-%Y"
   
    fields = ["Data", "Godzina","Strefa czasowa", "Imię i nazwisko (nazwa)",
              "Typ", "Status", "Waluta", "Brutto", "Opłata", "Netto", 
              "Z adresu e-mail", "Na adres e-mail",
              "Numer identyfikacyjny transakcji", "Status kontrahenta",
              "Status adresu", "Nazwa przedmiotu", "Identyfikator przedmiotu",
              "Koszt wysyłki oraz koszty manipulacyjne", "Kwota ubezpieczenia",
              "Podatek od sprzedaży", "Nazwa opcji 1", "Wartość opcji 1",
              "Nazwa opcji 2", "Wartość opcji 2", "Witryna aukcji", 
              "Nazwa kupującego", "Adres URL przedmiotu", "Data zamknięcia",
              "Pomocniczy numer identyfikacyjny transakcji", "Numer faktury",
              "Numer niestandardowy", "Identyfikator potwierdzenia", "Saldo",
              "Adres wiersz 1", "Adres wiersz 2/dzielnica/osiedle", "Miejscowość",
              "Stan/prowincja/województwo/region/terytorium/prefektura/republika",
              "Kod pocztowy", "Kraj", "Numer telefonu kontaktowego"]
    
    def parse(self):
        stmt = super(PaypalParser, self).parse()
        recalculate_balance(stmt)
        return stmt
    
    def split_records(self):
        return csv.reader(self.fin, delimiter=',', quotechar='"')
    
    def parse_record(self, line):
        
        if self.cur_record == 1:
            return
        
        if line[6] != self.statement.currency:
            return
              
        sl = super(PaypalParser, self).parse_record(line)

        d = dict(zip(self.fields, line))
        p = [d[k] for k in ("Typ", "Identyfikator przedmiotu", "Nazwa przedmiotu")]
        m = [d[k] for k in ("Z adresu e-mail", "Na adres e-mail")]
        m += line[26:31] + line[33:35] + line[36:39]
        sl.payee = ' - '.join([e for e in p if e])
        sl.memo  = ' '.join([e for e in m if e])
        
        if sl.amount < 0:
            sl.trntype = "DEBIT"
        elif 0 < sl.amount:
            sl.trntype = "CREDIT"

        return sl
    
    def parse_float(self, value):
        return super(PaypalParser, self).parse_float(re.sub("[ .a-zA-Z]", "", value).replace(",", "."))