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
query = "SELECT M_ID, MEASUREMENTS FROM CATALOGUE WHERE M_ID > {0} AND MEASUREMENTS IS NOT NULL ORDER BY M_ID ASC FETCH NEXT 10000 ROWS ONLY"
'''
query = """
SELECT
    M_ID
    ,MEASUREMENTS
FROM CATALOGUE 
WHERE M_ID IN (
2354,
128980,
143481,
148269,
1000049,
1000459,
1000603,
1001053,
1001867,
2001792,
2002986,
2007638,
2009816,
2010534,
2010579,
2012641,
2012725,
2012727,
2013253,
2100800,
2116676,
2129683,
3000196,
3001991,
3007082,
3008170,
3012332,
4002625,
4005052,
4102371,
4104779,
4106174,
4108085,
4111177,
5002189,
5002464,
5013860,
5015025,
5016238,
5017470,
5017666,
5017731,
5019761,
5022308,
5028733,
5037422,
5037742,
5043334,
5050240,
5052353
) AND {0} = {0}
ORDER BY M_ID ASC"""
'''

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
    + pp.Optional(
        pp.oneOf(
            [
                "in",
                '"',
                "inches",
                "ft",
                "'",
                "cm",
                "m",
                "mm",
                "g",
                "gm",
                "deg",
                "minutes",
                "seconds",
            ]
        )("unit")
        + pp.Optional(".")
    )
)

if is_notebook:
    debug = True
    (ok, res) = dim.run_tests(
        [
            "15/16 in",
            "5 3/4 in",
            "31 inches",
            "12 in",
            '26 3/4"',
            "14.6 cm",
            "11 cm",
            "3",
            "31 7/8",
            "125.7",
            "81",
            "17 ft",
            "26 3/4'",
            "5.2 m",
            "47 13/16 in.",
            "17mm",
            "3.293g",
            "3.0 gm.",
            "10 deg.",
            "5 minutes",
            "09 seconds",
        ],
        print_results=False,
        full_dump=False,
    )
    print("Success!" if ok and not debug else res)

vol = pp.Group(
    pp.OneOrMore(
        pp.Optional(pp.Suppress("x"))
        + dim("dimensions*")
        + pp.Optional(pp.Suppress("x"))
    )
)


dimensions = pp.Group(
    pp.Optional(
        pp.Group(
            pp.Word(pp.alphanums + "/" + "-" + "&" + "?" + "'" + " ").set_parse_action(
                pp.token_map(str.strip)
            )
            + pp.Optional(pp.Suppress(";") + pp.Word(pp.alphas + "-"))
            + pp.Optional(
                pp.Suppress(",")
                + pp.Word(pp.alphas + "/" + " ").set_parse_action(
                    pp.token_map(str.strip)
                )
            )
            + pp.Optional(
                pp.Combine(
                    "("
                    + pp.Word(pp.alphas + "-" + " ").set_parse_action(
                        pp.token_map(str.strip)
                    )
                    + ")"
                )
            )
        )("type")
        + pp.Suppress(":")
    )
    + pp.Optional(pp.Suppress(":"))
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
            ": 1 1/4 x 2 3/4 x 1 1/2 in.",
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
            "image: 11 in x 14 in ; 27.9 cm x 35.6 cm x",
        ],
        print_results=False,
        full_dump=False,
    )
    print("Success!" if ok and not debug else res)

mimsy_string = pp.OneOrMore(dimensions("facets*"))

if is_notebook:
    mimsy_string.create_diagram("parser.html", show_results_names=True)

    ex = mimsy_string.parse_string("17mm; 3.293g")
    print(ex)
    print(ex.as_dict())

    (ok, res) = mimsy_string.run_tests(
        """

        # M_ID: 2354
        Overall: 28 1/8 in x 10 1/2 in x 2 5/8 in; 71.4 cm x 26.7 cm x 6.7 cm

        # M_ID: 128980
        Overall: 11 7/8 in x 12 1/4 in x 12 1/4 in; 30.2 cm x 31.1 cm x 31.1 cm

        # M_ID: 143481
        Overall: 1 5/8 in x 7/8 in x 1/4 in; 4.1 cm x 2.2 cm x .6 cm

        # M_ID: 148269
        Overall: 15 5/8 in x 9 5/16 in x 8 11/16 in x 9 1/2 in; 39.7 cm x 23.7 cm x 22.1 cm x 24.1 cm

        # M_ID: 1000049
        overall: 20 3/4 in x 28 5/8 in; 52.705 cm x 72.7075 cm

        # M_ID: 1000459
        overall: 24 3/4 in x 43 in; 62.865 cm x 109.22 cm

        # M_ID: 1000603
        overall: 7 13/16 in x 9 11/16 in; 19.84375 cm x 24.60625 cm

        # M_ID: 1001053
        overall: 20 1/4 in x 24 in x 1 1/4 in; 51.435 cm x 60.96 cm x 3.175 cm

        # M_ID: 1001867
        Mat: 16 in x 16 in; 40.6 cm x 40.6 cm; Image: 10 in x 10 in; 25.4 cm x 25.4 cm

        # M_ID: 2001792
        mount: 19 1/16 x 13 1/8 in.; 48.4188 x 33.3375 cm; sheet/image: 9 3/16 x 6 5/16 in.; 23.3363 x 16.0338 cm

        # M_ID: 2002986
        sheet: 16 x 19 15/16 in.; 40.64 x 50.6413 cm; image: 12 x 17 1/2 in.; 30.48 x 44.45 cm

        # M_ID: 2007638
        sheet: 7 x 8 1/2 in.; 17.78 x 21.59 cm

        # M_ID: 2009816
        3 x 3 1/8 in. diameter; 7.62 x 7.9375 cm

        # M_ID: 2010534
        10 x 8 3/4 in.; 25.4 x 22.225 cm

        # M_ID: 2010579
        19 x 44 in.; 48.26 x 111.76 cm

        # M_ID: 2012641
        1/8 x 1 3/4 in. diameter; .3175 x 4.445 cm

        # M_ID: 2012725
        1/16 x 3/4 in. irregular diameter; .1588 x 1.905 cm

        # M_ID: 2012727
        1/16 x 3/4 in. irregular diameter; .1588 x 1.905 cm

        # M_ID: 2013253
        length: 4 1/4 in.; 10.795 cm

        # M_ID: 2100800
        3 x 2 7/16 x 1 1/8 in.; 7.62 x 6.1913 x 2.8575 cm

        # M_ID: 2116676
        sheet: 19 1/8 x 24 1/8 in.; 48.5775 x 61.2775 cm

        # M_ID: 2129683
         3/4 in. diameter; 1.905 cm, weight 3.0 gm., diexis 10 deg.

        # M_ID: 3000196
        overall: 6 in x 2 5/8 in; 15.2 cm x 6.7 cm

        # M_ID: 3001991
        overall: 8 1/8 x 4 5/8 in.; 20.6502 x 11.7602 cm

        # M_ID: 3007082
        overall: 18 1/2 in.; 46.99 cm

        # M_ID: 3008170
        overall: 4 3/4 x 2 3/8 in.

        # M_ID: 3012332
        overall: 5 in x 6 in; 12.7 cm x 15.24 cm

        # M_ID: 4002625
        frame: 31 1/8 x 37 1/8 x 1 3/4 in.; 79.0575 x 94.2975 x 4.445 cm

        # M_ID: 4005052
        Overall: 1 1/8 in x 3 1/2 in x 2 3/8 in; 2.9 cm x 8.9 cm x 6 cm

        # M_ID: 4102371
        17mm; 3.293g

        # M_ID: 4104779
        overall: 4 1/8 in x 3 1/4 in x 2 1/4 in; 10.4775 cm x 8.255 cm x 5.715 cm

        # M_ID: 4106174
        : 1 1/4 x 2 3/4 x 1 1/2 in.; 3.175 x 6.985 x 3.81 cm

        # M_ID: 4108085
        Sheet: 28 in x 28 in; 71.1 cm x 71.1 cm

        # M_ID: 4111177
        overall: 3/8 in x 2 3/8 in; .9525 cm x 6.0325 cm

        # M_ID: 5002189
        overall: 1 7/16 x 5/8 x 1/8 in.; 3.7 x 1.6 x .3 cm

        # M_ID: 5002464
        overall: 2 x 3/4 x 3/4 in.; 5.1 x 1.9 x 1.9 cm

        # M_ID: 5013860
        overall: 2 1/4 in x 5 1/2 in; 5.715 cm x 13.97 cm

        # M_ID: 5015025
        Frame: 21 1/8 x 17 3/16 x 1 in; 53.7 x 43.7 x 2.5 cm; Mat: 17 7/8 x 14 in; 45.4 x 35.6 cm; Sheet: 12 7/8 x 
10 1/8 in; 32.7 x 25.7 cm

        # M_ID: 5016238
        5 minutes; 09 seconds

        # M_ID: 5017470
        overall: 3 1/8 in x 3 1/8 in x 7/8 in; 7.9375 cm x 7.9375 cm x 2.2225 cm

        # M_ID: 5017666
        sheet: 11 in x 8 1/2 in; 27.94 cm x 21.59 cm

        # M_ID: 5017731
        Sheet: 14 in x 11 in; 35.56 cm x 27.94 cm; Image: 7 1/2 in x 6 1/2 in; 19.05 cm x 16.51 cm

        # M_ID: 5019761
        Overall: 6 1/4 x 4 3/4 x 7/8 in; 15.9 x 12.1 x 2.2 cm

        # M_ID: 5022308
        Overall: 1 13/16 in x 1 3/8 in x 15/16 in; 4.6 cm x 3.5 cm x 2.4 cm

        # M_ID: 5028733
        Sight: 11 1/16 in x 8 1/8 in; 28.1 cm x 20.6 cm

        # M_ID: 5037422
        Overall: 3 x 6 3/8 in; 7.6 x 16.2 cm

        # M_ID: 5037742
        overall: 3 1/4 in x 4 3/8 in x 2 1/4 in; 8.3 cm x 11.1 cm x 5.7 cm

        # M_ID: 5043334
        Overall: 3 1/4 in x 4 in x 1/2 in; 8.3 cm x 10.2 cm x 1.3 cm

        # M_ID: 5050240
        Sheet: 12 3/4 in x 18 in; 32.4 cm x 45.7 cm; Image: 8 7/8 in x 13 3/4 in; 22.5 cm x 34.9 cm

        # M_ID: 5052353
        Frame: 11 1/2 x 17 1/2 in; 29.2 x 44.4 cm; Sight: 5 5/8 x 11 5/8 in; 14.3 x 29.5 cm""",
        print_results=False,
        full_dump=False,
    )
    if not debug:
        print("Success!" if ok else res)

# %%
from copy import deepcopy
from datetime import datetime
from pathlib import Path

last = 0
output = Path("output", datetime.now().strftime("%m%d%H%M%S"))
output.mkdir(parents=True, exist_ok=False)
for batch_no, batch in enumerate(measurements(last - 1)):
    if is_notebook:
        print(f"{batch_no}...")

    results = []
    for item in batch.to_dicts():
        base_res = {"M_ID": item["M_ID"], "MEASUREMENTS": item["MEASUREMENTS"]}

        (ok, err) = mimsy_string.run_tests(
            item["MEASUREMENTS"], print_results=False, full_dump=False
        )
        if not ok:
            base_res["Parse Error"] = str(err)

        try:
            dimensions = mimsy_string.parse_string(item["MEASUREMENTS"])
        except pp.ParseException:
            results.append(base_res)
        except:
            last = item["M_ID"]

        for f in dimensions["facets"]:
            f_res = deepcopy(base_res)
            if "type" in f:
                types = f["type"]
                if len(types) > 0:
                    f_res["Type"] = types[0]
                if len(types) > 1:
                    f_res["Type (additional)"] = " ".join(f["type"][1:])

            f_res["Too Many Dimensions"] = len(f["measurements"]) > 5

            for m in f["measurements"]:
                m_res = deepcopy(f_res)
                units = set()
                for i, d in enumerate(m["dimensions"]):
                    if "value" in d:
                        m_res[f"Dimension{i+1}"] = d["value"]
                    if "unit" in d:
                        units.add(d["unit"])

                m_res["Inconsistent Units"] = len(units) > 1

                m_res[f"Units"] = ", ".join(units)
                results.append(m_res)

    pl.DataFrame(
        results,
        schema=[
            ("M_ID", pl.Int64),
            ("MEASUREMENTS", pl.String),
            ("Parse Error", pl.String),
            ("Inconsistent Units", pl.Boolean),
            ("Too Many Dimensions", pl.Boolean),
            ("Type", pl.String),
            ("Type (additional)", pl.String),
            ("Units", pl.String),
            ("Dimension1", pl.String),
            ("Dimension2", pl.String),
            ("Dimension3", pl.String),
            ("Dimension4", pl.String),
            ("Dimension5", pl.String),
        ],
        # ).write_csv(output / f"{batch_no:03d}.csv")
    ).write_parquet(output / f"{batch_no:03d}.parquet")

if is_notebook:
    print(f"{output} done!")

# %%
if is_notebook:
    all_rows = pl.scan_parquet(output)
    all_rows.filter(pl.col("Parse Error").is_not_null()).sink_csv(
        output / "parse_errors.csv"
    )

# %%
