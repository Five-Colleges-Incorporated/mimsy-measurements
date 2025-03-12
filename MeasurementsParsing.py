# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %%
# %conda env update -n base --file environment.yml

# %%
from dotenv import load_dotenv

load_dotenv()

# %%
is_notebook = False
try:
    get_ipython()
    is_notebook = True
    from rich import print
except:
    pass
print("In a notebook: ", is_notebook)

# %%
import os

import oracledb

mimsy = oracledb.connect(
    dsn=f"{os.environ["MIMSY_HOST"]}:{os.environ["MIMSY_PORT"]}/{os.environ["MIMSY_SERVICE"]}",
    user=os.environ["MIMSY_USERNAME"],
    password=os.environ["MIMSY_PASSWORD"],
    tcp_connect_timeout=5.0,
)
mimsy.is_healthy()

# %%
# query = "SELECT M_ID, MEASUREMENTS FROM CATALOGUE WHERE MEASUREMENTS IS NOT NULL FETCH NEXT 10 ROWS ONLY"
query = "SELECT M_ID, MEASUREMENTS FROM CATALOGUE WHERE M_ID > {0} AND MEASUREMENTS IS NOT NULL ORDER BY M_ID ASC"

# %%
import polars as pl


def measurements(last=0):
    return pl.read_database(
        connection=mimsy, query=query.format(last), iter_batches=True, batch_size=500
    )


# %%
if is_notebook:
    ms = pl.concat(list(measurements())).to_dicts()
    tests = """
    (ok, res) = mimsy_string.run_tests('''"""
    for m in ms:
        tests += f"\n\n\t# M_ID: {m["M_ID"]}"
        tests += f"\n\t{m["MEASUREMENTS"]}"
    tests += """''',
        print_results=False,
        full_dump=False,
    )
    print("Success!" if ok else res) 
    """
    print(tests)

# %%
import pyparsing as pp

dim = pp.Group(
    pp.Word(pp.nums + "." + "/" + " ").set_parse_action(pp.token_map(str.strip))(
        "value"
    )
    + pp.Optional(pp.oneOf(["in", "ft", "cm", "m"])("unit") + pp.Optional("."))
)

if is_notebook:
    (ok, res) = dim.run_tests(
        [
            "15/16 in",
            "5 3/4 in",
            "12 in",
            "14.6 cm",
            "11 cm",
            "3",
            "31 7/8",
            "125.7",
            "81",
            "17 ft",
            "5.2 m",
            "47 13/16 in.",
        ],
        print_results=False,
        full_dump=False,
    )
    print("Success!" if ok else res)

vol = pp.Group(
    (dim("width"))
    + pp.Optional(pp.Suppress("x") + dim("height"))
    + pp.Optional(pp.Suppress("x") + dim("depth"))
)


dimensions = pp.Group(
    pp.Optional(
        pp.Group(
            pp.Word(pp.alphanums + "/" + "-" + "&" + "?" + "'" + " ").set_parse_action(pp.token_map(str.strip))
            + pp.Optional(pp.Suppress(";") + pp.Word(pp.alphas + "-"))
            + pp.Optional(pp.Suppress(",") + pp.Word(pp.alphas + "/" + " ").set_parse_action(pp.token_map(str.strip)))
            + pp.Optional(pp.Combine("(" + pp.Word(pp.alphas + "-" + " ").set_parse_action(pp.token_map(str.strip)) + ")"))
        )("type")
        + pp.Suppress(":")
    )
    + pp.OneOrMore(vol("measurements*") + pp.Suppress(pp.Optional(";")))
)

if is_notebook:
    (ok, res) = dimensions.run_tests(
        [
            "Overall: 5 3/4 in x 12 1/4 in x 9 1/8 in; 14.6 cm x 31.1 cm x 23.2 cm",
            "Overall (a): 4 in x 2 7/8 in; 10.2 cm x 7.3 cm",
            "5Sheet: 17 3/8 in x 13 in; 44.1 cm x 33 cm",
            "Overall: 15/16 in x 3 1/16 in x 2 in; 2.4 cm x 7.8 cm x 5.1 cm",
            "24 x 24 in; 60.96 x 60.96 cm",
            "Sheet/Image: 5 x 7 1/4 in; 12.7 x 18.4 cm",
            "Overall: 9 in; 22.9 cm",
            "canvas (semi-circular): 31 1/8 x 59 1/8 in.; 79.0575 x 150.1775 cm",
            "u-shaped: 103 x 111 in.; 261.62 x 281.94 cm",
            "image and sheet: 21 7/8 x 30 in.; 55.5625 x 76.2 cm",
            "Overall (right boot): 10 1/4 in x 4 1/2 in x 12 in; 26 cm x 11.4 cm x 30.5 cm.",
            "stretcher; semi-circle: 33 1/4 x 66 1/4 in.; 84.455 x 168.275 cm",
            "sheet & image: 15 9/16 x 18 5/8 in.; 39.5288 x 47.3075 cm",
            "height, without base: 21 in.; 53.34 cm",
            "sheet?: 14 x 20 1/8 in.; 35.56 x 51.1175 cm",
            "overall, w/handle: 5 3/4 x 4 1/2 x 9 1/8 in.; 14.605 x 11.43 x 23.1775 cm",
            "artist's board: 7 5/8 x 11 7/16 in.; 19.3675 x 29.0513 cm",
        ],
        print_results=False,
        full_dump=False,
    )
    print("Success!" if ok else res)

mimsy_string = pp.OneOrMore(dimensions("dimensions*"))

if is_notebook:
    mimsy_string.create_diagram("parser.html", show_results_names=True)

    ex = mimsy_string.parse_string(
        "artist's board: 7 5/8 x 11 7/16 in.; 19.3675 x 29.0513 cm",
    )
    print(ex)
    print(ex.as_dict())

    (ok, res) = mimsy_string.run_tests(
        """

        # M_ID: 3
        Overall: 5 3/4 in x 12 1/4 in x 9 1/8 in; 14.6 cm x 31.1 cm x 23.2 cm

        # M_ID: 12
        Overall: 5 1/8 in x 2 7/8 in; 13 cm x 7.3 cm

        # M_ID: 13
        Sheet: 12 in x 16 in; 30.5 cm x 40.6 cm

        # M_ID: 14
        Overall (a): 4 in x 2 7/8 in; 10.2 cm x 7.3 cm; Overall (b): 3 5/8 in x 4 1/8 in; 9.2 cm x 10.5 cm

        # M_ID: 15
        Overall: 8 3/8 in x 4 1/16 in; 21.3 cm x 10.3 cm

        # M_ID: 16
        Overall: 7 9/16 in x 4 5/16 in; 19.2 cm x 11 cm

        # M_ID: 17
        Sheet: 9 15/16 in x 13 15/16 in; 25.2 cm x 35.4 cm

        # M_ID: 18
        mat: 24 3/8 in x 30 5/8 in; 61.9 cm x 77.8 cm; sheet: 18 in x 23 7/8 in; 45.7 cm x 60.6 cm

        # M_ID: 19
        mat: 19 13/16 in x 25 5/8 in; 50.3 cm x 65.1 cm; sheet: 15 1/4 in x 20 in; 38.7 cm x 50.8 cm

        # M_ID: 20
        Sheet: 16 in x 20 in; 40.6 cm x 50.8 cm""",
        print_results=False,
        full_dump=False,
    )
    print("Success!" if ok else res)

# %%
#last = 0
for batch in measurements(last - 1):
    for m in batch.to_dicts():
        try:
            if m["M_ID"] in [
                # misfits
                120306,
                122060,
                155447,
                155633,
                160985,
                161040,
                161062,
                161090,
                161103,
                161116,
                161118,
                162120,
                162558,
                163006,
                163008,
                163012,
                163033,
                163944,
                166223,
                168210,
                1000329,
                1001241,
                2001327,
                2001730,
                2002360,
                2002496,
                2002650,
                2005347,
                2006524,
                2008289,
                2008396,
                2008397,
                2009489,
                2009497,
                2009508,
                2009512,
                2009518,
                2009522,
                2009524,
                2009525,
                2009534,
                2009538,
                2009773,
                2009788,
                2010353,
                2010356,
                2010370,
                2010373,
                2010375,
                2010386,
                2010390,
                2010391,
                2010392,
                2010575,
                2010651,
                2011864,
                2011865,
                2011866,
                2011867,
                2012301,
                2012313,
                2012382,
                2012383,
                2012384,
                2012385,
                2012386,
                2012387,
                2012388,
                2012389,
                2012390,
                2012391,
                2012392,
                2012393,
                2012394,
                2012395,
                2012397,
                2012399,
                2012400,
                2012402,
                2012403,
                2012404,
                2012405,
                2012406,
                2012456,
                2012458,
                2012459,
                2012461,
                2012462,
                2012463,
                2012466,
                2012467,
                2012468,
                2012470,
                2012482,
                2012490,
                2012503,
                2012504,
                2012649,
                2013033,
                2013137,
                2013197,
                2013242,
                2013357,
                2013360,
                2013401,
                2012498,
                2013115,
                2013116,
                2013117,
                2013135,
                2013136,
                2013220,
                2013236,
                2013239,
                2013243,
                2013244,
                2013228,
                2013229,
                2013286,
                2013287,
                2013288,
                2013307,
                2013308,
                2013309,
                2013310,
                2013311,
                2013313,
                2013463,
                2013464,
                2013465,
                2013883,
                2014113,
                2101227,
                2103268,
                2104520,
                2105341,
                2105420,
                2105460,
                2105582,
                2105586,
                2105587,
                2105588,
                2105589,
                2105590,
                2105601,
                2105607,
                2105608,
                2105609,
                2105610,
                2105611,
                2105612,
                2105613,
                2105614,
                2105615,
                2105616,
                2105618,
                2105619,
                2105620,
                2105680,
                2105920,
                2105921,
                2105922,
                2105923,
                2105924,
                2105925,
                2105926,
                2105927,
                2105940,
                2105941,
                2105942,
                2105943,
                2105944,
                2105945,
                2105946,
                2105947,
                2105948,
                2105950,
                2105951,
                2105952,
                2105953,
                2105954,
                2105956,
                2105957,
                2105958,
                2105960,
                2105961,
                2105963,
                2106000,
                2106022,
                2106023,
                2106024,
                2106025,
                2106181,
                2106185,
                2106220,
                2106260,
                2106261,
                2106263,
                2106348,
                2106368,
                2106369,
                2106380,
                2106400,
                2106401,
                2106402,
                2106403,
                2106404,
                2106405,
                2106406,
                2106407,
                2106408,
                2106409,
                2106410,
                2106411,
                2106412,
                2106413,
                2106414,
                2106415,
                2106416,
                2106417,
                2106418,
                2106419,
                2106420,
                2106421,
                2106422,
                2106423,
                2106424,
                2106425,
                2106426,
                2106427,
                2106429,
                2106431,
                2106432,
                2106433,
                2106434,
                2106435,
                2106436,
                2106437,
                2106438,
                2106439,
                2106440,
                2106441,
                2106442,
                2106443,
                2106444,
                2106445,
                2106446,
                2106447,
                2106448,
                2106449,
                2106450,
                2106451,
                2106452,
                2106453,
                2106454,
                2106460,
                2106480,
                2106500,
                2106501,
                2106521,
                2106522,
                2106523,
                2106540,
                2106541,
                2106542,
                2106543,
                2106544,
                2106545,
                2106560,
                2106600,
                2106601,
                2106620,
                2106640,
                2106660,
                2106680,
                2106700,
                2106720,
                2106721,
                2106740,
                2106741,
                2106742,
                2106760,
                2106780,
                2106800,
                2106801,
                2106820,
                2106840,
                2106860,
                2106880,
                2106900,
                2106920,
                2106921,
                2106922,
                2106923,
                2106924,
                2106940,
                2106960,
                2106980,
                2106981,
                2106982,
                2107001,
                2107002,
                2107020,
                2107040,
                2107041,
                2107060,
                2107080,
                2107100,
                2107120,
                2107121,
                2107140,
                2107141,
                2107142,
                2107160,
                2107161,
                2107162,
                2107163,
                2107164,
                2107165,
                2107166,
                2107167,
                2107168,
                2107169,
                2107170,
                2107180,
                2107181,
                2107182,
                2107260,
                2107280,
                2107300,
                2107320,
                2107340,
                2107360,
                2107380,
                2107400,
                2107420,
                2107440,
                2107460,
                2107480,
                2107520,
                2107580,
                2107600,
                2107620,
                2107640,
                2107660,
                2107680,
                2107700,
                2107720,
                2107740,
                2107760,
                2107780,
                2107800,
                2107820,
                2107840,
                2107860,
                2107880,
                2107900,
                2107920,
                2107940,
                2107980,
                2108000,
                2108020,
                2108021,
                2108022,
                2108023,
                2108024,
                2108025,
                2108026,
                2108027,
                2108028,
                2108029,
                2108030,
                2108040,
                2108041,
                2108060,
                2108080,
                2108083,
                2108084,
                2108100,
                2108120,
                2108140,
                2108160,
                2108180,
                2108220,
                2108240,
                2108260,
                2108280,
                2108281,
                2108282,
                2108283,
                2108284,
                2108285,
                2108286,
                2108287,
                2108288,
                2108289,
                2108290,
                2108291,
                2108292,
                2108293,
                2108294,
                2108295,
                2108300,
                2108320,
                2108340,
                2108360,
                2108380,
                2108381,
                2108383,
                2108384,
                2108385,
                2108386,
                2108387,
                2108388,
                2108389,
                2108390,
                2108391,
                2108392,
                2108393,
                2108394,
                2108395,
                2108400,
                2108420,
                2108421,
                2108422,
                2108423,
                2108424,
                2108425,
                2108426,
                2108427,
                2108428,
                2108429,
                2108430,
                2108431,
                2108432,
                2108433,
                2108434,
                2108435,
                2108436,
                2108437,
                2108440,
                2108480,
                2108500,
                2108521,
                2108522,
                2108523,
                2108524,
                2108525,
                2108540,
                2108560,
                2108561,
                2108562,
                2108563,
                2108564,
                2108565,
                2108566,
                2108567,
                2108568,
                2108569,
                2108570,
                2108571,
                2108572,
                2108573,
                2108574,
                2108575,
                2108576,
                2108577,
                2108578,
                2108579,
                2108580,
                2108581,
                2108582,
                2108583,
                2108584,
                2108585,
                2108586,
                2108587,
                2108588,
                2108589,
                2108590,
                2108591,
                2108600,
                2108620,
                2108640,
                2108660,
                2108700,
                2108721,
                2108740,
                2108760,
                2108780,
                2108800,
                2108801,
                2108802,
                2108803,
                2108804,
                2108805,
                2108820,
                2108821,
                2108822,
                2108840,
                2108860,
                2108880,
                2108900,
                2108901,
                2108920,
                2108940,
                2108960,
                2108980,
                2109000,
                2109001,
                2109002,
                2109003,
                2109004,
                2109005,
                2109006,
                2109020,
                2109040,
                2109060,
                2109061,
                2109062,
                2109080,
                2109101,
                2109120,
                2109121,
                2109122,
                2109123,
                2109124,
                2109125,
                2109126,
                2109140,
                2109160,
                2109161,
                2109162,
                2109163,
                2109164,
                2109165,
                2109166,
                2109167,
                2109168,
                2109169,
                2109170,
                2109171,
                2109172,
                2109173,
                2109174,
                2109175,
                2109176,
                2109177,
                2109178,
                2109179,
                2109200,
                2109202,
                2109203,
                2109204,
                2109205,
                2109206,
                2109207,
                2109208,
                2109209,
                2109210,
                2109211,
                2109212,
                2109213,
                2109214,
                2109215,
                2109220,
                2109221,
                2109222,
                2109223,
                2109224,
                2109225,
                2109226,
                2109227,
                2109228,
                2109229,
                2109230,
                2109231,
                2109232,
                2109233,
                2109234,
                2109235,
                2109236,
                2109237,
                2109240,
                2109241,
                2109242,
                2109243,
                2109244,
                2109245,
                2109246,
                2109260,
                2109261,
                2109262,
                2109263,
                2109280,
                2109300,
                2109320,
                2109340,
                2109341,
                2109360,
                2109361,
                2109362,
                2109363,
                2109364,
                2109365,
                2109380,
                2109381,
                2109382,
                2109383,
                2109384,
                2109385,
                2109400,
                2109420,
                2109421,
                2109422,
                2109626,
                2109668,
                2109670,
                2109676,
                2109679,
                2109700,
                2109704,
                2109705,
                2109711,
                2109712,
                2109713,
                2109714,
                2109740,
                2109741,
                2109743,
                2109745,
                2110020,
                2110840,
                2110841,
                2110842,
                2110843,
                2110844,
                2110845,
                2110846,
                2110847,
                2110848,
                2110849,
                2110850,
                2110852,
                2110853,
                2110854,
                2110855,
                2110856,
                2110857,
                2110858,
                2110860,
                2110861,
                2110862,
                2110863,
                2110864,
                2110865,
                2110866,
                2110867,
                2110868,
                2110869,
                2110870,
                2110871,
                2110872,
                2110873,
                2110874,
                2110875,
                2110876,
                2110877,
                2110878,
                2110879,
                2110880,
                2110881,
                2110882,
                2110883,
                2110884,
                2110885,
                2110886,
                2110900,
                2110901,
                2110903,
                2110904,
                2110905,
                2110906,
                2110907,
                2110908,
                2110909,
                2110911,
                2110913,
                2110914,
                2110915,
                2110916,
                2110917,
                2110918,
                2110919,
                2110920,
                2110921,
                2110922,
                2110923,
                2110924,
                2110925,
                2110926,
                2110927,
                2110928,
                2110929,
                2110930,
                2110931,
                2110932,
                2110933,
                2110934,
                2110935,
                2110940,
                2110960,
                2110980,
                2111000,
                2111020,
                2111040,
                2111060,
                2111080,
                2111081,
                2111082,
                2111083,
                2111084,
                2111100,
                2111101,
                2111102,
                2111103,
                2111104,
                2111105,
                2111106,
                2111107,
                2111108,
                2111109,
                2111110,
                2111111,
                2111112,
                2111113,
                2111114,
                2111115,
                2111116,
                2111117,
                2111118,
                2111119,
                2111120,
                2111121,
                2111122,
                2111123,
                2111124,
                2111125,
                2111126,
                2111127,
                2111128,
                2111129,
                2111130,
                2111131,
                2111132,
                2111133,
                2111134,
                2111135,
                2111136,
                2111137,
                2111138,
                2111139,
                2111140,
                2111141,
                2111142,
                2111143,
                2111144,
                2111145,
                2111146,
                2111149,
                2111150,
                2111151,
                2111152,
                2111153,
                2111154,
                2111155,
                2111156,
                2111157,
                2111159,
                2111160,
                2111183,
                2111267,
                2111269,
                2111280,
                2111281,
                2111282,
                2111283,
                2111304,
                2111305,
                2111306,
                2111313,
                2111314,
                2111324,
                2111327,
                2112640,
                2112660,
                2112680,
                2112700,
                2112740,
                2112760,
                2112780,
                2112820,
                2112960,
                2112980,
                2113000,
                2113020,
                2113040,
                2113060,
                2113061,
                2113080,
                2113081,
                2113082,
                2113083,
                2113084,
                2113085,
                2113100,
                2113101,
                2113120,
                2113200,
                2113220,
                2113260,
                2113261,
                2113262,
                2113263,
                2113264,
                2113280,
                2113300,
                2113320,
                2113340,
                2113360,
                2113380,
                2113381,
                2113400,
                2113420,
                2113421,
                2113440,
                2113441,
                2113442,
                2113460,
                2113461,
                2113462,
                2113480,
                2113500,
                2113520,
                2113540,
                2113560,
                2113561,
                2115660,
                2115661,
                2118083,
                2124244,
                2124276,
                2125740,
                2125859,
                2126000,
                2126121,
                2126780,
                2127616,
                2129328,
                2129500,
                2129747,
                2129748,
                2129749,
                2129750,
                2129751,
                2129752,
                2129753,
                2129754,
                2129755,
                2129756,
                2129757,
                2129758,
                2129759,
                2129760,
                2129761,
                2129766,
                2129767,
                2129774,
                3000325,
                3000659,
                3000707,
                3000714,
                3000816,
                3001084,
                3001239,
                3001329,
                3001365,
                3001537,
                3001616,
                3001728,
                3001743,
                3001771,
                3001781,
                3001782,
                3001784,
                3001795,
                3001973,
                3001980,
                3002050,
                3002120,
                3002362,
                3002380,
                3002381,
                3002412,
                3002464,
                3002653,
                3002936,
                3002974,
                3003013,
                3003200,
                3003201,
                3003233,
                3003258,
                3003324,
                3003392,
                3003524,
                3003600,
                3003620,
                3003669,
                3003713,
                3003750,
            ]:
                continue
                
            if ":" not in m["MEASUREMENTS"] or m["MEASUREMENTS"] in ["overall: in.; cm"]:
                print("                " + str(m["M_ID"]) + ",")
                continue
                
            mimsy_string.parse_string(m["MEASUREMENTS"])
        except:
            print("                " + str(m["M_ID"]) + ",")
            
            print(m)
            last = m["M_ID"]
            raise

# %%
