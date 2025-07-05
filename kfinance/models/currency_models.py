from dataclasses import dataclass


@dataclass
class Currency:
    """Follows ISO 4217"""

    code: str
    num: int
    conventional_decimals: int
    name: str
    symbol: str | None


CURRENCIES = [
    Currency(
        code="AED",
        num=784,
        conventional_decimals=2,
        name="United Arab Emirates dirham",
        symbol=None,
    ),
    Currency(code="AFN", num=971, conventional_decimals=2, name="Afghan afghani", symbol="\u060b"),
    Currency(code="ALL", num=8, conventional_decimals=2, name="Albanian lek", symbol="Lek"),
    Currency(code="AMD", num=51, conventional_decimals=2, name="Armenian dram", symbol="\u058f"),
    Currency(code="AOA", num=973, conventional_decimals=2, name="Angolan kwanza", symbol="Kz"),
    Currency(code="ARS", num=32, conventional_decimals=2, name="Argentine peso", symbol="Arg$"),
    Currency(code="AUD", num=36, conventional_decimals=2, name="Australian dollar", symbol="A$"),
    Currency(code="AWG", num=533, conventional_decimals=2, name="Aruban florin", symbol="\u0192"),
    Currency(
        code="AZN", num=944, conventional_decimals=2, name="Azerbaijani manat", symbol="\u20bc"
    ),
    Currency(
        code="BAM",
        num=977,
        conventional_decimals=2,
        name="Bosnia and Herzegovina convertible mark",
        symbol="KM",
    ),
    Currency(code="BBD", num=52, conventional_decimals=2, name="Barbados dollar", symbol="Bds$"),
    Currency(code="BDT", num=50, conventional_decimals=2, name="Bangladeshi taka", symbol="\u09f3"),
    Currency(code="BGN", num=975, conventional_decimals=2, name="Bulgarian lev", symbol="lev"),
    Currency(code="BHD", num=48, conventional_decimals=3, name="Bahraini dinar", symbol="BD"),
    Currency(code="BIF", num=108, conventional_decimals=0, name="Burundian franc", symbol="FBu"),
    Currency(code="BMD", num=60, conventional_decimals=2, name="Bermudian dollar", symbol="Ber$"),
    Currency(code="BND", num=96, conventional_decimals=2, name="Brunei dollar", symbol="B$"),
    Currency(code="BOB", num=68, conventional_decimals=2, name="Boliviano", symbol="Bs"),
    Currency(
        code="BOV",
        num=984,
        conventional_decimals=2,
        name="Bolivian Mvdol (funds code),",
        symbol=None,
    ),
    Currency(code="BRL", num=986, conventional_decimals=2, name="Brazilian real", symbol="R$"),
    Currency(code="BSD", num=44, conventional_decimals=2, name="Bahamian dollar", symbol="B$"),
    Currency(code="BTN", num=64, conventional_decimals=2, name="Bhutanese ngultrum", symbol="Nu"),
    Currency(code="BWP", num=72, conventional_decimals=2, name="Botswana pula", symbol="P"),
    Currency(code="BYN", num=933, conventional_decimals=2, name="Belarusian ruble", symbol="R"),
    Currency(code="BZD", num=84, conventional_decimals=2, name="Belize dollar", symbol="BZ$"),
    Currency(code="CAD", num=124, conventional_decimals=2, name="Canadian dollar", symbol="C$"),
    Currency(code="CDF", num=976, conventional_decimals=2, name="Congolese franc", symbol="FC"),
    Currency(code="CHE", num=947, conventional_decimals=2, name="WIR franc", symbol=None),
    Currency(code="CHF", num=756, conventional_decimals=2, name="Swiss franc", symbol="SFr"),
    Currency(code="CHW", num=948, conventional_decimals=2, name="WIR franc", symbol=None),
    Currency(
        code="CLF",
        num=990,
        conventional_decimals=4,
        name="Unidad de Fomento (funds code),",
        symbol=None,
    ),
    Currency(code="CLP", num=152, conventional_decimals=0, name="Chilean peso", symbol="Ch$"),
    Currency(code="CNY", num=156, conventional_decimals=2, name="Renminbi", symbol="CN\u00a5"),
    Currency(code="COP", num=170, conventional_decimals=2, name="Colombian peso", symbol="Col$"),
    Currency(
        code="COU",
        num=970,
        conventional_decimals=2,
        name="Unidad de Valor Real (UVR), (funds code),",
        symbol=None,
    ),
    Currency(
        code="CRC", num=188, conventional_decimals=2, name="Costa Rican colon", symbol="\u20a1"
    ),
    Currency(code="CUP", num=192, conventional_decimals=2, name="Cuban peso", symbol="Cu$"),
    Currency(code="CVE", num=132, conventional_decimals=2, name="Cape Verdean escudo", symbol=None),
    Currency(code="CZK", num=203, conventional_decimals=2, name="Czech koruna", symbol="K\u010d"),
    Currency(code="DJF", num=262, conventional_decimals=0, name="Djiboutian franc", symbol="DF"),
    Currency(code="DKK", num=208, conventional_decimals=2, name="Danish krone", symbol="kr"),
    Currency(code="DOP", num=214, conventional_decimals=2, name="Dominican peso", symbol="RD$"),
    Currency(code="DZD", num=12, conventional_decimals=2, name="Algerian dinar", symbol="DA"),
    Currency(code="EGP", num=818, conventional_decimals=2, name="Egyptian pound", symbol="\u00a3E"),
    Currency(code="ERN", num=232, conventional_decimals=2, name="Eritrean nakfa", symbol="Nfk"),
    Currency(code="ETB", num=230, conventional_decimals=2, name="Ethiopian birr", symbol="Br"),
    Currency(code="EUR", num=978, conventional_decimals=2, name="Euro", symbol="\u20ac"),
    Currency(code="FJD", num=242, conventional_decimals=2, name="Fiji dollar", symbol="FJ$"),
    Currency(
        code="FKP", num=238, conventional_decimals=2, name="Falkland Islands pound", symbol="\u00a3"
    ),
    Currency(code="GBP", num=826, conventional_decimals=2, name="Pound sterling", symbol="\u00a3"),
    Currency(code="GEL", num=981, conventional_decimals=2, name="Georgian lari", symbol="\u20be"),
    Currency(code="GHS", num=936, conventional_decimals=2, name="Ghanaian cedi", symbol="\u20bf"),
    Currency(code="GIP", num=292, conventional_decimals=2, name="Gibraltar pound", symbol="\u00a3"),
    Currency(code="GMD", num=270, conventional_decimals=2, name="Gambian dalasi", symbol="D"),
    Currency(code="GNF", num=324, conventional_decimals=0, name="Guinean franc", symbol="FG"),
    Currency(code="GTQ", num=320, conventional_decimals=2, name="Guatemalan quetzal", symbol="Q"),
    Currency(code="GYD", num=328, conventional_decimals=2, name="Guyanese dollar", symbol="G$"),
    Currency(code="HKD", num=344, conventional_decimals=2, name="Hong Kong dollar", symbol="HK$"),
    Currency(code="HNL", num=340, conventional_decimals=2, name="Honduran lempira", symbol="L"),
    Currency(code="HTG", num=332, conventional_decimals=2, name="Haitian gourde", symbol="G"),
    Currency(code="HUF", num=348, conventional_decimals=2, name="Hungarian forint", symbol="Ft"),
    Currency(code="IDR", num=360, conventional_decimals=2, name="Indonesian rupiah", symbol="Rp"),
    Currency(
        code="ILS", num=376, conventional_decimals=2, name="Israeli new shekel", symbol="\u20aa"
    ),
    Currency(code="INR", num=356, conventional_decimals=2, name="Indian rupee", symbol="\u20b9"),
    Currency(code="IQD", num=368, conventional_decimals=3, name="Iraqi dinar", symbol="ID"),
    Currency(code="IRR", num=364, conventional_decimals=2, name="Iranian rial", symbol="\ufdfc"),
    Currency(code="ISK", num=352, conventional_decimals=0, name="Icelandic króna", symbol="kr"),
    Currency(code="JMD", num=388, conventional_decimals=2, name="Jamaican dollar", symbol="J$"),
    Currency(code="JOD", num=400, conventional_decimals=3, name="Jordanian dinar", symbol="JD"),
    Currency(code="JPY", num=392, conventional_decimals=0, name="Japanese yen", symbol="\u00a5"),
    Currency(code="KES", num=404, conventional_decimals=2, name="Kenyan shilling", symbol="KSh"),
    Currency(code="KGS", num=417, conventional_decimals=2, name="Kyrgyzstani som", symbol="\u20c0"),
    Currency(code="KHR", num=116, conventional_decimals=2, name="Cambodian riel", symbol="\u17db"),
    Currency(code="KMF", num=174, conventional_decimals=0, name="Comoro franc", symbol="FC"),
    Currency(
        code="KPW", num=408, conventional_decimals=2, name="North Korean won", symbol="\u20a9"
    ),
    Currency(
        code="KRW", num=410, conventional_decimals=0, name="South Korean won", symbol="\u20a9"
    ),
    Currency(code="KWD", num=414, conventional_decimals=3, name="Kuwaiti dinar", symbol="KD"),
    Currency(
        code="KYD", num=136, conventional_decimals=2, name="Cayman Islands dollar", symbol="CI$"
    ),
    Currency(
        code="KZT", num=398, conventional_decimals=2, name="Kazakhstani tenge", symbol="\u20b8"
    ),
    Currency(code="LAK", num=418, conventional_decimals=2, name="Lao kip", symbol="\u20ad "),
    Currency(code="LBP", num=422, conventional_decimals=2, name="Lebanese pound", symbol="LL"),
    Currency(
        code="LKR", num=144, conventional_decimals=2, name="Sri Lankan rupee", symbol="\u20a8"
    ),
    Currency(code="LRD", num=430, conventional_decimals=2, name="Liberian dollar", symbol="L$"),
    Currency(code="LSL", num=426, conventional_decimals=2, name="Lesotho loti", symbol="L"),
    Currency(code="LYD", num=434, conventional_decimals=3, name="Libyan dinar", symbol="LD"),
    Currency(code="MAD", num=504, conventional_decimals=2, name="Moroccan dirham", symbol="Dh"),
    Currency(code="MDL", num=498, conventional_decimals=2, name="Moldovan leu", symbol="L"),
    Currency(code="MGA", num=969, conventional_decimals=2, name="Malagasy ariary", symbol="Ar"),
    Currency(code="MKD", num=807, conventional_decimals=2, name="Macedonian denar", symbol="DEN"),
    Currency(code="MMK", num=104, conventional_decimals=2, name="Myanmar kyat", symbol="K"),
    Currency(
        code="MNT", num=496, conventional_decimals=2, name="Mongolian tögrög", symbol="\u20ae"
    ),
    Currency(code="MOP", num=446, conventional_decimals=2, name="Macanese pataca", symbol="$"),
    Currency(code="MRU", num=929, conventional_decimals=2, name="Mauritanian ouguiya", symbol="UM"),
    Currency(code="MUR", num=480, conventional_decimals=2, name="Mauritian rupee", symbol="\u20a8"),
    Currency(code="MVR", num=462, conventional_decimals=2, name="Maldivian rufiyaa", symbol="Rf"),
    Currency(code="MWK", num=454, conventional_decimals=2, name="Malawian kwacha", symbol="MK"),
    Currency(code="MXN", num=484, conventional_decimals=2, name="Mexican peso", symbol="Mex$"),
    Currency(
        code="MXV",
        num=979,
        conventional_decimals=2,
        name="Mexican Unidad de Inversion (UDI), (funds code),",
        symbol=None,
    ),
    Currency(code="MYR", num=458, conventional_decimals=2, name="Malaysian ringgit", symbol="RM"),
    Currency(code="MZN", num=943, conventional_decimals=2, name="Mozambican metical", symbol="Mt"),
    Currency(code="NAD", num=516, conventional_decimals=2, name="Namibian dollar", symbol="N$"),
    Currency(code="NGN", num=566, conventional_decimals=2, name="Nigerian naira", symbol="\u20a6"),
    Currency(code="NIO", num=558, conventional_decimals=2, name="Nicaraguan córdoba", symbol="C$"),
    Currency(code="NOK", num=578, conventional_decimals=2, name="Norwegian krone", symbol="kr"),
    Currency(code="NPR", num=524, conventional_decimals=2, name="Nepalese rupee", symbol="\u20b9"),
    Currency(code="NZD", num=554, conventional_decimals=2, name="New Zealand dollar", symbol="$NZ"),
    Currency(code="OMR", num=512, conventional_decimals=3, name="Omani rial", symbol="RO"),
    Currency(code="PAB", num=590, conventional_decimals=2, name="Panamanian balboa", symbol="B/."),
    Currency(code="PEN", num=604, conventional_decimals=2, name="Peruvian sol", symbol="S/"),
    Currency(
        code="PGK", num=598, conventional_decimals=2, name="Papua New Guinean kina", symbol="K"
    ),
    Currency(code="PHP", num=608, conventional_decimals=2, name="Philippine peso", symbol="\u20b1"),
    Currency(code="PKR", num=586, conventional_decimals=2, name="Pakistani rupee", symbol="Pre"),
    Currency(code="PLN", num=985, conventional_decimals=2, name="Polish złoty", symbol="z\u0142"),
    Currency(
        code="PYG", num=600, conventional_decimals=0, name="Paraguayan guaraní", symbol="\u20b2"
    ),
    Currency(code="QAR", num=634, conventional_decimals=2, name="Qatari riyal", symbol="QR"),
    Currency(code="RON", num=946, conventional_decimals=2, name="Romanian leu", symbol=None),
    Currency(code="RSD", num=941, conventional_decimals=2, name="Serbian dinar", symbol="DIN"),
    Currency(code="RUB", num=643, conventional_decimals=2, name="Russian ruble", symbol="\u20bd"),
    Currency(code="RWF", num=646, conventional_decimals=0, name="Rwandan franc", symbol="FRw"),
    Currency(code="SAR", num=682, conventional_decimals=2, name="Saudi riyal", symbol="\u20c2"),
    Currency(
        code="SBD", num=90, conventional_decimals=2, name="Solomon Islands dollar", symbol="SI$"
    ),
    Currency(code="SCR", num=690, conventional_decimals=2, name="Seychelles rupee", symbol="Sre"),
    Currency(code="SDG", num=938, conventional_decimals=2, name="Sudanese pound", symbol="LS"),
    Currency(code="SEK", num=752, conventional_decimals=2, name="Swedish krona", symbol="kr"),
    Currency(code="SGD", num=702, conventional_decimals=2, name="Singapore dollar", symbol="S$"),
    Currency(
        code="SHP", num=654, conventional_decimals=2, name="Saint Helena pound", symbol="\u00a3"
    ),
    Currency(
        code="SLE", num=925, conventional_decimals=2, name="Sierra Leonean leone", symbol="Le"
    ),
    Currency(
        code="SOS", num=706, conventional_decimals=2, name="Somalian shilling", symbol="Sh.So."
    ),
    Currency(code="SRD", num=968, conventional_decimals=2, name="Surinamese dollar", symbol=None),
    Currency(
        code="SSP", num=728, conventional_decimals=2, name="South Sudanese pound", symbol="SSP"
    ),
    Currency(
        code="STN",
        num=930,
        conventional_decimals=2,
        name="São Tomé and Príncipe dobra",
        symbol="Db",
    ),
    Currency(
        code="SVC", num=222, conventional_decimals=2, name="Salvadoran colón", symbol="\u20a1"
    ),
    Currency(code="SYP", num=760, conventional_decimals=2, name="Syrian pound", symbol="LS"),
    Currency(code="SZL", num=748, conventional_decimals=2, name="Swazi lilangeni", symbol="E"),
    Currency(code="THB", num=764, conventional_decimals=2, name="Thai baht", symbol="\u0e3f"),
    Currency(code="TJS", num=972, conventional_decimals=2, name="Tajikistani somoni", symbol="SM"),
    Currency(
        code="TMT", num=934, conventional_decimals=2, name="Turkmenistan manat", symbol="\u20bc"
    ),
    Currency(code="TND", num=788, conventional_decimals=3, name="Tunisian dinar", symbol="DT"),
    Currency(code="TOP", num=776, conventional_decimals=2, name="Tongan paʻanga", symbol="T$"),
    Currency(code="TRY", num=949, conventional_decimals=2, name="Turkish lira", symbol="\u20ba"),
    Currency(
        code="TTD",
        num=780,
        conventional_decimals=2,
        name="Trinidad and Tobago dollar",
        symbol="TT$",
    ),
    Currency(code="TWD", num=901, conventional_decimals=2, name="New Taiwan dollar", symbol="NT$"),
    Currency(code="TZS", num=834, conventional_decimals=2, name="Tanzanian shilling", symbol="TSh"),
    Currency(
        code="UAH", num=980, conventional_decimals=2, name="Ukrainian hryvnia", symbol="\u20b4"
    ),
    Currency(code="UGX", num=800, conventional_decimals=0, name="Ugandan shilling", symbol="Ush"),
    Currency(code="USD", num=840, conventional_decimals=2, name="United States dollar", symbol="$"),
    Currency(
        code="USN",
        num=997,
        conventional_decimals=2,
        name="United States dollar (next day),",
        symbol="$",
    ),
    Currency(
        code="UYI",
        num=940,
        conventional_decimals=0,
        name="Uruguay Peso en Unidades Indexadas (URUIURUI), (funds code),",
        symbol=None,
    ),
    Currency(code="UYU", num=858, conventional_decimals=2, name="Uruguayan peso", symbol="$U"),
    Currency(code="UYW", num=927, conventional_decimals=4, name="Unidad previsional", symbol=None),
    Currency(code="UZS", num=860, conventional_decimals=2, name="Uzbekistani sum", symbol="sum"),
    Currency(
        code="VED", num=926, conventional_decimals=2, name="Venezuelan digital bolívar", symbol="Bs"
    ),
    Currency(
        code="VES",
        num=928,
        conventional_decimals=2,
        name="Venezuelan sovereign bolívar",
        symbol="Bs",
    ),
    Currency(code="VND", num=704, conventional_decimals=0, name="Vietnamese đồng", symbol="\u20ab"),
    Currency(code="VUV", num=548, conventional_decimals=0, name="Vanuatu vatu", symbol="VT"),
    Currency(code="WST", num=882, conventional_decimals=2, name="Samoan tala", symbol="WS$"),
    Currency(code="XAF", num=950, conventional_decimals=0, name="CFA franc BEAC", symbol=None),
    Currency(code="XAG", num=961, conventional_decimals=3, name="Silver", symbol=None),
    Currency(code="XAU", num=959, conventional_decimals=3, name="Gold", symbol=None),
    Currency(
        code="XBA",
        num=955,
        conventional_decimals=3,
        name="European Composite Unit (EURCO), (bond market unit),",
        symbol=None,
    ),
    Currency(
        code="XBB",
        num=956,
        conventional_decimals=3,
        name="European Monetary Unit (E.M.U.-6), (bond market unit),",
        symbol=None,
    ),
    Currency(
        code="XBC",
        num=957,
        conventional_decimals=3,
        name="European Unit of Account 9 (E.U.A.-9), (bond market unit),",
        symbol=None,
    ),
    Currency(
        code="XBD",
        num=958,
        conventional_decimals=3,
        name="European Unit of Account 17 (E.U.A.-17), (bond market unit),",
        symbol=None,
    ),
    Currency(
        code="XCD", num=951, conventional_decimals=2, name="East Caribbean dollar", symbol="EC$"
    ),
    Currency(
        code="XCG",
        num=532,
        conventional_decimals=2,
        name="Netherlands Antillean guilder",
        symbol="\u0192",
    ),
    Currency(
        code="XDR", num=960, conventional_decimals=3, name="Special drawing rights", symbol=None
    ),
    Currency(code="XOF", num=952, conventional_decimals=0, name="CFA franc BCEAO", symbol=None),
    Currency(code="XPD", num=964, conventional_decimals=3, name="Palladium", symbol=None),
    Currency(
        code="XPF",
        num=953,
        conventional_decimals=0,
        name="CFP franc (franc Pacifique),",
        symbol="F",
    ),
    Currency(code="XPT", num=962, conventional_decimals=3, name="Platinum", symbol=None),
    Currency(code="XSU", num=994, conventional_decimals=3, name="SUCRE", symbol=None),
    Currency(
        code="XTS", num=963, conventional_decimals=3, name="Code reserved for testing", symbol=None
    ),
    Currency(code="XUA", num=965, conventional_decimals=3, name="ADB Unit of Account", symbol=None),
    Currency(code="XXX", num=999, conventional_decimals=3, name="No currency", symbol=None),
    Currency(code="YER", num=886, conventional_decimals=2, name="Yemeni rial", symbol="Yrl"),
    Currency(code="ZAR", num=710, conventional_decimals=2, name="South African rand", symbol="R"),
    Currency(code="ZMW", num=967, conventional_decimals=2, name="Zambian kwacha", symbol="K"),
    Currency(code="ZWG", num=924, conventional_decimals=2, name="Zimbabwe Gold", symbol="ZiG"),
]
ISO_CODE_TO_CURRENCY = {c.code: c for c in CURRENCIES}
