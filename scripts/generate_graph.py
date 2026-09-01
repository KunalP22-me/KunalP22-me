import os
import json
import urllib.request
from datetime import datetime, timedelta


# ==========================================
# CONFIGURATION
# ==========================================

USERNAME = "KunalP22-me"
TOKEN = os.environ["GRAPH_TOKEN"]


# ==========================================
# GET LAST 30 DAYS
# ==========================================

today = datetime.utcnow().date()
start_date = today - timedelta(days=29)


# ==========================================
# GITHUB GRAPHQL QUERY
# ==========================================

query = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


payload = {
    "query": query,
    "variables": {
        "username": USERNAME,
        "from": start_date.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z"
    }
}


# ==========================================
# SEND REQUEST TO GITHUB API
# ==========================================

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode("utf-8"),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Contribution-Graph"
    }
)


# ==========================================
# GET RESPONSE
# ==========================================

with urllib.request.urlopen(request) as response:
    data = json.load(response)


# ==========================================
# CHECK FOR API ERRORS
# ==========================================

if "errors" in data:
    print(json.dumps(data["errors"], indent=2))
    raise Exception("Failed to fetch contribution data")


# ==========================================
# EXTRACT CONTRIBUTION DATA
# ==========================================

weeks = (
    data["data"]["user"]
    ["contributionsCollection"]
    ["contributionCalendar"]
    ["weeks"]
)


days = []

for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)


# Keep last 30 days
days = days[-30:]


values = [
    day["contributionCount"]
    for day in days
]


labels = [
    datetime.strptime(
        day["date"],
        "%Y-%m-%d"
    ).day
    for day in days
]


print("Contribution values:", values)


# ==========================================
# DYNAMIC GRAPH MAX
# ==========================================

max_value = max(values) if values else 1

# Directly use maximum contribution count
graph_max = max_value

# Prevent division by zero
if graph_max == 0:
    graph_max = 1


# ==========================================
# SVG DIMENSIONS
# ==========================================

WIDTH = 1200
HEIGHT = 420

LEFT = 90
RIGHT = 1150

TOP = 80
BOTTOM = 350


graph_width = RIGHT - LEFT
graph_height = BOTTOM - TOP


# ==========================================
# CONVERT VALUE TO Y POSITION
# ==========================================

def get_y(value):
    return BOTTOM - (
        value / graph_max
    ) * graph_height


# ==========================================
# CREATE GRAPH POINTS
# ==========================================

points = []

for i, value in enumerate(values):

    x = LEFT + (
        i * graph_width / (len(values) - 1)
    )

    y = get_y(value)

    points.append((x, y))


# ==========================================
# CREATE LINE PATH
# ==========================================

path = ""

for i, (x, y) in enumerate(points):

    if i == 0:
        path += f"M{x:.2f},{y:.2f}"
    else:
        path += f"L{x:.2f},{y:.2f}"


# ==========================================
# CREATE AREA PATH
# ==========================================

area_path = path
area_path += f"L{points[-1][0]:.2f},{BOTTOM}"
area_path += f"L{points[0][0]:.2f},{BOTTOM}Z"


# ==========================================
# START SVG
# ==========================================

svg = f'''<svg
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    fill="none"
    xmlns="http://www.w3.org/2000/svg">

<style>

.title {{
    font-family: Segoe UI, Ubuntu, sans-serif;
    font-size: 20px;
    font-weight: 600;
    fill: #3FB950;
}}

.label {{
    font-family: Segoe UI, Ubuntu, sans-serif;
    font-size: 12px;
    fill: #8B949E;
}}

.axis-title {{
    font-family: Segoe UI, Ubuntu, sans-serif;
    font-size: 13px;
    fill: #8B949E;
}}

.grid {{
    stroke: #30363D;
    stroke-width: 1;
    stroke-opacity: 0.8;
    stroke-dasharray: 2;
}}

.line {{
    fill: none;
    stroke: #3FB950;
    stroke-width: 4;
    stroke-linejoin: round;
    stroke-linecap: round;
}}

.point {{
    fill: #3FB950;
}}

.area {{
    fill: #3FB950;
    fill-opacity: 0.12;
}}

</style>


<!-- TITLE -->

<text
    x="600"
    y="45"
    text-anchor="middle"
    class="title">
    Kunal's Contribution Graph
</text>
'''


# ==========================================
# VERTICAL GRID LINES
# ==========================================

for x, y in points:

    svg += f'''
<line
    x1="{x:.2f}"
    x2="{x:.2f}"
    y1="{TOP}"
    y2="{BOTTOM}"
    class="grid"
/>
'''


# ==========================================
# DYNAMIC Y-AXIS
# ==========================================

# Create 5 equal sections
steps = min(graph_max, 5)

for i in range(steps + 1):

    value = round(
        (graph_max / steps) * i
    )

    y = get_y(value)

    svg += f'''
<line
    x1="{LEFT}"
    x2="{RIGHT}"
    y1="{y:.2f}"
    y2="{y:.2f}"
    class="grid"
/>

<text
    x="80"
    y="{y + 5:.2f}"
    text-anchor="end"
    class="label">
    {value}
</text>
'''


# ==========================================
# ADD AREA
# ==========================================

svg += f'''

<path
    d="{area_path}"
    class="area"
/>
'''


# ==========================================
# ADD LINE
# ==========================================

svg += f'''

<path
    d="{path}"
    class="line"
/>
'''


# ==========================================
# ADD POINTS
# ==========================================

for x, y in points:

    svg += f'''
<circle
    cx="{x:.2f}"
    cy="{y:.2f}"
    r="4"
    class="point"
/>
'''


# ==========================================
# ADD X-AXIS LABELS
# ==========================================

for i, label in enumerate(labels):

    x = points[i][0]

    svg += f'''
<text
    x="{x:.2f}"
    y="375"
    text-anchor="middle"
    class="label">
    {label}
</text>
'''


# ==========================================
# AXIS TITLES
# ==========================================

svg += '''

<text
    x="620"
    y="405"
    text-anchor="middle"
    class="axis-title">
    Days
</text>


<text
    x="25"
    y="215"
    text-anchor="middle"
    class="axis-title"
    transform="rotate(-90 25 215)">
    Contributions
</text>

</svg>
'''


# ==========================================
# CREATE ASSETS FOLDER
# ==========================================

os.makedirs(
    "assets",
    exist_ok=True
)


# ==========================================
# SAVE SVG
# ==========================================

with open(
    "assets/contribution-graph.svg",
    "w",
    encoding="utf-8"
) as file:

    file.write(svg)


print("================================")
print("Contribution graph generated!")
print("Maximum commits:", max_value)
print("================================")
