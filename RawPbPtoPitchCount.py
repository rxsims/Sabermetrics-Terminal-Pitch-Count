import numpy as np
import pandas as pd
import time
import os


# Takes raw play-by-play file and extracts only the in-games actions, labelled by 'play' in the raw file
def BatterPbP(filename,path):
    raw_file = open(path + filename,'r').read().split('\n')
    
    games_list = [] # List of games    
    games_keys = [] # Game IDs and Event number in each game. Used to create MultiIndex
    games_events = [] # In-game events, denoted by 'play' in raw file
    
    game_start_index = [i for i,x in enumerate(raw_file) if x[:2]=='id'] # Check for start of a game id
    game_start_index.append(len(raw_file)) # Add the final line to the list of indices, we will not loop to include this point
    
    for i in range(len(game_start_index)-1): # Loop over indices (positions of game start), excluding the last one
        games_list.append(raw_file[game_start_index[i]:game_start_index[i+1]])
        
    for game in games_list:
        # game[0] is the first line for each game.  The format is of the form 'id,XXXYYYYMMDDG'.
        # We can identify each game by removing the first 3 chars in the string and only keeping 'XXXYYYYMMDDG'.
        # These identifying string will be used as dictionary keys to pull the batting information.
        # We include the visiting team ID at the end of the game ID code.
        # All batting information begins with the chars 'play,' which we can exclude.
        # Each line will be a sublist, which we need to seperate for each comma in the line.
        game_id = game[0][3:] + game[2][-3:]
        
        j = 0
        for line in game:
            if line[:4] == 'play':
                games_keys.append((game_id,j))
                games_events.append(line[5:].split(','))
                j += 1
        #= dict(enumerate([line[5:].split(',') for line in game if line[:4]=='play']))
        
    games_df = pd.DataFrame(games_events,index = pd.MultiIndex.from_tuples(games_keys))
    
    return games_df


# Adds two additional columns which dictates the batter on-deck (Next Batter), and the Inning that batter comes to the plate
# If two game actions have the same batter in the same inning, the action involves runners on base
# Since we only care about what the batter is doing, we can ignore the first of these two events then
def team_next_batter(team_games_all):
    team_games_wnb = team_games_all.copy()
    team_games_wnb['Next_Batter'] = team_games_all.groupby(level=0)['2'].shift(-1)
    team_games_wnb['Next_Inning'] = team_games_all.groupby(level=0)['0'].shift(-1)
    
    # Removes same batter appearing twice in a row, unless it occurs in seperate innings
    team_games_unique_batter = team_games_wnb[(team_games_wnb['2'] != team_games_wnb['Next_Batter']) 
                                              |(team_games_wnb['0'] != team_games_wnb['Next_Inning'])]
    
    return team_games_unique_batter


# Counts the number of times each pitch count results in a game action for each team
def all_team_count(team_dict, homeaway):
    team_pitch_count_dict = {}
    
    for team in team_dict.keys():
        team_all_batter = team_dict[team]
        team_all_batter.columns = ['0','1','2','3','4','5']
        team_batters = team_all_batter.loc[team_all_batter['1']==homeaway]

        team_batter_nodup = team_next_batter(team_batters).groupby('3').size()

        team_pitch_count_dict[team[:3]] = team_batter_nodup[counts].tolist()

    return team_pitch_count_dict




if __name__ == "__main__":
    path_raw = '' # Path to directory containing the raw play-by-play data files
    path_save = '' # Path to directory where the pitch count data will be saved
    
    team_raw_list = os.listdir(path_raw)

    home_dict = {}
    away_dict = {}

    s = np.array(['0','1','2'])
    b = np.array(['0','1','2','3'])
    counts = [i+j for j in s for i in b] # Create all pitch counts from combination of balls + strikes


    # Create a dictionary of DataFrames to house the pitch data for each team, separating home and away stats
    for file in team_raw_list:    
        home_dict[file[4:7]] = pd.DataFrame()
        away_dict[file[4:7]] = pd.DataFrame()


    for file in team_raw_list:
        # For each team's set of home games, extract the game actions
        all_games = BatterPbP(file, path_raw)

        # Loop through the different home games
        for game in all_games.index.levels[0]:
            home_str = game[:3]
            away_str = game[-3:]

            # Assign game events to either the home team or the away team
            home_dict[home_str] = pd.concat([home_dict[home_str],
                                             all_games.groupby(level=0).get_group(game)])
            away_dict[away_str] = pd.concat([away_dict[away_str],
                                             all_games.groupby(level=0).get_group(game)])


    # Count the team's season total of pitch counts in home and away games
    home_pitch_count_dict = all_team_count(home_dict,'1')
    away_pitch_count_dict = all_team_count(away_dict,'0')

    home_team_df = pd.DataFrame.from_dict(home_pitch_count_dict, orient='index', columns=counts)
    away_team_df = pd.DataFrame.from_dict(away_pitch_count_dict, orient='index', columns=counts)

    
    # Save pitch count DataFrames for future use
    home_team_df.to_csv(path_save+'Home')
    away_team_df.to_csv(path_save+'Away')