import os
import datetime
import requests

USERNAME = "luckshayisok"
TOKEN = os.environ["ACCESS_TOKEN"]
HEADERS = {"Authorization": f"bearer {TOKEN}"}
GRAPHQL_URL = "https://api.github.com/graphql"


def run_query(query, variables=None):
    response = requests.post(
        GRAPHQL_URL,
        json={"query": query, "variables": variables or {}},
        headers=HEADERS,
    )
    if response.status_code != 200:
        raise Exception(f"Query failed: {response.status_code} {response.text}")
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data["data"]


def get_profile_stats():
    query = """
    query($login: String!) {
      user(login: $login) {
        followers { totalCount }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes {
            stargazers { totalCount }
          }
        }
      }
    }
    """
    data = run_query(query, {"login": USERNAME})
    user = data["user"]
    total_stars = sum(r["stargazers"]["totalCount"] for r in user["repositories"]["nodes"])
    return {
        "followers": user["followers"]["totalCount"],
        "repos": user["repositories"]["totalCount"],
        "stars": total_stars,
    }


def get_total_commits():
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          restrictedContributionsCount
        }
        createdAt
      }
    }
    """
    created = run_query(
        "query($login: String!) { user(login: $login) { createdAt } }",
        {"login": USERNAME},
    )["user"]["createdAt"]
    start_year = int(created[:4])
    current_year = datetime.datetime.utcnow().year

    total = 0
    for year in range(start_year, current_year + 1):
        from_date = f"{year}-01-01T00:00:00Z"
        to_date = f"{year}-12-31T23:59:59Z"
        data = run_query(query, {"login": USERNAME, "from": from_date, "to": to_date})
        cc = data["user"]["contributionsCollection"]
        total += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
    return total


def get_uptime():
    query = "query($login: String!) { user(login: $login) { createdAt } }"
    created = run_query(query, {"login": USERNAME})["user"]["createdAt"]
    created_date = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
    delta = datetime.datetime.utcnow() - created_date
    years = delta.days // 365
    days = delta.days % 365
    return f"{years}y {days}d"


def render_svg(template_path, output_path, values):
    with open(template_path, "r", encoding="utf-8") as f:
        svg = f.read()
    for key, val in values.items():
        svg = svg.replace("{{" + key + "}}", str(val))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)


def main():
    profile = get_profile_stats()
    commits = get_total_commits()
    uptime = get_uptime()

    values = {
        "REPOS": profile["repos"],
        "STARS": profile["stars"],
        "FOLLOWERS": profile["followers"],
        "COMMITS": commits,
        "UPTIME": uptime,
    }

    render_svg("templates/dark_mode_template.svg", "dark_mode.svg", values)
    render_svg("templates/light_mode_template.svg", "light_mode.svg", values)
    print("SVGs regenerated:", values)


if __name__ == "__main__":
    main()
