import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick


def process_data(path: str):
    with open(path, "r") as f:
        raw_data = json.load(f)["domains"]

    processed_data = {}
    for domain in raw_data:
        if "results" in raw_data[domain]:
            domain_tests = raw_data[domain]["results"]["tests"]
            domain_categories = raw_data[domain]["results"]["categories"]
            processed_data[domain] = {}
            processed_data[domain] = {
                test: domain_tests[test]["verdict"] for test in domain_tests
            } | {
                f"{category}_total": domain_categories[category]["verdict"]
                for category in domain_categories
            }

    df = pd.DataFrame.from_dict(processed_data, orient="index")
    df = df.transpose()

    df["category"] = df.index.map(lambda x: x.split("_")[1])
    df["name"] = df.index.map(lambda x: "_".join(x.split("_")[2:]))
    df = df.set_index(["category", "name"])

    df = df.map(
        lambda x: {
            "failed": "bad",
            "passed": "good",
            "seclevel-bad": "bad",
            "recommendations": "ok",
            "notice": "ok",
            "not-tested": "bad",
            "warning": "ok",
            "phase-out": "ok",
            "na": "good",
            "other": "bad",
            "unreachable": "bad",
            "no-addresses": "ok",
            "redirect": "ok",
            "could-not-test": "bad",
            "no-email": "ok",
            "include": "ok",
            "external": "ok",
            "no-mailservers": "ok",
            "no-mx": "ok",
            "no-null-mx": "ok",
            "other-2": "ok",
            "policy": "bad",
            "untestable": "bad",
        }.get(x, x)
    )

    return df


df_web = process_data("web.json")
df_mail = process_data("mail.json")


# Pre-process web
df_web = (
    df_web.drop(("appsecpriv", "x_xss"))
    .drop(("appsecpriv", "server_header"))
    .drop(("appsecpriv", "set_cookie"))
)

# Pre-process mail
df_mail.loc[("auth", "spf_policy"), :] = df_mail.loc[("auth", "spf_policy"), :].map(
    lambda x: "bad" if x in ["all", "max-lookups"] else x
)


def process_results(df: pd.DataFrame):
    new_df = df

    new_df = new_df.apply(lambda x: pd.Series(x).value_counts(), axis=1)
    new_df = new_df.fillna(0).map(round)
    new_df = new_df * 100 / sum(new_df.iloc[0])

    new_df = new_df[["good", "ok", "bad"]]

    return new_df


df_web_processed = process_results(df_web)
df_mail_processed = process_results(df_mail)

# Post-process web
df_web_processed = df_web_processed.sort_values(by=["category", "bad"], ascending=False)

# Post-process mail
df_mail_processed = df_mail_processed.sort_values(
    by=["category", "bad"], ascending=False
)


ax = df_web_processed.loc[pd.IndexSlice[:, ["total"]], :][::-1].plot.bar(
    color={"bad": "red", "good": "green", "ok": "orange"}, figsize=(10, 5), rot=0
)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.get_figure().savefig("web_generic.png", bbox_inches="tight")
ax = df_web_processed.sort_values(by=["good", "ok", "bad"], ascending=True).plot.barh(
    color={"bad": "red", "good": "green", "ok": "orange"}, figsize=(10, 9), stacked=True
)
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.get_figure().savefig("web_detailed.png", bbox_inches="tight")


ax = df_mail_processed.loc[pd.IndexSlice[:, ["total"]], :][::-1].plot.bar(
    color={"bad": "red", "good": "green", "ok": "orange"}, figsize=(10, 5), rot=0
)
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.get_figure().savefig("mail_generic.png", bbox_inches="tight")
ax = df_mail_processed.sort_values(by=["good", "ok", "bad"], ascending=True).plot.barh(
    color={"bad": "red", "good": "green", "ok": "orange"}, figsize=(10, 9), stacked=True
)
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.get_figure().savefig("mail_detailed.png", bbox_inches="tight")
