from _pydecimal import Context, Decimal as pyDecimal
from decimal import Decimal as CDecimal
from enum import Enum
from numbers import Rational
from typing import NamedTuple, Optional, Sequence, Union


# Specifically need the python implementation of decimal instead of the C/binary implementation for inheritance

ComparableType = Union[pyDecimal, CDecimal, float, Rational, "Money"]
OperableType = Union[pyDecimal, CDecimal, int, "Money"]
SafeComparableType = Union[pyDecimal, float, Rational, "Money"]
SafeOperableType = Union[pyDecimal, int, "Money"]

class Currency(NamedTuple):
    """Follows ISO 4217"""

    code: str
    num: int
    conventional_decimals: Optional[int]
    name: str
    symbol: Optional[str]

class Currencies(Enum):
    AED = Currency(code="AED", num=784, conventional_decimals=2, name="United Arab Emirates dirham", symbol=None)
    AFN = Currency(code="AFN", num=971, conventional_decimals=2, name="Afghan afghani", symbol="\u060b")
    ALL = Currency(code="ALL", num=8, conventional_decimals=2, name="Albanian lek", symbol="Lek")
    AMD = Currency(code="AMD", num=51, conventional_decimals=2, name="Armenian dram", symbol="\u058f")
    AOA = Currency(code="AOA", num=973, conventional_decimals=2, name="Angolan kwanza", symbol="Kz")
    ARS = Currency(code="ARS", num=32, conventional_decimals=2, name="Argentine peso", symbol="Arg$")
    AUD = Currency(code="AUD", num=36, conventional_decimals=2, name="Australian dollar", symbol="A$")
    AWG = Currency(code="AWG", num=533, conventional_decimals=2, name="Aruban florin", symbol="\u0192")
    AZN = Currency(code="AZN", num=944, conventional_decimals=2, name="Azerbaijani manat", symbol="\u20bc")
    BAM = Currency(code="BAM", num=977, conventional_decimals=2, name="Bosnia and Herzegovina convertible mark", symbol="KM")
    BBD = Currency(code="BBD", num=52, conventional_decimals=2, name="Barbados dollar", symbol="Bds$")
    BDT = Currency(code="BDT", num=50, conventional_decimals=2, name="Bangladeshi taka", symbol="\u09F3")
    BGN = Currency(code="BGN", num=975, conventional_decimals=2, name="Bulgarian lev", symbol="lev")
    BHD = Currency(code="BHD", num=48, conventional_decimals=3, name="Bahraini dinar", symbol="BD")
    BIF = Currency(code="BIF", num=108, conventional_decimals=0, name="Burundian franc", symbol="FBu")
    BMD = Currency(code="BMD", num=60, conventional_decimals=2, name="Bermudian dollar", symbol="Ber$")
    BND = Currency(code="BND", num=96, conventional_decimals=2, name="Brunei dollar", symbol="B$")
    BOB = Currency(code="BOB", num=68, conventional_decimals=2, name="Boliviano", symbol="Bs")
    BOV = Currency(code="BOV", num=984, conventional_decimals=2, name="Bolivian Mvdol (funds code)", symbol=None)
    BRL = Currency(code="BRL", num=986, conventional_decimals=2, name="Brazilian real", symbol="R$")
    BSD = Currency(code="BSD", num=44, conventional_decimals=2, name="Bahamian dollar", symbol="B$")
    BTN = Currency(code="BTN", num=64, conventional_decimals=2, name="Bhutanese ngultrum", symbol="Nu")
    BWP = Currency(code="BWP", num=72, conventional_decimals=2, name="Botswana pula", symbol="P")
    BYN = Currency(code="BYN", num=933, conventional_decimals=2, name="Belarusian ruble", symbol="R")
    BZD = Currency(code="BZD", num=84, conventional_decimals=2, name="Belize dollar", symbol="BZ$")
    CAD = Currency(code="CAD", num=124, conventional_decimals=2, name="Canadian dollar", symbol="C$")
    CDF = Currency(code="CDF", num=976, conventional_decimals=2, name="Congolese franc", symbol="FC")
    CHE = Currency(code="CHE", num=947, conventional_decimals=2, name="WIR franc", symbol=None)
    CHF = Currency(code="CHF", num=756, conventional_decimals=2, name="Swiss franc", symbol="SFr")
    CHW = Currency(code="CHW", num=948, conventional_decimals=2, name="WIR franc", symbol=None)
    CLF = Currency(code="CLF", num=990, conventional_decimals=4, name="Unidad de Fomento (funds code)", symbol=None)
    CLP = Currency(code="CLP", num=152, conventional_decimals=0, name="Chilean peso", symbol="Ch$")
    CNY = Currency(code="CNY", num=156, conventional_decimals=2, name="Renminbi", symbol="CN\u00a5")
    COP = Currency(code="COP", num=170, conventional_decimals=2, name="Colombian peso", symbol="Col$")
    COU = Currency(code="COU", num=970, conventional_decimals=2, name="Unidad de Valor Real (UVR) (funds code)", symbol=None)
    CRC = Currency(code="CRC", num=188, conventional_decimals=2, name="Costa Rican colon", symbol="\u20a1")
    CUP = Currency(code="CUP", num=192, conventional_decimals=2, name="Cuban peso", symbol="Cu$")
    CVE = Currency(code="CVE", num=132, conventional_decimals=2, name="Cape Verdean escudo", symbol=None)
    CZK = Currency(code="CZK", num=203, conventional_decimals=2, name="Czech koruna", symbol="K\u010D")
    DJF = Currency(code="DJF", num=262, conventional_decimals=0, name="Djiboutian franc", symbol="DF")
    DKK = Currency(code="DKK", num=208, conventional_decimals=2, name="Danish krone", symbol="kr")
    DOP = Currency(code="DOP", num=214, conventional_decimals=2, name="Dominican peso", symbol="RD$")
    DZD = Currency(code="DZD", num=12, conventional_decimals=2, name="Algerian dinar", symbol="DA")
    EGP = Currency(code="EGP", num=818, conventional_decimals=2, name="Egyptian pound", symbol="\u00a3E")
    ERN = Currency(code="ERN", num=232, conventional_decimals=2, name="Eritrean nakfa", symbol="Nfk")
    ETB = Currency(code="ETB", num=230, conventional_decimals=2, name="Ethiopian birr", symbol="Br")
    EUR = Currency(code="EUR", num=978, conventional_decimals=2, name="Euro", symbol="\u20ac")
    FJD = Currency(code="FJD", num=242, conventional_decimals=2, name="Fiji dollar", symbol="FJ$")
    FKP = Currency(code="FKP", num=238, conventional_decimals=2, name="Falkland Islands pound", symbol="\u00a3")
    GBP = Currency(code="GBP", num=826, conventional_decimals=2, name="Pound sterling", symbol="\u00a3")
    GEL = Currency(code="GEL", num=981, conventional_decimals=2, name="Georgian lari", symbol="\u20be")
    GHS = Currency(code="GHS", num=936, conventional_decimals=2, name="Ghanaian cedi", symbol="\u20bf")
    GIP = Currency(code="GIP", num=292, conventional_decimals=2, name="Gibraltar pound", symbol="\u00a3")
    GMD = Currency(code="GMD", num=270, conventional_decimals=2, name="Gambian dalasi", symbol="D")
    GNF = Currency(code="GNF", num=324, conventional_decimals=0, name="Guinean franc", symbol="FG")
    GTQ = Currency(code="GTQ", num=320, conventional_decimals=2, name="Guatemalan quetzal", symbol="Q")
    GYD = Currency(code="GYD", num=328, conventional_decimals=2, name="Guyanese dollar", symbol="G$")
    HKD = Currency(code="HKD", num=344, conventional_decimals=2, name="Hong Kong dollar", symbol="HK$")
    HNL = Currency(code="HNL", num=340, conventional_decimals=2, name="Honduran lempira", symbol="L")
    HTG = Currency(code="HTG", num=332, conventional_decimals=2, name="Haitian gourde", symbol="G")
    HUF = Currency(code="HUF", num=348, conventional_decimals=2, name="Hungarian forint", symbol="Ft")
    IDR = Currency(code="IDR", num=360, conventional_decimals=2, name="Indonesian rupiah", symbol="Rp")
    ILS = Currency(code="ILS", num=376, conventional_decimals=2, name="Israeli new shekel", symbol="\u20aa")
    INR = Currency(code="INR", num=356, conventional_decimals=2, name="Indian rupee", symbol="\u20b9")
    IQD = Currency(code="IQD", num=368, conventional_decimals=3, name="Iraqi dinar", symbol="ID")
    IRR = Currency(code="IRR", num=364, conventional_decimals=2, name="Iranian rial", symbol="\ufdfc")
    ISK = Currency(code="ISK", num=352, conventional_decimals=0, name="Icelandic króna", symbol="kr")
    JMD = Currency(code="JMD", num=388, conventional_decimals=2, name="Jamaican dollar", symbol="J$")
    JOD = Currency(code="JOD", num=400, conventional_decimals=3, name="Jordanian dinar", symbol="JD")
    JPY = Currency(code="JPY", num=392, conventional_decimals=0, name="Japanese yen", symbol="\u00a5")
    KES = Currency(code="KES", num=404, conventional_decimals=2, name="Kenyan shilling", symbol="KSh")
    KGS = Currency(code="KGS", num=417, conventional_decimals=2, name="Kyrgyzstani som", symbol="\u20c0")
    KHR = Currency(code="KHR", num=116, conventional_decimals=2, name="Cambodian riel", symbol="\u17db")
    KMF = Currency(code="KMF", num=174, conventional_decimals=0, name="Comoro franc", symbol="FC")
    KPW = Currency(code="KPW", num=408, conventional_decimals=2, name="North Korean won", symbol="\u20a9")
    KRW = Currency(code="KRW", num=410, conventional_decimals=0, name="South Korean won", symbol="\u20a9")
    KWD = Currency(code="KWD", num=414, conventional_decimals=3, name="Kuwaiti dinar", symbol="KD")
    KYD = Currency(code="KYD", num=136, conventional_decimals=2, name="Cayman Islands dollar", symbol="CI$")
    KZT = Currency(code="KZT", num=398, conventional_decimals=2, name="Kazakhstani tenge", symbol="\u20B8")
    LAK = Currency(code="LAK", num=418, conventional_decimals=2, name="Lao kip", symbol="\u20ad ")
    LBP = Currency(code="LBP", num=422, conventional_decimals=2, name="Lebanese pound", symbol="LL")
    LKR = Currency(code="LKR", num=144, conventional_decimals=2, name="Sri Lankan rupee", symbol="\u20a8")
    LRD = Currency(code="LRD", num=430, conventional_decimals=2, name="Liberian dollar", symbol="L$")
    LSL = Currency(code="LSL", num=426, conventional_decimals=2, name="Lesotho loti", symbol="L")
    LYD = Currency(code="LYD", num=434, conventional_decimals=3, name="Libyan dinar", symbol="LD")
    MAD = Currency(code="MAD", num=504, conventional_decimals=2, name="Moroccan dirham", symbol="Dh")
    MDL = Currency(code="MDL", num=498, conventional_decimals=2, name="Moldovan leu", symbol="L")
    MGA = Currency(code="MGA", num=969, conventional_decimals=2, name="Malagasy ariary", symbol="Ar")
    MKD = Currency(code="MKD", num=807, conventional_decimals=2, name="Macedonian denar", symbol="DEN")
    MMK = Currency(code="MMK", num=104, conventional_decimals=2, name="Myanmar kyat", symbol="K")
    MNT = Currency(code="MNT", num=496, conventional_decimals=2, name="Mongolian tögrög", symbol="\u20ae")
    MOP = Currency(code="MOP", num=446, conventional_decimals=2, name="Macanese pataca", symbol="$")
    MRU = Currency(code="MRU", num=929, conventional_decimals=2, name="Mauritanian ouguiya", symbol="UM")
    MUR = Currency(code="MUR", num=480, conventional_decimals=2, name="Mauritian rupee", symbol="\u20a8")
    MVR = Currency(code="MVR", num=462, conventional_decimals=2, name="Maldivian rufiyaa", symbol="Rf")
    MWK = Currency(code="MWK", num=454, conventional_decimals=2, name="Malawian kwacha", symbol="MK")
    MXN = Currency(code="MXN", num=484, conventional_decimals=2, name="Mexican peso", symbol="Mex$")
    MXV = Currency(code="MXV", num=979, conventional_decimals=2, name="Mexican Unidad de Inversion (UDI) (funds code)", symbol=None)
    MYR = Currency(code="MYR", num=458, conventional_decimals=2, name="Malaysian ringgit", symbol="RM")
    MZN = Currency(code="MZN", num=943, conventional_decimals=2, name="Mozambican metical", symbol="Mt")
    NAD = Currency(code="NAD", num=516, conventional_decimals=2, name="Namibian dollar", symbol="N$")
    NGN = Currency(code="NGN", num=566, conventional_decimals=2, name="Nigerian naira", symbol="\u20a6")
    NIO = Currency(code="NIO", num=558, conventional_decimals=2, name="Nicaraguan córdoba", symbol="C$")
    NOK = Currency(code="NOK", num=578, conventional_decimals=2, name="Norwegian krone", symbol="kr")
    NPR = Currency(code="NPR", num=524, conventional_decimals=2, name="Nepalese rupee", symbol="\u20b9")
    NZD = Currency(code="NZD", num=554, conventional_decimals=2, name="New Zealand dollar", symbol="$NZ")
    OMR = Currency(code="OMR", num=512, conventional_decimals=3, name="Omani rial", symbol="RO")
    PAB = Currency(code="PAB", num=590, conventional_decimals=2, name="Panamanian balboa", symbol="B/.")
    PEN = Currency(code="PEN", num=604, conventional_decimals=2, name="Peruvian sol", symbol="S/")
    PGK = Currency(code="PGK", num=598, conventional_decimals=2, name="Papua New Guinean kina", symbol="K")
    PHP = Currency(code="PHP", num=608, conventional_decimals=2, name="Philippine peso", symbol="\u20b1")
    PKR = Currency(code="PKR", num=586, conventional_decimals=2, name="Pakistani rupee", symbol="Pre")
    PLN = Currency(code="PLN", num=985, conventional_decimals=2, name="Polish złoty", symbol="z\u0142")
    PYG = Currency(code="PYG", num=600, conventional_decimals=0, name="Paraguayan guaraní", symbol="\u20b2")
    QAR = Currency(code="QAR", num=634, conventional_decimals=2, name="Qatari riyal", symbol="QR")
    RON = Currency(code="RON", num=946, conventional_decimals=2, name="Romanian leu", symbol=None)
    RSD = Currency(code="RSD", num=941, conventional_decimals=2, name="Serbian dinar", symbol="DIN")
    RUB = Currency(code="RUB", num=643, conventional_decimals=2, name="Russian ruble", symbol="\u20bd")
    RWF = Currency(code="RWF", num=646, conventional_decimals=0, name="Rwandan franc", symbol="FRw")
    SAR = Currency(code="SAR", num=682, conventional_decimals=2, name="Saudi riyal", symbol="\u20c2")
    SBD = Currency(code="SBD", num=90, conventional_decimals=2, name="Solomon Islands dollar", symbol="SI$")
    SCR = Currency(code="SCR", num=690, conventional_decimals=2, name="Seychelles rupee", symbol="Sre")
    SDG = Currency(code="SDG", num=938, conventional_decimals=2, name="Sudanese pound", symbol="LS")
    SEK = Currency(code="SEK", num=752, conventional_decimals=2, name="Swedish krona", symbol="kr")
    SGD = Currency(code="SGD", num=702, conventional_decimals=2, name="Singapore dollar", symbol="S$")
    SHP = Currency(code="SHP", num=654, conventional_decimals=2, name="Saint Helena pound", symbol="\u00A3")
    SLE = Currency(code="SLE", num=925, conventional_decimals=2, name="Sierra Leonean leone", symbol="Le")
    SOS = Currency(code="SOS", num=706, conventional_decimals=2, name="Somalian shilling", symbol="Sh.So.")
    SRD = Currency(code="SRD", num=968, conventional_decimals=2, name="Surinamese dollar", symbol=None)
    SSP = Currency(code="SSP", num=728, conventional_decimals=2, name="South Sudanese pound", symbol="SSP")
    STN = Currency(code="STN", num=930, conventional_decimals=2, name="São Tomé and Príncipe dobra", symbol="Db")
    SVC = Currency(code="SVC", num=222, conventional_decimals=2, name="Salvadoran colón", symbol="\u20a1")
    SYP = Currency(code="SYP", num=760, conventional_decimals=2, name="Syrian pound", symbol="LS")
    SZL = Currency(code="SZL", num=748, conventional_decimals=2, name="Swazi lilangeni", symbol="E")
    THB = Currency(code="THB", num=764, conventional_decimals=2, name="Thai baht", symbol="\u0E3F")
    TJS = Currency(code="TJS", num=972, conventional_decimals=2, name="Tajikistani somoni", symbol="SM")
    TMT = Currency(code="TMT", num=934, conventional_decimals=2, name="Turkmenistan manat", symbol="\u20bc")
    TND = Currency(code="TND", num=788, conventional_decimals=3, name="Tunisian dinar", symbol="DT")
    TOP = Currency(code="TOP", num=776, conventional_decimals=2, name="Tongan paʻanga", symbol="T$")
    TRY = Currency(code="TRY", num=949, conventional_decimals=2, name="Turkish lira", symbol="\u20ba")
    TTD = Currency(code="TTD", num=780, conventional_decimals=2, name="Trinidad and Tobago dollar", symbol="TT$")
    TWD = Currency(code="TWD", num=901, conventional_decimals=2, name="New Taiwan dollar", symbol="NT$")
    TZS = Currency(code="TZS", num=834, conventional_decimals=2, name="Tanzanian shilling", symbol="TSh")
    UAH = Currency(code="UAH", num=980, conventional_decimals=2, name="Ukrainian hryvnia", symbol="\u20b4")
    UGX = Currency(code="UGX", num=800, conventional_decimals=0, name="Ugandan shilling", symbol="Ush")
    USD = Currency(code="USD", num=840, conventional_decimals=2, name="United States dollar", symbol="$")
    USN = Currency(code="USN", num=997, conventional_decimals=2, name="United States dollar (next day)", symbol="$")
    UYI = Currency(code="UYI", num=940, conventional_decimals=0, name="Uruguay Peso en Unidades Indexadas (URUIURUI) (funds code)", symbol=None)
    UYU = Currency(code="UYU", num=858, conventional_decimals=2, name="Uruguayan peso", symbol="$U")
    UYW = Currency(code="UYW", num=927, conventional_decimals=4, name="Unidad previsional", symbol=None)
    UZS = Currency(code="UZS", num=860, conventional_decimals=2, name="Uzbekistani sum", symbol="sum")
    VED = Currency(code="VED", num=926, conventional_decimals=2, name="Venezuelan digital bolívar", symbol="Bs")
    VES = Currency(code="VES", num=928, conventional_decimals=2, name="Venezuelan sovereign bolívar", symbol="Bs")
    VND = Currency(code="VND", num=704, conventional_decimals=0, name="Vietnamese đồng", symbol="\u20ab")
    VUV = Currency(code="VUV", num=548, conventional_decimals=0, name="Vanuatu vatu", symbol="VT")
    WST = Currency(code="WST", num=882, conventional_decimals=2, name="Samoan tala", symbol="WS$")
    XAF = Currency(code="XAF", num=950, conventional_decimals=0, name="CFA franc BEAC", symbol=None)
    XAG = Currency(code="XAG", num=961, conventional_decimals=None, name="Silver", symbol=None)
    XAU = Currency(code="XAU", num=959, conventional_decimals=None, name="Gold", symbol=None)
    XBA = Currency(code="XBA", num=955, conventional_decimals=None, name="European Composite Unit (EURCO) (bond market unit)", symbol=None)
    XBB = Currency(code="XBB", num=956, conventional_decimals=None, name="European Monetary Unit (E.M.U.-6) (bond market unit)", symbol=None)
    XBC = Currency(code="XBC", num=957, conventional_decimals=None, name="European Unit of Account 9 (E.U.A.-9) (bond market unit)", symbol=None)
    XBD = Currency(code="XBD", num=958, conventional_decimals=None, name="European Unit of Account 17 (E.U.A.-17) (bond market unit)", symbol=None)
    XCD = Currency(code="XCD", num=951, conventional_decimals=2, name="East Caribbean dollar", symbol="EC$")
    XCG = Currency(code="XCG", num=532, conventional_decimals=2, name="Netherlands Antillean guilder", symbol="\u0192")
    XDR = Currency(code="XDR", num=960, conventional_decimals=None, name="Special drawing rights", symbol=None)
    XOF = Currency(code="XOF", num=952, conventional_decimals=0, name="CFA franc BCEAO", symbol=None)
    XPD = Currency(code="XPD", num=964, conventional_decimals=None, name="Palladium", symbol=None)
    XPF = Currency(code="XPF", num=953, conventional_decimals=0, name="CFP franc (franc Pacifique)", symbol="F")
    XPT = Currency(code="XPT", num=962, conventional_decimals=None, name="Platinum", symbol=None)
    XSU = Currency(code="XSU", num=994, conventional_decimals=None, name="SUCRE", symbol=None)
    XTS = Currency(code="XTS", num=963, conventional_decimals=None, name="Code reserved for testing", symbol=None)
    XUA = Currency(code="XUA", num=965, conventional_decimals=None, name="ADB Unit of Account", symbol=None)
    XXX = Currency(code="XXX", num=999, conventional_decimals=None, name="No currency", symbol="")
    YER = Currency(code="YER", num=886, conventional_decimals=2, name="Yemeni rial", symbol="Yrl")
    ZAR = Currency(code="ZAR", num=710, conventional_decimals=2, name="South African rand", symbol="R")
    ZMW = Currency(code="ZMW", num=967, conventional_decimals=2, name="Zambian kwacha", symbol="K")
    ZWG = Currency(code="ZWG", num=924, conventional_decimals=2, name="Zimbabwe Gold", symbol="ZiG")

class InvalidCurrencyCode(KeyError):
    pass

class CurrencyMismatch(ValueError):
    pass

class Money(pyDecimal):
    currency: Currency
    _exp: int
    _int: str
    _sign: int
    _is_special: bool
    __slots__ = ("currency", "_exp","_int","_sign", "_is_special")

    def __new__(
            cls,
            value: Union[pyDecimal, CDecimal, float, str, tuple[int, Sequence[int], int], int]="0",
            currency: str = "XXX",
        ) -> "Money":
        """Create a new instance of Money"""
        self = object.__new__(cls)
        try:
            self.currency = Currencies[currency].value
        except KeyError:
            raise InvalidCurrencyCode("currency code %s is a invalid currency under ISO 4217" % currency)
        if isinstance(value, CDecimal):
            value = str(value)
        d = pyDecimal(value=value)
        self._exp  = d._exp # type: ignore
        self._sign = d._sign # type: ignore
        self._int  = d._int # type: ignore
        self._is_special  = d._is_special # type: ignore
        return self


    @classmethod
    def from_float(cls, f: float, currency: str = "XXX",) -> "Money":
        """Implement decimal's from float method"""
        return cls.__new__(Money, value=pyDecimal.from_float(f), currency=currency)

    def __repr__(self) -> str:
        """Represents the number as an instance of Money."""
        return "Money('%s')" % str(self)

    def __str__(self) -> str:
        """Return string representation of the money"""
        return f"{self.currency.symbol if self.currency.symbol else ''}{super().__str__()}{'' if self.currency.symbol else ' ' + self.currency.code}"

    def _check_for_currency_match(self, value: ComparableType) -> bool:
         return isinstance(value, Money) and (value.currency.code == self.currency.code)

    def _raise_for_currency_mismatch(self, value: ComparableType, operation:str) -> None:
        if isinstance(value, Money) and (value.currency.code != self.currency.code):
            raise CurrencyMismatch(f"Operation of {operation} cannot be performed between {self.currency.code} and {value.currency.code}")

    def _ready_operable_value(self, value: OperableType) -> SafeOperableType:
        """Protect from C Decimal incompatibility with python Decimal and currency check for operable values"""
        return pyDecimal(str(value)) if isinstance(value, CDecimal) else value

    def _ready_comparable_type(self, value: ComparableType) -> SafeComparableType:
        """"Protect from C Decimal incompatibility with python Decimal and currency check for comparable values"""
        return pyDecimal(str(value)) if isinstance(value, CDecimal) else value

    def _operation_common(self, value: OperableType, name: str) -> SafeOperableType:
        """Core functions shared between operations with and without context"""
        self._raise_for_currency_mismatch(value, self.__add__.__name__)
        return pyDecimal(str(value)) if isinstance(value, CDecimal) else value

    def _operation(self, value: OperableType, name: str) -> Union["Money", pyDecimal]:
        """Generic function for operations on Money that do not need context"""
        v = self._operation_common(value, name)
        if self._check_for_currency_match(v):
            return Money(getattr(super(), name)(v), currency=self.currency.code)
        else:
            return getattr(super(), name)(v)

    def _operation_w_context(self, value: OperableType, name: str, context: Optional[Context]) -> Union["Money", pyDecimal]:
        """Generic function for operations on Money that do not need context"""
        v = self._operation_common(value, name)
        if self._check_for_currency_match(v):
            return Money(getattr(super(), name)(v, context), currency=self.currency.code)
        else:
            return getattr(super(), name)(v, context)

    def compare(self, other: OperableType, context: Optional[Context] = None) -> Union["Money", pyDecimal]:
        """Implement decimal's compare method"""
        # the typing for compare in pyDecimal leaves something to be desired as the typing seems
        # to have some level of mis match with with behavior of the function itself
        return self._operation_w_context(other, name=self.compare.__name__, context=context)

    def __add__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__add__.__name__)

    def __eq__(self, value: object) -> bool:
        return (
            super().__eq__(value)
            if (not isinstance(value, Money)) or self._check_for_currency_match(value)
            else False
        )

    def __floordiv__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__floordiv__.__name__)

    def __ge__(self, value: ComparableType) -> bool:
        self._raise_for_currency_mismatch(value, self.__ge__.__name__)
        return super().__ge__(self._ready_comparable_type(value))

    def __gt__(self, value: ComparableType) -> bool:
        self._raise_for_currency_mismatch(value, self.__gt__.__name__)
        return super().__gt__(self._ready_comparable_type(value))

    def __le__(self, value: ComparableType) -> bool:
        self._raise_for_currency_mismatch(value, self.__le__.__name__)
        return super().__le__(self._ready_comparable_type(value))

    def __lt__(self, value: ComparableType) -> bool:
        self._raise_for_currency_mismatch(value, self.__lt__.__name__)
        return super().__lt__(self._ready_comparable_type(value))

    def __mod__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__mod__.__name__)

    def __mul__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__mul__.__name__)

    def __pow__(self, value: OperableType, mod: OperableType | None = None) -> Union["Money", pyDecimal]:
        self._raise_for_currency_mismatch(value, self.__pow__.__name__)
        safe_value = self._ready_operable_value(value)
        self._raise_for_currency_mismatch(mod, self.__pow__.__name__) if mod else None
        safe_mod = self._ready_operable_value(mod) if mod else None
        if self._check_for_currency_match(safe_value):
            return Money(super().__pow__(safe_value, safe_mod), currency=self.currency.code)
        else:
            return super().__pow__(safe_value, safe_mod)

    def __radd__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__radd__.__name__)

    def __rmod__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__rmod__.__name__)

    def __rmul__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__rmul__.__name__)

    def __rsub__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__rsub__.__name__)

    def __rtruediv__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__rtruediv__.__name__)

    def __sub__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__sub__.__name__)

    def __truediv__(self, value: OperableType) -> Union["Money", pyDecimal]:
        return self._operation(value, name=self.__truediv__.__name__)

    def remainder_near(self, other: OperableType, context: Optional[Context] = None) -> Union["Money", pyDecimal]:
        """Implement remainder_near from decimal"""
        return self._operation_w_context(other, name=self.remainder_near.__name__, context=context)

    def __rpow__(self, value: OperableType, context: Optional[Context] = None) -> Union["Money", pyDecimal]:
        return self._operation_w_context(value, name=self.__rpow__.__name__, context=context)

    def sqrt(self, context: Optional[Context] = None) -> "Money":
        """Implement square root from decimal"""
        return Money(pyDecimal(super().__str__()).sqrt(context=context), self.currency.code)

    def max(self, other:OperableType, context: Optional[Context] = None) -> Union["Money", pyDecimal]:
        """Implement max from decimal"""
        return self._operation_w_context(other, name=self.max.__name__, context=context)

    def min(self, other:OperableType, context: Optional[Context] = None) -> Union["Money", pyDecimal]:
        """Implement min from decimal"""
        return self._operation_w_context(other, name=self.min.__name__, context=context)
