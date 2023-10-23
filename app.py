from flask import Flask, render_template, redirect, url_for, flash,request, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager,UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from getStats import *
from webforms import *
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import os
import math

app = Flask(__name__)
# Old SQLite database 
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Cr7<3aA1!@localhost/usersList'
app.config['SECRET_KEY'] = "secretpasswordkey"


# Initialize function scheduler
scheduler = BackgroundScheduler(daemon=True)

#Initialize database
db=SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class Picks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game = db.Column(db.String(20),nullable=False)
    winner = db.Column(db.String(10), nullable=False)
    best_scorer = db.Column(db.String(60), nullable=False)
    best_passer = db.Column(db.String(60), nullable=False)
    best_rebounder = db.Column(db.String(60), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    correctPicks = db.Column(db.Integer)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('Users', backref=db.backref('game_picks', lazy=True))

# Function to calculate picks points
def calcPoints():
    users = Users.query.all()
    date = datetime.utcnow()
    string_date = months[date.month-1]+str(date.day)
    getDailyBoxscore(date.day,date.month,date.year)
    updatePlayerStats(date)
    dailyLeaders = getDailyLeaders(date.day,date.month)
    for user in users:
        points = 0
        winnerPoints = 0
        scorerPoints = 0
        passerPoints = 0
        rebounderPoints = 0
        ngames = 0
        user_picks = Picks.query.filter_by(user_id=user.id,date=string_date)
        for pick in user_picks:
            ngames += 1
            winnerCheck = False
            ptsCheck = False
            astCheck = False
            rebCheck = False
            correctPicks = 0
            game = pick.game
            if str(dailyLeaders[game]["Winner"]) == str(pick.winner):
                points += 1
                winnerPoints += 1
                correctPicks += 1
                winnerCheck = True
            if any(str(pick.best_scorer) == str(player) for player in dailyLeaders[game]["PTS"]):
                points += 1
                scorerPoints += 1
                correctPicks = correctPicks*10 + 1
                ptsCheck = True
            else:
                correctPicks = correctPicks*10
            if any(str(pick.best_passer) == str(player) for player in dailyLeaders[game]["AST"]):
                points += 1
                passerPoints += 1
                correctPicks = correctPicks*10 + 1
                astCheck = True
            else:
                correctPicks = correctPicks*10
            if any(str(pick.best_rebounder) == str(player) for player in dailyLeaders[game]["REB"]):
                points += 1
                rebounderPoints += 1
                correctPicks = correctPicks*10 + 1
                rebCheck = True
            else:
                correctPicks = correctPicks*10
            pick.correctPicks = correctPicks
            if winnerCheck and ptsCheck and astCheck and rebCheck:
                points += 1
                user.perfectGames += 1
            db.session.commit()
        if winnerPoints == ngames:
            points += math.ceil(ngames*1.2)
        if scorerPoints == ngames:
            points += math.ceil(ngames*1.2)
        if passerPoints == ngames:
            points += math.ceil(ngames*1.2)
        if rebounderPoints == ngames:
            points += math.ceil(ngames*1.2)
        if user.points == None:
            user.points = points
        else:
            user.points += points
        db.session.commit()
    flash("Points have been updated!!!")

def updatePlayerStats(date):
    str_date = date.strftime('%b')
    str_date = str_date+(str(date.day))
    games = Games.query.filter_by(date=str_date)
    statsOTD = getStatsOTD(date.day,date.month)
    for game in games:
        home_team = Teams.query.filter_by(id=game.team1_id).first()
        away_team = Teams.query.filter_by(id=game.team2_id).first()
        home_score = 0
        away_score = 0
        homePlayerStats = statsOTD["{} vs {}".format(home_team.shortTeamName,away_team.shortTeamName)][home_team.shortTeamName]
        for player in homePlayerStats.keys():
            home_score += homePlayerStats[player]["PTS"]
            player_db = Player.query.filter_by(name=player).first()
            if player_db != None:
                player_db.points += homePlayerStats[player]["PTS"]
                player_db.assists += homePlayerStats[player]["AST"]
                player_db.rebounds += homePlayerStats[player]["REB"]
                player_db.games += 1 
        awayPlayerStats = statsOTD["{} vs {}".format(home_team.shortTeamName,away_team.shortTeamName)][away_team.shortTeamName]
        for player in awayPlayerStats.keys():
            away_score += awayPlayerStats[player]["PTS"]
            player_db = Player.query.filter_by(name=player).first()
            if player_db != None:
                player_db.points += awayPlayerStats[player]["PTS"]
                player_db.assists += awayPlayerStats[player]["AST"]
                player_db.rebounds += awayPlayerStats[player]["REB"]
                player_db.games += 1
        game.score1 = home_score
        game.score2 = away_score
        if home_score > away_score:
            home_team.wins += 1
            away_team.losses += 1
        else:
            away_team.wins += 1
            home_team.losses += 1
        db.session.commit()

# Create Teams Model
class Teams(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shortTeamName = db.Column(db.String(10), unique=True, nullable=False)
    teamName = db.Column(db.String(50), unique=True, nullable=False)
    wins = db.Column(db.Integer)
    losses = db.Column(db.Integer)

# Function to add teams to database table
def load_team_data_to_db():
    for i in range(len(teams)):
        team_name = teams[i]
        short_team_name = teamsshort[i]
        team = Teams(shortTeamName=short_team_name, teamName = team_name, wins=0, losses=0)
        db.session.add(team)
    db.session.commit()

# Create Player Model
class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    link = db.Column(db.String(250), nullable=False)
    games = db.Column(db.Integer)
    points = db.Column(db.Integer)
    rebounds = db.Column(db.Integer)
    assists = db.Column(db.Integer)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    teams = db.relationship('Teams', backref=db.backref("players", lazy=True))

# Pass players to database
def load_players_to_db():
    for team in teamsshort:
        data = getPlayersfromTeamPage(team)
        players_data = data["Players"]
        for player_data in players_data:
            player = Player.query.filter_by(name=player_data["Player"]).first()
            if player is None:  # Player is not on database, gets added
                team_id = Teams.query.filter_by(shortTeamName=team).first().id
                player = Player(name=player_data["Player"],link=player_data["Link"],games=0,points=0,rebounds=0,assists=0,team_id=team_id)
                db.session.add(player)
            else: # Player is in the database
                player_team = Teams.query.filter_by(id=player.team_id).first()
                if team != Teams.query.filter_by(shortTeamName=player_team.shortTeamName).first().shortTeamName: # Player in the database has been traded(changed teams)
                    player_to_delete = Player.query.filter_by(name=player.name,team_id=player.team_id).first()
                    db.session.delete(player_to_delete)
                    team_id = Teams.query.filter_by(shortTeamName=team).first().id # add the player to his new team, with the stats from the full season
                    player_to_new_team = Player(name=player.name,link=player.link,games=player.games,points=player.points,assists=player.assists,rebounds=player.rebounds,team_id=team_id)
                    db.session.add(player_to_new_team)
        db.session.commit()
        team_id = Teams.query.filter_by(shortTeamName=team).first().id
        for db_player in Player.query.filter_by(team_id=team_id): # check if there any players that are not on the team anymore
            if all(db_player.name != player_data["Player"] for player_data in players_data): # if player from certain team in database does not match
                db.session.delete(db_player)                                   # any other players in team file, player gets removed
        db.session.commit()



class Games(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team1_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    team2_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    score1 = db.Column(db.Integer, nullable=False)
    score2 = db.Column(db.Integer, nullable=False)
    team1 = db.relationship('Teams',foreign_keys=[team1_id])
    team2 = db.relationship('Teams',foreign_keys=[team2_id])

# Function to add games to database table
def load_games_data_from_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    data = data["Date"]
    for date, games in data.items():
        for game in games:
            team1 = game['Home']
            team2 = game['Visitor']
            team1_query = Teams.query.filter_by(shortTeamName=team1).first()
            id_team1 = team1_query.id
            team2_query = Teams.query.filter_by(shortTeamName=team2).first()
            # print(team2_query, team2)
            id_team2 = team2_query.id
            game = Games(team1_id=id_team1, team2_id=id_team2, date=date, score1=0, score2=0)
            db.session.add(game)
    db.session.commit()

# Create Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    points = db.Column(db.Integer)
    perfectGames = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
# Create 

@app.route('/')
def index():
    if "user" in session:
        userLogged = True
    else: 
        userLogged = False
    # for pick in Picks.query.filter_by(user_id=18):
    #     db.session.delete(pick)
    # db.session.commit()
    for game in Games.query.filter_by(date="Aug30"):
        db.session.delete(game)
    db.session.commit()
    # for player in Player.query.filter_by(games=1):
    #     player.games = 0
    #     player.points = 0
    #     player.assists = 0
    #     player.rebounds = 0
    # db.session.commit()
    # for user in Users.query.filter_by(id=18):
    #     user.points = 0
    # db.session.commit()
    # load_players_to_db()
    return render_template('index.html',userLogged=userLogged)

@app.route('/picks')
def picks():
    if "user" in session:
        userLogged = True
        date = datetime.utcnow()
        string_date = months[date.month-1]+str(date.day)
        games = {"Games":[]}
        playersList = {}
        i = 0
        for game in Games.query.filter_by(date=string_date) :
            home = Teams.query.filter_by(id=game.team1_id).first()
            away = Teams.query.filter_by(id=game.team2_id).first()
            games['Games'].append({"team1": home.shortTeamName, "team2":away.shortTeamName})
            players_team1 = Player.query.filter_by(team_id=game.team1_id)
            players_team2 = Player.query.filter_by(team_id=game.team2_id)
            players_array = []
            for player in players_team1:
                players_array.append(player.name)
            for player in players_team2:
                players_array.append(player.name)
            players_array = sorted(players_array)
            playersList.update({"game{}".format(i): players_array})
            i += 1
        flash("Remember to check what players are not playing, so you don't pick someone who doesn't play!")
        return render_template('picks.html',userLogged=userLogged,playersList=playersList,games=games)
    else:
        userLogged = False
        flash("You need to be logged in to make your picks!")
        return redirect(url_for('login'))

# Submit picks page
@app.route("/submit", methods=['GET','POST'])
def submit():
    data = {}
    user= session["user"]
    if "user" in session:
        userLogged = True
    else:
        userLogged = False
    if request.method == "POST":
        data = request.get_json()
        if user:
            for key in data:
                user = session["user"]
                date = datetime.utcnow()
                string_date = months[date.month-1]+str(date.day)
                pick = Picks(winner=data[key]["Winner"][0],
                            best_scorer=data[key]["PTS"][0],
                            best_passer=data[key]["AST"][0],
                            best_rebounder=data[key]["REB"][0],
                            game = key,
                            date=string_date,
                            user_id = user,
                            correctPicks=2)
                db.session.add(pick)      
            db.session.commit()
            return "Picks were updated succesfully", 200
        else: 
            return "User not logged in.", 401
    
    return render_template('submit.html',userLogged=userLogged, data=data)

    # Now user_selections contains the user's selections for each game.
    # You can process and store the data as needed.

    # return "Picks submitted successfully!"

@app.route('/rankings')
def rankings():
    if "user" in session:
        userLogged = True
    else:
        userLogged = False
    # delete certain row from picks
    current_rankings = {}
    for user in Users.query.all():
        current_rankings.update({user.username :int(user.points)})
    sorted_rankings = dict(sorted(current_rankings.items(), key=lambda item: item[1], reverse=True))
    return render_template('rankings.html',userLogged=userLogged,current_rankings=sorted_rankings)

@app.route('/results')
def results():
    if "user" in session:
        userLogged = True
    else:
        userLogged = False
    gameResults = {}
    for game in Games.query.all():
        if game.score1 != 0 and game.score2 != 0:
            home_team = Teams.query.filter_by(id=game.team1_id).first()
            away_team = Teams.query.filter_by(id=game.team2_id).first()
            gameResults.update({game.id:{"Date":game.date,"Home":home_team,"Away":away_team,"HomeScore":game.score1,"AwayScore":game.score2}})
        sorted_results = dict(sorted(gameResults.items(), key=lambda item: getDateValue(item[1]['Date']), reverse=True))
    return render_template('results.html',userLogged=userLogged, sorted_results=sorted_results)

@app.route('/schedule')
def schedule():
    if "user" in session:
        userLogged = True
    else:   
        userLogged = False
    games = {}
    date = datetime.utcnow()
    month = date.month
    monthName = months[month-1]
    for game in Games.query.filter(Games.date.like(monthName + "%")).all():
        if game.score1 == 0 and game.score2 == 0 :
            home_team = Teams.query.filter_by(id=game.team1_id).first()
            away_team = Teams.query.filter_by(id=game.team2_id).first()
            games.update({game.id:{"Date":game.date,"Home":home_team.teamName,"HomeShort":home_team.shortTeamName,"Away":away_team.teamName,"AwayShort":away_team.shortTeamName}})
    sorted_games = dict(sorted(games.items(), key=lambda item: getDateValue(item[1]['Date']), reverse=False))
    return render_template('schedule.html',userLogged=userLogged, sorted_games=sorted_games)

@app.route('/standings')
def standings():
    if "user" in session:
        userLogged = True
    else:
        userLogged = False
    teamStandings = {}
    eastStandings = {}
    westStandings = {}
    winPct = 0
    for team in Teams.query.all():
        team.games = team.wins + team.losses
        if team.games == 0:
            winPct = 0
        else: 
            winPct = (float)(team.wins)/(float)(team.games)*100
        if team.id <=15:
                eastStandings.update({team.id:{"Name":team.teamName,"ShortName":team.shortTeamName,"Wins":team.wins,"Losses":team.losses,"WinPCT":winPct}})
        else : 
            westStandings.update({team.id:{"Name":team.teamName,"ShortName":team.shortTeamName,"Wins":team.wins,"Losses":team.losses,"WinPCT":winPct}})
        teamStandings.update({team.id:{"Name":team.teamName,"ShortName":team.shortTeamName,"Wins":team.wins,"Losses":team.losses,"WinPCT":winPct}})
    sortedTeamStandings = dict(sorted(teamStandings.items(), key=lambda item: item[1]["WinPCT"], reverse=True))
    eastStandingsSorted = dict(sorted(eastStandings.items(), key=lambda item: item[1]["WinPCT"], reverse=True))
    westStandingsSorted = dict(sorted(westStandings.items(), key=lambda item: item[1]["WinPCT"], reverse=True))
    return render_template('standings.html',userLogged=userLogged,teamStandings=sortedTeamStandings,west=westStandingsSorted,east=eastStandingsSorted)

@app.route('/stats/<team>')
def stats(team):
    if "user" in session:
        userLogged = True
    else:
        userLogged = False
    teamDict = {}
    teamInfo = Teams.query.filter_by(shortTeamName=team).first()
    playersDict = {}
    teamInfo.games = teamInfo.wins + teamInfo.losses
    if teamInfo.games == 0:
        winPct = 0
    else: 
        winPct = round((float)(team.wins)/(float)(team.games)*100,1)
    for player in Player.query.filter_by(team_id=teamInfo.id):
        if player.games == 0:
            ptsPerGame = 0
            rebPerGame = 0
            astPerGame = 0
        else :
            ptsPerGame = round(float(player.points)/float(player.games),1)
            rebPerGame = round(float(player.rebounds)/float(player.games),1)
            astPerGame = round(float(player.assists)/float(player.games),1)
        playersDict.update({player.id:{"Name":player.name,"Link":player.link,"PPG":ptsPerGame,"APG":astPerGame,"RPG":rebPerGame,"Games":player.games}})
    sorted_players = dict(sorted(playersDict.items(), key=lambda item: item[1]["PPG"], reverse=True))
    topPPG = dict(sorted(playersDict.items(), key=lambda item: item[1]['PPG'], reverse=True)[:3])
    topAPG = dict(sorted(playersDict.items(), key=lambda item: item[1]['APG'], reverse=True)[:3])
    topRPG = dict(sorted(playersDict.items(), key=lambda item: item[1]['RPG'], reverse=True)[:3])
    teamDict = {"Name":teamInfo.teamName,"ShortName":team,"Wins":teamInfo.wins,"Losses":teamInfo.losses,"WinPCT":winPct,"Players":sorted_players}
    return render_template('stats.html',userLogged=userLogged,teamDict=teamDict,ppg=topPPG,apg=topAPG,rpg=topRPG)

# Create Login Page
@app.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm()
    userLogged = False
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password_hash.data):
                login_user(user)
                session["user"] = user.id
                flash("Login Succesfull!!")
                userLogged = True
                return render_template('index.html',userLogged=True)   
            else:
                flash("Incorrect Password! Try Again!")
        else:
            flash("User Does Not Exist! Try Again!")
    data = "You will be able to see your picks here! Make your picks!"
    return render_template('login.html',form=form,userLogged=userLogged,data=data)

# Create Profile Page
@app.route('/profile', methods = ['GET','POST'])
@login_required
def profile():
    if "user" in session:
        userLogged = True
    else:
        userLogged = False
    user = session["user"]
    picksList = Picks.query.filter_by(user_id=user)
    if picksList.first() is not None:
        data = {}
        for pick in Picks.query.filter_by(user_id=user):
            if pick.correctPicks == 2:
                data.update({pick: {"Winner": pick.winner,"PTS":pick.best_scorer,"AST":pick.best_passer,"REB":pick.best_rebounder,"Date":pick.date,"Game":pick.game,"CorrectPicks":2}})
            else :
                pickWin = int(pick.correctPicks / 1000)
                pickPTS = int((pick.correctPicks % 1000) / 100)
                pickAST = int((pick.correctPicks % 100) / 10)
                pickREB = int(pick.correctPicks % 10)
                data.update({pick: {"Winner": pick.winner,"PTS":pick.best_scorer,"AST":pick.best_passer,"REB":pick.best_rebounder,"Date":pick.date,"Game":pick.game,"CorrectPicks":1,"PickREB":pickREB,"PickAST":pickAST,"PickPTS":pickPTS,"PickWin":pickWin}})
        return render_template('profile.html',userLogged=userLogged,data=data,picks_available=True)
    else:
        data = "You will be able to see your picks here! Make your picks!"   
        return render_template('profile.html',userLogged=userLogged,data=data,picks_available=False)

# Create Logout Page
@app.route('/logout', methods = ['GET','POST'])
@login_required
def logout():
    logout_user()
    session.pop('user', None)
    session["user"] = None
    flash('You Have Been Logged Out!')
    return render_template('index.html', userLogged=False)

@app.route('/sign-up',methods = ['GET', 'POST'])
def sign_up():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = Users(username=form.username.data, email=form.email.data, password_hash=hashed_pw,perfectGames=0)
            db.session.add(user)
            db.session.commit()
        name = form.username.data
        form.username.data = ''
        form.email.data = ''
        form.password_hash.data = ''
    our_users = Users.query.order_by(Users.date_added)
    userLogged = False
    return render_template('sign-up.html', form=form,name=name,our_users=our_users,userLogged=userLogged)



@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html")

if __name__ == '__main__':    
    app.run(debug=True)