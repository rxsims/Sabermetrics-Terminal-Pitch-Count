import numpy as np
import pandas as pd
import os


class Team:
    def __init__(self, team, year, event_data, homeaway):
        self.team = team
        self.year = year
        self.homeaway = homeaway # 0 for away, 1 for home
        self.counts_str = [i+j for j in ['0','1','2'] for i in ['0','1','2','3']] # Pitch count strings
        
        self.event_data = self.clean_pitches(event_data)
        self.outcomes = self.at_bat_outcomes()
        
        self.counts = self.outcomes['Count'].value_counts().sort_index()
        self.count_outcomes = self.set_count_outcomes().groupby('Count')['Outcome'].value_counts().unstack().fillna(0)
        self.plate_disc = pd.DataFrame()
        
    
    # Remove data from the string of pitches that do not involve the batter
    def clean_pitches(self, event_data):
        if '1' in event_data.columns:
            # When adding games to an away team, make sure to only add the data from games that specific away team played
            if self.homeaway==0:
                event_data = event_data[event_data.index.get_level_values(0).str[-3:]==self.team]
            
            # Select the home or away data for the team, and rename the columns appropriately
            event_homeaway = event_data[event_data['1']==self.homeaway].drop(columns=['1'])
            event_homeaway.columns = ['Inning','Batter','Count','Pitches','Event']
            
            # Remove events where the same batter is at the place twice in a row in the same inning
            # This should only happen when events occur not involving the batter, such as stolen bases
            event_nodup = self.team_next_batter(event_homeaway)
            
            # Remove certain edge cases which cause the at-bat to end w/o influence of the batter
            # 'NP' = No Pitch, the batter was substituted
            # 'PO' = Pick off, a runner on base was tagged out and ended the inning
            # 'C' = Runner was caught stealing. Whether or not it ended the at-bat, it it is recorded in the game events
            event_data = event_nodup[(event_nodup['Event']!='NP')&(~event_nodup['Event'].str.contains('PO'))&(event_nodup['Event'].str[0]!='C')]
        event_copy = event_data.copy()
        event_copy['Pitches'] = event_data['Pitches'].str.translate(str.maketrans('','', '123+.*>'))
        return event_copy
    
    
    # Remove events where the same batter is at the place twice in a row in the same inning
    # This should only happen when events occur not involving the batter, such as stolen bases
    def team_next_batter(self, team_games_all):
        team_games_wnb = team_games_all.copy()
        team_games_wnb['Next_Batter'] = team_games_all.groupby(level=0)['Batter'].shift(-1)
        team_games_wnb['Next_Inning'] = team_games_all.groupby(level=0)['Inning'].shift(-1)

        team_games_unique_batter = team_games_wnb[(team_games_wnb['Batter'] != team_games_wnb['Next_Batter']) # Removes same batter appearing twice in a row 
                                                  |(team_games_wnb['Inning'] != team_games_wnb['Next_Inning'])] # Unless it occurs in seperate innings

        return team_games_unique_batter
    
    
    # Create Dataframe that categorizes each at-bat outcome, and the type of contact made
    # One event that is not covered is a Balk ('B' in 'Outcome' column) that ends the game
    def at_bat_outcomes(self):
        ab_outcome = self.event_data['Event'].str.split('/',expand=True)
        ab_outcome['Count'] = self.event_data['Count']
        
        # The first split of 'Event' tells what the outcome of the at-bat is.
        # The first character is unique except for home-runs (HR) and hit-by-pitch (HP)
        # Assign the outcome as this first character, but when that character is 'H' take the 2nd character instead.
        ab_outcome['Outcome'] = ab_outcome[0].str[0]
        ab_outcome.loc[ab_outcome[ab_outcome[0].str[0]=='H'].index,'Outcome'] = ab_outcome[0].str[1]
        
        # Translate each specific outcome into (O)uts, Stri(K)eouts, (W)alks, (S)ingle, (D)ouble, (T)riple, Home (R)uns
        all_event_types = 'DEFRPIKSTW123456789'
        all_event_repl =  'DOORWWKSTWOOOOOOOOO'
        ab_outcome['Outcome'] = ab_outcome['Outcome'].str.translate(str.maketrans(all_event_types,all_event_repl))
        
        
        # The 2nd split of 'Event' tells how 'hard' the ball was hit and where the ball was hit.
        # The first character is also unique except for sac-flies (SF) and sac-bunts (SH).
        # Assign the type of AB as this first character, but when that character is 'S' take the 2nd character instead.
        ab_outcome['Type'] = ab_outcome[1].str[0]
        ab_outcome.loc[ab_outcome[(ab_outcome[1].str[0]=='S')].index,'Type'] = ab_outcome[1].str[1]
        
        # Translate each specific type into (G)round ball, (F)ly ball, (P)op Fly, (T)hrowing Error,
        # Unspecified (D)ouble Play, or No Contact (NC)
        all_launch_types = 'GFLP789BTDH'
        all_launch_repl =  'GFFPFFFGTDG'
        ab_outcome['Type'] = ab_outcome['Type'].str.translate(str.maketrans(all_launch_types,all_launch_repl))
        ab_outcome['Type'].fillna('NC',inplace=True)

        return ab_outcome[['Count','Outcome','Type']]
    
    
    # For away games, the at-bats will be spread throughout multiple raw files
    # The class must be able to handle merging data from multiple files.
    # New additions need to be cleaned, added to events, outcomes, and counts.
    def merge_games(self, new_games):
        new_games_cleaned = self.clean_pitches(new_games)
        self.event_data = pd.concat([self.event_data, new_games_cleaned])
        self.outcomes = self.at_bat_outcomes()
        self.counts = self.outcomes['Count'].value_counts()
        
    
    # Create the transformation matrix for modifying batting strategy
    def transformation_matrix(self):
        simple_pitch = self.parsing_pitches()
        
        # Only keep unique pitch counts during each at-bat
        counts_reached = self.pitch_counts_during_ab(simple_pitch).groupby(level=[0,1]).unique() 
        
        # Create a DataFrame recording how frequently each terminal count is reached from a particular count
        num_counts = len(self.counts_str)
        term_from_cur = pd.DataFrame(np.zeros((num_counts,num_counts)), index = self.counts_str, columns = self.counts_str)
        
        # For each at-bat, iterate through the pitch counts reached and record the terminal pitch count for the at-bat
        for atbat in counts_reached.to_list():
            for count in atbat:
                term_from_cur.loc[count,atbat[-1]] += 1
                
        # For the Transformation matrix, we need to find the total number of at-bats the end after a given count
        for i in self.counts_str:
            term_from_cur.loc[i,i] = 0
        
        relative_frac = term_from_cur.div(term_from_cur.sum(axis=1),axis=0).fillna(0) - np.identity(num_counts)
        relative_frac.loc['32','32'] = 0
        
        return relative_frac.T
        
    
    # Convert string of pitches during at-bat into an ordered list of all pitch counts reached during the at-bat
    def pitch_counts_during_ab(self, pitch_strings):
        # Start the at-bat at 0-0 count, which we will label as a zero (anything other than B or S)
        # Look at each pitch during the at-bat, other than the final pitch
        stacked_pitch = ('0'+pitch_strings.str[0:-1]).str.split('',expand=True).stack()
        
        # A batter will occasionally foul off enough pitches that more than 9 'strikes' occur in the at-bat.
        # Cumulative sum over Balls = 100 and Strikes = 1 will correctly identify an expanded version of the pitch count
        pc_during_ab = stacked_pitch.drop(stacked_pitch[stacked_pitch==''].index).str.translate(str.maketrans({'B':'100','S':'1'})).astype(int).groupby(level=[0,1]).cumsum()
        
        # If a pitch count goes above 4 balls without the at-bat ending (due to umpire error), the at-bat continues with 3 balls
        counts_cap_ball = pc_during_ab*(pc_during_ab//100 < 4) + (300+pc_during_ab%100)*(pc_during_ab//100 > 3)
        
        # If more than 3 'strikes' occur during an at-bat, do not iterate the pitch count higher than x-2
        counts_cap_strike = counts_cap_ball*(counts_cap_ball%100 < 3) + (2 + 100*(counts_cap_ball//100))*(counts_cap_ball%100 >2)
        
        # Convert the counts in the form B-0-S into a string 'BS'
        return (counts_cap_strike//100).astype(str) + (counts_cap_strike%100).astype(str)
        
    
    # Reduce each type of pitch into strikes and balls
    # N (No pitch) and U (no data) are converted into None values
    def parsing_pitches(self, all_pitch_types='CFIKLMOPQRTV', all_pitch_repl='SSBSSSSBSSSB', pitch_none='NU'):
        return self.event_data['Pitches'].str.translate(str.maketrans(all_pitch_types,all_pitch_repl,pitch_none))
    
    
    # For pitch within an at-bat, record what happens.
    # Need to keep record of balls, hit-by-pitch, called strikes, swinging strikes, fouls, foul bunts, and balls-in-play
    def set_count_outcomes(self):
        all_pitch_types = 'IKMOPQRTV'
        all_pitch_repl =  'BSSSBSFSB'
        team_pitches = self.parsing_pitches(all_pitch_types, all_pitch_repl)
        stacked_pitch = (team_pitches).str.split('', expand=True).stack()
        stacked_pitch = stacked_pitch.drop(stacked_pitch[stacked_pitch==''].index)
        
        # For each pitch during each at-bat, add the current pitch count
        # Translating each pitch into an updated count is dealt with inside the Team class file
        pitches_and_counts = pd.concat([self.pitch_counts_during_ab(self.parsing_pitches()),stacked_pitch],axis=1)
        pitches_and_counts.columns = ['Count','Outcome']
        
        return pitches_and_counts
    
    
    # Determine the team's count specific plate discipline stats: Zone%, O-Contact%, Z-Contact%
    def plate_discipline(self, zcontact, ocontact):
        # Group pitch labels, dropping special labels now that each count is correctly identified
        simple_pitch = pd.DataFrame()
        simple_pitch['B'] = self.count_outcomes['B']+self.count_outcomes['H'] # Pitches outside the strike zone w/o swing
        simple_pitch['C'] = self.count_outcomes['C'] # Pitches inside the strike zone w/o swing
        simple_pitch['S'] = self.count_outcomes['S'] # Pitches swung at w/o contact
        simple_pitch['X'] = self.count_outcomes['X'] + self.count_outcomes['L'] + self.count_outcomes['F'] # Pitches swung at w/ contact
        simple_pitch['Total'] = self.count_outcomes.sum(axis=1) # Total number of pitches thrown at a particular count
        
        # Solve for the values of SZ, SO
        A = np.array([[1,1],[ocontact/(1-ocontact),zcontact/(1-zcontact)]])
        simple_pitch_zosep = pd.concat([simple_pitch, simple_pitch[['S','X']].dot(np.linalg.inv(A).T)],axis=1).rename(columns={0:'SO',1:'SZ'})

        # If SO is negative due to the approximation made with seasonal average, set it to zero and correct SZ.
        simple_pitch_zosep.loc[(simple_pitch_zosep['SO']<0),'SZ'] = simple_pitch_zosep['SO'] + simple_pitch_zosep['SZ']
        simple_pitch_zosep.loc[(simple_pitch_zosep['SO']<0),'SO'] = 0

        # Calculate the split of X into Z/O
        simple_pitch_zosep['XO'] = simple_pitch_zosep['SO']*ocontact/(1-ocontact)
        simple_pitch_zosep['XZ'] = simple_pitch_zosep['SZ']*zcontact/(1-zcontact)
        simple_pitch_zosep.loc[np.abs(simple_pitch_zosep[['XZ','XO']].sum(axis=1)<1E-5), 'XZ'] = simple_pitch_zosep['X']

        # Calculate Z/O-Swing% and Zone%
        simple_pitch_zosep['O-Swing%'] = simple_pitch_zosep[['XO','SO']].sum(axis=1)/simple_pitch_zosep[['B','XO','SO']].sum(axis=1)
        simple_pitch_zosep['Z-Swing%'] = simple_pitch_zosep[['SZ','XZ']].sum(axis=1)/simple_pitch_zosep[['C','SZ','XZ']].sum(axis=1)
        simple_pitch_zosep['Zone%'] = simple_pitch_zosep[['C','SZ','XZ']].sum(axis=1)/simple_pitch_zosep['Total']
        
        # Set Z/O-Contact% for each count equal to season average
        simple_pitch_zosep['O-Contact%'] = ocontact
        simple_pitch_zosep['Z-Contact%'] = zcontact
        
        self.plate_disc = simple_pitch_zosep
    

    
def setup_teams(path,homeaway):
    pbp_files = os.listdir(path)
    team_dict = {}
    for file in pbp_files:
        team = file[4:7]
        year = file[:4]
        team_data = pd.read_csv(path+file,index_col=[0,1])
        team_dict[year+team] = Team(team, year, team_data, homeaway)
    return team_dict

            
if __name__ == "__main__":
    path_home = './PbP_HomeCSV/'
    path_away = './PbP_AwayCSV/'

    team_dict_home = setup_teams(path_home,1)
    team_dict_away = setup_teams(path_away,0)