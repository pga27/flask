import pandas as pd
import requests
import json
import csv
from bs4 import BeautifulSoup
from datetime import datetime
teams = ["Philadelphia 76ers","Boston Celtics", "Toronto Raptors", "New York Knicks", "Brooklyn Nets","Indiana Pacers", "Detroit Pistons", "Chicago Bulls", "Milwaukee Bucks", "Cleveland Cavaliers","Atlanta Hawks", "Miami Heat", "Orlando Magic", "Charlotte Hornets", "Washington Wizards","Los Angeles Lakers", "Los Angeles Clippers", "Sacramento Kings", "Golden State Warriors", "Phoenix Suns","Minnesota Timberwolves", "Portland Trail Blazers","Denver Nuggets","Oklahoma City Thunder","Utah Jazz","New Orleans Pelicans", "Memphis Grizzlies", "Dallas Mavericks", "San Antonio Spurs", "Houston Rockets"]
teamsshort = ["PHI","BOS","TOR","NYK","BRK","IND","DET","CHI","MIL","CLE","ATL","MIA","ORL","CHO","WAS","LAL","LAC","SAC","GSW","PHO","MIN","POR","DEN","OKC","UTA","NOP","MEM","DAL","SAS","HOU"]
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
# nba_stats = dict(pd.read_json("nba_teams_stats.json"))
def getDailyBoxscore(day,month,year):
    player_stats_url = "https://www.basketball-reference.com/friv/dailyleaders.fcgi?month={}&day={}&year={}"
    url = player_stats_url.format(month,day,year)
    data = requests.get(url)
    dfs = []
    page = data.text
    soup = BeautifulSoup(page, "html.parser")
    soup.find('tr', class_ = "thead").decompose()
    player_table = soup.find(id="all_stats")
    player = pd.read_html(str(player_table))[0]
    player["Date"] = ("{}-{}-2022").format(month, day)
    dfs.append(player)
    data = pd.concat(dfs) 
    if data.empty:
        return 0
    data.rename(columns={'Unnamed: 0':'Id','Unnamed: 3':'H/A','Unnamed: 5':'W/L'},inplace=True)
    stats = data.iloc[:,[1,2,3,4,5,18,19,24,26]]
    games = []
    game_stats = dict()
    for index in stats.index:
        if stats["Player"][index] == "Player":
            continue
        winner = None
        home_team = None
        away_team = None
        if stats["H/A"][index] == "@":
            game = "{} vs {}".format(stats["Opp"][index] ,stats["Tm"][index])
            if game not in games:
                if game != "Tm vs Opp":
                    games += [game]
            home_team = stats["Opp"][index]
            away_team = stats["Tm"][index]
        else :
            game = "{} vs {}".format(stats["Tm"][index] ,stats["Opp"][index])
            if game not in games:
                if game != "Tm vs Opp":
                    games += [game]
            home_team = stats["Tm"][index]
            away_team = stats["Opp"][index]
        if game not in game_stats.keys():
            if stats["W/L"][index] == "W":
                winner = stats["Tm"][index]
            else:
                winner = stats["Opp"][index]
            game_stats[game] = {
                "Winner": winner,
                home_team: {},
                away_team: {}
            }
            if stats["Tm"][index] == home_team:
                game_stats[game][home_team].update({stats["Player"][index]: {
                    "PTS": int(stats['PTS'][index]),
                    "AST": int(stats['AST'][index]),
                    "REB": int(stats['TRB'][index]),
                    "GmSc": float(stats['GmSc'][index])
                }})
            else:
                game_stats[game][away_team].update({stats["Player"][index]: {
                    "PTS": int(stats['PTS'][index]),
                    "AST": int(stats['AST'][index]),
                    "REB": int(stats['TRB'][index]),
                    "GmSc": float(stats['GmSc'][index])
                }})
        else:
            if stats["Tm"][index] == home_team:
                game_stats[game][home_team].update({stats["Player"][index]: {
                    "PTS": int(stats['PTS'][index]),
                    "AST": int(stats['AST'][index]),
                    "REB": int(stats['TRB'][index]),
                    "GmSc": float(stats['GmSc'][index])
                }})
            else:
                game_stats[game][away_team].update({stats["Player"][index]: {
                    "PTS": int(stats['PTS'][index]),
                    "AST": int(stats['AST'][index]),
                    "REB": int(stats['TRB'][index]),
                    "GmSc": float(stats['GmSc'][index])
                }})
    with open('static/files/games_played/boxscore_{}-{}.json'.format(month,day), 'w') as json_file:
        json.dump(game_stats, json_file, indent=4)
def updateSPGAndWinPCTAndLeaders():
    # #print(nba_stats)
    nba_stats = dict(pd.read_json("nba_teams_stats.json"))
    for key in nba_stats.keys():
        #print(key)
        #print("Record: ", nba_stats[key].get("Wins"), "-", nba_stats[key].get("Losses"))
        win_pct = round(nba_stats[key].get("Wins")/nba_stats[key].get("Games"),3)
        nba_stats[key]["Percentage"] =  win_pct
    nba_stats = pd.DataFrame(nba_stats)
    nba_stats.to_json("nba_teams_stats.json")
    nba_stats = dict(pd.read_json("nba_teams_stats.json"))


    for key in nba_stats.keys():
        for player in nba_stats[key].get("Players").keys():
            nba_stats[key].get("Players")[player]["PPG"] = round(int(nba_stats[key].get("Players")[player]["PTS"]) / int(nba_stats[key].get("Players")[player]["Games"]),1)
            nba_stats[key].get("Players")[player]["APG"] = round(int(nba_stats[key].get("Players")[player]["AST"]) / int(nba_stats[key].get("Players")[player]["Games"]),1)
            nba_stats[key].get("Players")[player]["RPG"] = round(int(nba_stats[key].get("Players")[player]["TRB"]) / int(nba_stats[key].get("Players")[player]["Games"]),1)
    nba_stats = pd.DataFrame(nba_stats)
    nba_stats.to_json("nba_teams_stats.json")
    nba_stats = dict(pd.read_json("nba_teams_stats.json"))

    for key in nba_stats.keys():
        nba_stats[key]["PPGLeader"] = getLeaders(key, nba_stats[key].get("Players"), "PPG")
        nba_stats[key]["APGLeader"] = getLeaders(key, nba_stats[key].get("Players"), "APG")
        nba_stats[key]["RPGLeader"] = getLeaders(key, nba_stats[key].get("Players"), "RPG")
        print(nba_stats[key]["PPGLeader"])
        print(nba_stats[key]["APGLeader"])
        print(nba_stats[key]["RPGLeader"])
    nba_stats = pd.DataFrame(nba_stats)
    nba_stats.to_json("nba_teams_stats.json")


def getLeaders(key, dict, category):
    leaders = []
    teams = pd.read_json("players.json")
    for player in dict.keys():
        if player not in teams[key].get("Players"):
            continue
        if leaders == []:
            leaders = [player]
        elif len(leaders) ==1:
            if int(dict[player].get(category)) > int(dict[leaders[0]].get(category)):
                leaders = [player, leaders[0]]
            else:
                leaders += [player]
        elif len(leaders) == 2:
            if int(dict[player].get(category)) > int(dict[leaders[0]].get(category)):
                leaders = [player, leaders[0], leaders[1]]
            elif int(dict[player].get(category)) > int(dict[leaders[1]].get(category)) and int(dict[player].get(category)) < int(dict[leaders[0]].get(category)):
                leaders = [leaders[0], player, leaders[1]]
            else:
                leaders += [player]
        else:
            if int(dict[player].get(category)) > int(dict[leaders[0]].get(category)):
                leaders = [player, leaders[0], leaders[1]]
            elif int(dict[player].get(category)) > int(dict[leaders[1]].get(category)) and int(dict[player].get(category)) < int(dict[leaders[0]].get(category)):
                leaders = [leaders[0], player, leaders[1]]
            elif int(dict[player].get(category)) > int(dict[leaders[2]].get(category)) and int(dict[player].get(category)) < int(dict[leaders[1]].get(category)):
                leaders = [leaders[0], leaders[1], player]
    return leaders
def printTeamLeaders(dict):
    ptsLeaders = dict.get("PPGLeader")
    astLeaders = dict.get("APGLeader")
    rebLeaders = dict.get("RPGLeader")
    print("------------------------")
    print("POINTS LEADERS:")

    print(ptsLeaders[0], dict.get("Players")[ptsLeaders[0]].get("PPG"))
    print(ptsLeaders[1], dict.get("Players")[ptsLeaders[1]].get("PPG"))
    print(ptsLeaders[2], dict.get("Players")[ptsLeaders[2]].get("PPG"))
    print("------------------------")
    print("ASSISTS LEADERS: ")

    print(astLeaders[0], dict.get("Players")[astLeaders[0]].get("APG"))
    print(astLeaders[1], dict.get("Players")[astLeaders[1]].get("APG"))
    print(astLeaders[2], dict.get("Players")[astLeaders[2]].get("APG"))
    print("------------------------")
    print("REBOUNDS LEADERS: ")

    print(rebLeaders[0], dict.get("Players")[rebLeaders[0]].get("RPG"))
    print(rebLeaders[1], dict.get("Players")[rebLeaders[1]].get("RPG"))
    print(rebLeaders[2], dict.get("Players")[rebLeaders[2]].get("RPG"))
    print("------------------------")
def getTeamRecord(dict):    # dictionary of specific team, returns Record %% - %%(W-L)
    wins = dict.get("Wins")
    losses = dict.get("Losses")
    record = "Record: {}-{}".format(wins,losses)
    return record
def getGameInfo(dict, game):
    teams = game.split(" vs ")
    for team in teams:
        print("\t",team)
        print(getTeamRecord(dict[team]))
        printTeamLeaders(dict[team])   
def getStatsOTD(day,month):
    with open('static/files/games_played/boxscore_{}-{}.json'.format(month,day)) as file:
        stats = json.load(file)
    return stats
    
def getDailyLeaders(day, month):
    with open('static/files/games_played/boxscore_{}-{}.json'.format(month,day)) as file:
        stats = json.load(file)
    dayLeaders = dict()
    for game in stats.keys():
        ptsLeader = []
        astLeader = []
        rebLeader = []
        winner = stats[game]["Winner"]
        hometeam, awayteam = game.split(" vs ")
        playersList = {}
        for player in stats[game][hometeam].keys():
            playersList.update({player: stats[game][hometeam][player]})
        for player in stats[game][awayteam].keys():
            playersList.update({player: stats[game][awayteam][player]})
        max_points = max(playersList, key=lambda k: playersList[k]['PTS'])
        ptsLeader = [k for k in playersList if playersList[k]['PTS'] == playersList[max_points]['PTS']]
        max_assists = max(playersList, key=lambda k: playersList[k]['AST'])
        astLeader = [k for k in playersList if playersList[k]['AST'] == playersList[max_assists]['AST']]
        max_rebounds = max(playersList, key=lambda k: playersList[k]['REB'])
        rebLeader = [k for k in playersList if playersList[k]['REB'] == playersList[max_rebounds]['REB']]
        dayLeaders.update({game:{ "Winner": winner, "PTS": list(set(ptsLeader)), "AST": list(set(astLeader)), "REB": list(set(rebLeader))}})
    return dayLeaders
def printDayLeaders(day, month):
    dayLeaders = getDailyLeaders(day, month)
    for game in dayLeaders.keys():
        print(game)
        print("Winner: ",dayLeaders.get(game).get("Winner")[0])
        ptsLeader = dayLeaders.get(game).get("PTS")
        astLeader = dayLeaders.get(game).get("AST")
        rebLeader = dayLeaders.get(game).get("REB")
        stats = pd.read_csv("static/files/games_played/boxscore_{}-{}.csv".format(month, day))
        for index in stats.index:
            if stats["Player"][index]==ptsLeader[0]:
                pts = stats["PTS"][index] 
            if stats["Player"][index]==astLeader[0]:
                ast = stats["AST"][index] 
            if stats["Player"][index]==rebLeader[0]:
                reb = stats["TRB"][index]   
        print("Points Leader: ",pts, " - ", ', '.join(ptsLeader))
        print("Assists Leader: ",ast, " - ", ', '.join(astLeader))
        print("Rebounds Leader: ",reb, " - ",', '.join(rebLeader))

def printStandings(dict,conf):
    teams = conf
    standings = []
    while teams != []:
        team_index = 0
        best_pct = 0
        best_team = ""
        for team in teams:
            if dict.get(team).get("Percentage") > best_pct:
                best_team = team
                best_pct = dict[team]["Percentage"]
                team_index = teams.index(best_team)
        standings += [str(teams.pop(team_index))]
    for team in standings:
        print("{} - {}-{}({})".format(team,int(dict.get(team).get("Wins")),int(dict.get(team).get("Losses")), round(dict.get(team).get("Percentage"),3)))
def getGames(month):
    games_url = "https://www.basketball-reference.com/leagues/NBA_2024_games-{}.html"
    data = requests.get(games_url.format(month))
    dfs = []
    page = data.text
    soup = BeautifulSoup(page, "html.parser")
    games = soup.find(id="schedule")
    monthgames = pd.read_html(str(games))[0]
    dfs.append(monthgames)
    data = pd.concat(dfs)
    data.drop('Start (ET)', inplace=True, axis=1)
    data.drop('PTS', inplace=True, axis=1)
    data.drop('PTS.1', inplace=True, axis=1)
    data.drop('Unnamed: 6', inplace=True, axis=1)
    data.drop('Unnamed: 7', inplace=True, axis=1)
    data.drop('Attend.', inplace=True, axis=1)
    data.drop('Arena', inplace=True, axis=1)
    data.drop('Notes', inplace=True, axis=1)
    for index in data.index:
        date = data["Date"][index]
        weekday, monthday, year = date.split(", ")
        cleardate = getShortDate(monthday)
        awayteam = getTeamShort(data["Visitor/Neutral"][index])
        hometeam = getTeamShort(data["Home/Neutral"][index])
        data["Date"][index] = cleardate
        data["Visitor/Neutral"][index] = awayteam
        data["Home/Neutral"][index] = hometeam
    data.to_json("games/games{}.json".format(month))
def getShortDate(monthday):
    month, day = monthday.split(" ")
    return month+(str(day))
def getDateValue(date):
    date_obj = datetime.strptime(date,"%b%d")
    if date_obj.month >= 10:
        value = int(date_obj.month)*31 + int(date_obj.day)
    if date_obj.month < 10:
        value = 400 + int(date_obj.month)*31 + int(date_obj.day)
    return value
def getDateMonth(date):
    month = date[0:3]
    monthNum = months.index(month) + 1
    # date_obj = datetime(2024,1,1)
    # date_obj = datetime.strptime(date,"%b%d")
    
    return (monthNum)
    
def gamesToClean(month):
    with open('games/games{}.json'.format(month)) as file:
        stats = json.load(file)
    
    transformed_data = {}
    sorted_dates = list(set(stats["Date"].values()))
    # Group the data by "Date" and iterate through each group
    for date in sorted_dates:
        #print(date, group, "\n")
        games = []
        # Iterate through the games in the current date
        for i in range(len(stats["Date"])):
            if(stats["Date"][str(i)] == date) :
                visitor_team = stats["Visitor/Neutral"][str(i)]
                home_team = stats["Home/Neutral"][str(i)]
                game = {"Visitor": visitor_team, "Home": home_team}
                games.append(game)
        
        # Add the list of games to the transformed data with the date as the key
        transformed_data[date] = games

    # Create a final dictionary with a single key "Date" that contains the transformed data
    final_data = {"Date": transformed_data}
    with open('games/games{}.json'.format(month), 'w') as outfile:
        json.dump(final_data, outfile, indent=4)
def jsonPlayerFileChanges(team):
    with open('teams/{}.json'.format(team),'r') as file:
        data = json.load(file)
    values = list(data["Player"].values())
    new_data = {"Players" : values}
    with open('teams/{}.json'.format(team), 'w') as outfile:
        json.dump(new_data, outfile, indent=4)
def getDate(monthday, year):
    month, day = monthday.split(" ")
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthn = months.index(month) + 1
    return str(day)+"-"+str(monthn)+"-"+str(year)
def getTeamShort(team):
    index = teams.index(team)
    return teamsshort[index]
# def getPlayers():
#     playersList = dict()
#     for team in nba_stats:
#         teamPlayers = []
#         players = nba_stats[team].get("Players").keys()
#         for player in players:
#             teamPlayers += [player]
#         if team not in playersList.keys():
#             playersList[team] = teamPlayers
#     playersList = pd.DataFrame(playersList)
#     playersList.to_json("players.json")

## Get players from team according to teams name
def getPlayersfromTeamPage(teamabv):
    teams_url = "https://www.basketball-reference.com/teams/{}/2024.html"
    data = requests.get(teams_url.format(teamabv))
    dfs = []
    page = data.text
    soup = BeautifulSoup(page, "html.parser")
    roster = soup.find(id="roster")
    # players = pd.read_html(str(roster))[0]
    players_data = roster.find_all("td", {"data-stat": "player"})
    # dfs.append(players)
    # data = pd.concat(dfs)
    # data.drop(['Pos','No.','Ht','Wt','Birth Date','Exp','College','Unnamed: 6'], inplace=True, axis=1)
    playerList = []
    sub_string = '\u00a0\u00a0(TW)'
    for player in players_data:
        player_name = player.get_text()
        if sub_string in player_name:
            player_name = player_name.replace(sub_string,'')
        player_href = player.find("a")["href"]
        player_link = "https://www.basketball-reference.com" + player_href
        player_info = {"Player": player_name, "Link": player_link}
        playerList.append(player_info)
    # for index in range(0,len(data)):    
    #     playerList.append(data["Player"][index])
    new_data = {"Players" : playerList}
    with open('static/files/teams/{}.json'.format(teamabv), 'w') as outfile:
        json.dump(new_data, outfile, indent=4)
    return new_data

def csvToJSON(team):
    csvFilePath = "teams/{}.csv"
    jsonFilePath = "teams/{}.json"

    data = {}
    with open(csvFilePath.format(team), encoding='utf-8') as csvFile:
        csvReader = csv.DictReader(csvFile)
        for rows in csvReader:
            id = rows['Id']
            data[id] = rows
    with open(jsonFilePath.format(team), 'w') as jsonFile:
        jsonFile.write(json.dumps(data, indent=4))

def tradePlayer(player1,team1,team2):
    f = open('players.json')
    playerList = json.load(f)
    if player1 in playerList[team1]:
        playerList[team1].remove(player1)
    if player1 not in playerList[team2]:
        playerList[team2].add(player1)
