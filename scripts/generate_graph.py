import os
import json
import urllib.request
from datetime import datetime, timedelta

TOKEN = os.environ["GITHUB_TOKEN"]

# Last 30 days
today = datetime.utcnow().date()
start_date = today - timedelta(days=29)

query = """
query($from: DateTime!, $to: DateTime!) {
  viewer {
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
        "from": start_date.isoformat() + "T00:00:00Z",
        "to": today.isoformat() + "T23:59:59Z"
    }
}

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps(payload).encode(),
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
)

with urllib.request.urlopen(request) as response:
    data = json.load(response)

# Extract contribution days
weeks = data["data"]["viewer"]["contributionsCollection"]["contributionCalendar"]["weeks"]

days = []

for week in weeks:
    for day in week["contributionDays"]:
        days.append(day)

# Keep last 30 days
days = days[-30:]

values = [day["contributionCount"] for day in days]
labels = [datetime.fromisoformat(day["date"]).day for day in days]

max_value = max(values) if max(values) > 0 else 5

# Round graph maximum
if max_value <= 5:
    graph_max = 5
elif max_value <= 10:
    graph_max = 10
elif max_value <= 15:
    graph_max = 15
elif max_value <= 20:
    graph_max = 20
else:
    graph_max = ((max_value // 5) + 1) * 5


# SVG dimensions
WIDTH = 1200
HEIGHT = 420

LEFT = 90
RIGHT = 1150
TOP = 80
BOTTOM = 350

graph_width = RIGHT - LEFT
graph_height = BOTTOM - TOP


# Convert contribution value to Y coordinate
def get_y(value):
    return BOTTOM - (value / graph_max) * graph_height


# Generate points
points = []

for i, value in enumerate(values):
    x = LEFT + (i * graph_width / (len(values) - 1))
    y = get_y(value)

    points.append((x, y))


# Create SVG path
path = ""

for i, (x, y) in enumerate(points):
    if i == 0:
        path += f"M{x:.2f},{y:.2f}"
    else:
        path += f"L{x:.2f},{y:.2f}"


# Area under graph
area_path = path
area_path += f"L{points[-1][0]:.2f},{BOTTOM}"
area_path += f"L{points[0][0]:.2f},{BOTTOM}Z"


svg = f'''<svg
    width="{WIDTH}"
    height="{HEIGHT}"
    viewBox="0 0 {WIDTH} {HEIGHT}"
    fill="none"
    xmlns="http://www.w3.org/2000/svg">

<style>

body {{
    font-family: Segoe UI, Ubuntu, sans-serif;
}}

.title {{
    font-size: 20px;
    font-weight: 600;
    fill: #539BF5;
}}

.label {{
    font-size: 12px;
    fill: #ADBAC7;
}}

.axis-title {{
    font-size: 13px;
    fill: #ADBAC7;
}}

.grid {{
    stroke: #ADBAC7;
    stroke-width: 1;
    stroke-opacity: 0.25;
    stroke-dasharray: 2;
}}

.line {{
    fill: none;
    stroke: #ADBAC7;
    stroke-width: 4;
    stroke-linejoin: round;
    stroke-linecap: round;
}}

.point {{
    fill: #539BF5;
}}

.area {{
    fill: #ADBAC7;
    fill-opacity: 0.10;
}}

</style>


<!-- Background -->

<rect
    x="0"
    y="0"
    width="1200"
    height="420"
    rx="6"
    fill="#24292F"
    stroke="#444C56"
    stroke-width="1"
/>


<!-- Title -->

<text
    x="600"
    y="45"
    text-anchor="middle"
    class="title">
    Kunal's Contribution Graph
</text>


<!-- Vertical grid lines -->
'''

# Vertical grid lines
for i in range(len(points)):
    x = points[i][0]

    svg += f'''
<line
    x1="{x:.2f}"
    x2="{x:.2f}"
    y1="{TOP}"
    y2="{BOTTOM}"
    class="grid"
/>
'''

# Horizontal grid lines
steps = 5

for i in range(steps + 1):

    value = int((graph_max / steps) * i)
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

# Graph area and line
svg += f'''

<!-- Area -->

<path
    d="{area_path}"
    class="area"
/>


<!-- Contribution line -->

<path
    d="{path}"
    class="line"
/>
'''

# Points
for x, y in points:

    svg += f'''
<circle
    cx="{x:.2f}"
    cy="{y:.2f}"
    r="4"
    class="point"
/>
'''

# X axis labels
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

# Axis titles
svg += '''

<!-- Axis titles -->

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


# Save SVG
os.makedirs("assets", exist_ok=True)

with open(
    "assets/contribution-graph.svg",
    "w",
    encoding="utf-8"
) as file:

    file.write(svg)


print("Contribution graph generated successfully!")
