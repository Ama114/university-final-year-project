from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__, template_folder='pages' , static_folder='static')

df = pd.read_csv("odi_batting.csv", encoding="ISO-8859-1")
df['Runs'] = pd.to_numeric(df['Runs'], errors='coerce')

categorical_columns = ['Player Name', 'Opposition', 'Ground', 'Pitch Type', 'Ball type', 'bowler', 'Dismissal']
label_encoders = {}
for col in categorical_columns:
    le = LabelEncoder()
    df[col] = df[col].astype(str)
    df[col] = le.fit_transform(df[col])
    label_encoders[col] = le

@app.route('/')
def home():
    return render_template('index.html')
 

@app.route('/bowling')
def bowling():
    return render_template('bowling.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Demo credentials
        if username == 'admin' and password == 'admin123':
            return redirect(url_for('home'))
        else:
            error = 'Invalid username or password!'
    return render_template('login.html', error=error)

@app.route('/comparison')
def comparison():
    return render_template('comparison.html')

@app.route('/batting', methods=['GET', 'POST'])
def batting():
    
    players = sorted(label_encoders['Player Name'].classes_)
    filter_type = request.form.get('filter_type', 'Player & Ground')
    selected_player = request.form.get('player', players[0])
    selected = request.form.get('selected', None)

  


    # Filter grounds/oppositions for selected player
    player_enc = label_encoders['Player Name'].transform([selected_player])[0]
    if filter_type == "Player & Ground":
        values = df[df['Player Name'] == player_enc]['Ground']
        options = sorted(label_encoders['Ground'].inverse_transform(values.unique()))
        label = "Ground"
    else:
        values = df[df['Player Name'] == player_enc]['Opposition']
        options = sorted(label_encoders['Opposition'].inverse_transform(values.unique()))
        label = "Opposition"

    # Output calculation (only if all selected)
    summary = None
    img = None
    if selected:
        if filter_type == "Player & Ground":
            ground_enc = label_encoders['Ground'].transform([selected])[0]
            filtered = df[(df['Player Name'] == player_enc) & (df['Ground'] == ground_enc)]
            context = f"{selected_player} at {selected}"
        else:
            opp_enc = label_encoders['Opposition'].transform([selected])[0]
            filtered = df[(df['Player Name'] == player_enc) & (df['Opposition'] == opp_enc)]
            context = f"{selected_player} vs {selected}"

        total_matches = len(filtered)
        total_runs = filtered['Runs'].sum()
        avg_runs = round(filtered['Runs'].mean(), 2) if not filtered.empty else 'N/A'
        dismissal_mode = label_encoders['Dismissal'].inverse_transform(
            [filtered['Dismissal'].mode().iloc[0]])[0] if not filtered['Dismissal'].mode().empty else "N/A"
        top_venue = label_encoders['Ground'].inverse_transform(
            [filtered['Ground'].mode().iloc[0]])[0] if not filtered['Ground'].mode().empty else "N/A"
        most_bowler_mode = label_encoders['bowler'].inverse_transform(
            [filtered['bowler'].mode().iloc[0]])[0] if not filtered['bowler'].mode().empty else "N/A"
        vulnerable_pitch = label_encoders['Pitch Type'].inverse_transform(
            [filtered['Pitch Type'].mode().iloc[0]])[0] if not filtered['Pitch Type'].mode().empty else "N/A"
        vulnerable_ball = filtered['dismissal shot'].mode().iloc[0] if 'dismissal shot' in filtered.columns and not filtered['dismissal shot'].mode().empty else "N/A"

        # Plot: Run Distribution
        if not filtered['Runs'].dropna().empty:
            plt.figure(figsize=(8, 4))
            sns.histplot(filtered['Runs'].dropna(), kde=True, bins=15)
            plt.title(f'Run Distribution for {context}')
            plt.xlabel('Runs')
            plt.ylabel('Frequency')
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            img = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

        summary = {
            'context': context,
            'total_matches': total_matches,
            'total_runs': total_runs,
            'avg_runs': avg_runs,
            'dismissal_mode': dismissal_mode,
            'top_venue': top_venue,
            'most_bowler_mode': most_bowler_mode,
            'vulnerable_pitch': vulnerable_pitch,
            'vulnerable_ball': vulnerable_ball
        }

    return render_template(
        'batting.html',
        players=players,
        filter_type=filter_type,
        selected_player=selected_player,
        options=options,
        selected=selected,
        label=label,
        summary=summary,
        img=img
    )

if __name__ == '__main__':
    app.run(debug=True)