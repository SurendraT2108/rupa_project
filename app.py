from flask import Flask, request, redirect, render_template_string
import pandas as pd
import os
from collections import Counter

app = Flask(__name__)

FILE = "placement_data.csv"

# Load or create CSV
if os.path.exists(FILE):
    df = pd.read_csv(FILE, on_bad_lines="skip")
else:
    df = pd.DataFrame(columns=["Name", "Department", "Company", "Package", "Status"])
    df.to_csv(FILE, index=False)

# ---------------------------------------------------------
# HTML + CSS COMBINED INSIDE TEMPLATE STRING
# ---------------------------------------------------------
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Placement Tracker</title>

    <style>
        * {box-sizing: border-box; font-family: 'Segoe UI'; transition: 0.3s;}
        body {background: linear-gradient(135deg,#1d2671,#c33764); padding: 30px;}

        h1 {text-align:center; color:white; margin-bottom:20px; font-size:40px; 
            text-shadow:3px 3px 8px rgb(8, 118, 173);}

        .filter-bar, .stat-box, table {
            background: rgba(255,255,255,0.15);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        .filter-bar {display:flex; justify-content:center; gap:15px; padding:20px; margin-bottom:30px;}
        .filter-bar input, .filter-bar select {padding:10px; border-radius:6px; border:none; outline:none;}

        .filter-bar button {
            padding:10px 25px; border:none; color:white; font-weight:bold;
            background: linear-gradient(45deg,#ff416c,#f90707); border-radius:6px; cursor:pointer;
        }
        .filter-bar button:hover {transform:scale(1.1); background:linear-gradient(45deg,#eb2805,#ff416c);}

        .stats {display:flex; justify-content:center; gap:20px; margin-bottom:40px;}
        .stat-box {padding:20px; text-align:center; color:white; width:150px;}
        .stat-box:hover {transform:translateY(-8px) scale(1.05); background:linear-gradient(45deg,#36d1dc,#5b86e5);}

        h2 {color:white; text-align:center; font-size:40px; text-shadow:#36d1dc 1px 1px 5px;}

        table {width:100%; border-collapse:collapse;}
        th {padding:12px; color:white; background:linear-gradient(45deg,#141e30,#243b55);}
        td {padding:10px; text-align:center; font-weight:bold;}

        tr:hover {background:rgba(255,255,255,0.2); transform:scale(1.01);}
        .placed {color:#033c1b; font-weight:bold;}
        .notplaced {color:#e80606; font-weight:bold;}

        .highlight {background:linear-gradient(45deg,#f7971e,#00f7ff); color:black; font-weight:bold;}

        .popup {
            position: fixed; top: 30px; right: 30px;
            background: linear-gradient(45deg,#00b09b,#96c93d);
            color: white; padding: 15px 40px; border-radius: 10px;
            font-weight: bold; animation: popupFade 0.5s ease-in-out;
        }

        @keyframes popupFade {from {opacity:0; transform:translateY(-20px);} to {opacity:1; transform:translateY(0);}}

        .progress-container {
            width:80%; margin:auto; background:rgba(255,255,255,0.2);
            border-radius:20px; overflow:hidden; margin-bottom:40px;
        }
        .progress-bar {
            height:25px; background:linear-gradient(45deg,#00c6ff,#0072ff);
            text-align:center; color:white; font-weight:bold; line-height:25px;
            animation: grow 2s;
        }
        @keyframes grow {from {width:0;} to {width:100%;}}
    </style>

</head>

<body onload="showMessage('{{ message }}')">

<script>
    function showMessage(msg){
        if(msg){ alert(msg); }
    }
</script>

<h1>Placement Tracker Dashboard</h1>

{% if message %}
<div id="popup" class="popup">{{ message }}</div>
<script>
    setTimeout(()=>{ document.getElementById("popup").style.display="none"; }, 3000)
</script>
{% endif %}

<!-- SEARCH BAR -->
<form method="GET" action="/" class="filter-bar">
    <input type="text" name="name" placeholder="Enter Student Name">
    <button type="submit">Search</button>
</form>

<!-- ADD STUDENT -->
<form method="POST" action="/add" class="filter-bar">
    <input type="text" name="name" placeholder="Name" required>
    <input type="text" name="department" placeholder="Department" required>
    <input type="text" name="company" placeholder="Company" required>
    <input type="number" step="0.1" name="package" placeholder="Package" required>

    <select name="status">
        <option value="Placed">Placed</option>
        <option value="Not Placed">Not Placed</option>
    </select>

    <button type="submit">Enter</button>
</form>

<!-- DASHBOARD -->
<div class="stats">
    <div class="stat-box"><h3>{{ total }}</h3>Total</div>
    <div class="stat-box"><h3>{{ placed }}</h3>Placed</div>
    <div class="stat-box"><h3>{{ not_placed }}</h3>Not Placed</div>
    <div class="stat-box"><h3>{{ percentage }}%</h3>Percent</div>
</div>

<div class="progress-container">
    <div class="progress-bar" style="width:{{percentage}}%">{{percentage}}%</div>
</div>

<h2>Student Details</h2>

<table>
<tr>
    <th>Name</th>
    <th>Department</th>
    <th>Company</th>
    <th>Package</th>
    <th>Status</th>
</tr>

{% if students %}
    {% for student in students %}
    <tr class="{% if search_name and search_name.lower() == student.Name.lower() %}highlight{% endif %}">
        <td>{{ student.Name }}</td>
        <td>{{ student.Department }}</td>
        <td>{{ student.Company }}</td>
        <td>{{ student.Package }}</td>
        <td class="{{ 'placed' if student.Status == 'Placed' else 'notplaced' }}">{{ student.Status }}</td>
    </tr>
    {% endfor %}
{% else %}
<tr><td colspan="5">No student found</td></tr>
{% endif %}
</table>

</body>
</html>
"""

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    global df

    search_name = request.args.get("name", "").strip()
    if search_name:
        filtered_df = df[df["Name"].str.contains(search_name, case=False, na=False)]
        message = "Student Found" if not filtered_df.empty else "Student Not Found"
    else:
        filtered_df = df
        message = ""

    total = len(df)
    placed_df = df[df["Status"] == "Placed"]
    placed = len(placed_df)
    not_placed = total - placed
    percentage = round((placed / total) * 100, 2) if total > 0 else 0

    return render_template_string(
        TEMPLATE,
        students=filtered_df.to_dict(orient="records"),
        total=total, placed=placed, not_placed=not_placed,
        percentage=percentage, search_name=search_name, message=message
    )


@app.route("/add", methods=["POST"])
def add_student():
    global df
    new_data = {
        "Name": request.form["name"],
        "Department": request.form["department"],
        "Company": request.form["company"].replace(",", ""),
        "Package": float(request.form["package"]),
        "Status": request.form["status"]
    }

    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(FILE, index=False)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
