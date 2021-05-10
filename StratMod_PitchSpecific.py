import numpy as np
import pandas as pd
from TeamData import *

# Given a team's change in strategy, modify the number of outcomes for each pitch in different counts.
def modify_count_outcomes(team_class, swing_changes): 
    pitch_counts = team_class.plate_disc
    mod_count_outcomes = pitch_counts[['B','C','S','X']].copy()
    
    # Assume hitters will not get hit-by-pitch more often
    mod_count_outcomes['B'] = pitch_counts['B'] - team_class.count_outcomes['H'] + swing_changes[['X>B','S>B','B>X','B>S']].dot(np.array([1,1,-1,-1]))
    mod_count_outcomes['H'] = team_class.count_outcomes['H']
    
    mod_count_outcomes['C'] = pitch_counts['C'] + swing_changes[['X>C','S>C','C>X','C>S']].dot(np.array([1,1,-1,-1]))
    mod_count_outcomes['S'] = pitch_counts['S'] + swing_changes[['C>S','B>S','S>B','S>C']].dot(np.array([1,1,-1,-1]))

    # Additional swings are not bunts, so no extra foul bunts (only relevant for strike 3 on foul bunt)
    mod_count_outcomes['X'] = pitch_counts['X']  - team_class.count_outcomes['L'] + swing_changes[['C>X','B>X','X>B','X>C']].dot(np.array([1,1,-1,-1]))
    mod_count_outcomes['L'] = team_class.count_outcomes['L']
    
    return contact_to_inplay(team_class, mod_count_outcomes)


# Distinguish between different types of contact made; Fair vs Foul terrirory, out vs hit.
# Given a modified strategy, we assume the ratio of these events remains the same as the unmodified strategy.
def contact_to_inplay(team_class, mod_count_outcomes):
    old_count_outcomes = team_class.count_outcomes
    
    # Split contact made on the pitch into foul or fair territory using team data for each count
    # The remaining column of fair territory is labelled 'X' to split again
    pitch_contact_result = pd.concat([mod_count_outcomes.drop(columns=['X']),
                                      old_count_outcomes[['F','X']].div(old_count_outcomes[['F','X']].sum(axis=1),axis=0)*np.array([mod_count_outcomes['X'].values]).T],
                                     axis=1)
    pitch_contact_result = pitch_contact_result[['B','H','C','S','L','F','X']]
    pitch_contact_result.columns = ['Ball','HBP','CStrike','SStrike','FBunt', 'Foul','X']
    
    # Split the remaining pitches hit into play into their respective outcomes (Out, Single, Double, Triple, HR)
    inplay_outcomes = team_class.outcomes.groupby('Count')['Outcome'].value_counts().unstack().fillna(0)[['O','S','D','T','R']]
    inplay_outcomes.set_index(old_count_outcomes.index,inplace=True)
    inplay_outcomes.columns = ['Out','Single','Double','Triple','HR']
    
    return pd.concat([pitch_contact_result.drop(columns=['X']),
                    inplay_outcomes.div(inplay_outcomes.sum(axis=1),axis=0)*np.array([pitch_contact_result['X'].values]).T],
                    axis=1)


# Implements game rules for determining how one pitch count moves to another
def group_pitch_outcomes(count_outcomes):
    # Group which outcomes have the same result, depending on the pitch count
    grouped_outcomes = count_outcomes[['Out','Single','Double','Triple','HR']].copy()
    grouped_outcomes.loc[count_outcomes.index.str[0]=='3','Ball'] = 0
    grouped_outcomes.loc[count_outcomes.index.str[0]=='3','Walk'] = count_outcomes[['Ball','HBP']].sum(axis=1)
    grouped_outcomes.loc[count_outcomes.index.str[0]!='3','Ball'] = count_outcomes['Ball']
    grouped_outcomes.loc[count_outcomes.index.str[0]!='3','Walk'] = count_outcomes['HBP']
    grouped_outcomes.loc[count_outcomes.index.str[1]=='2','Strike'] = 0
    grouped_outcomes.loc[count_outcomes.index.str[1]=='2','Self'] = count_outcomes['Foul']
    grouped_outcomes.loc[count_outcomes.index.str[1]=='2','Strikeout'] = count_outcomes[['CStrike','SStrike','FBunt']].sum(axis=1)
    grouped_outcomes.loc[count_outcomes.index.str[1]!='2','Strike'] = count_outcomes[['CStrike','SStrike','FBunt','Foul']].sum(axis=1)
    grouped_outcomes.loc[count_outcomes.index.str[1]!='2','Self'] = 0
    grouped_outcomes.loc[count_outcomes.index.str[1]!='2','Strikeout'] = 0
    return grouped_outcomes


# Creates a stochastic matrix describing the transitions between different pitch counts and outcomes from a single pitch
def transformation_matrix(grouped_outcomes):
    outcome_labels = ['Strikeout','Out','Walk','Single','Double','Triple','HR']
    count_labels = grouped_outcomes.index.tolist()
    all_labels = count_labels+outcome_labels
    transition_matrix = pd.DataFrame(index=all_labels, columns=all_labels)
    
    # For each count (b,s), determine the number of times the count moves to (b,s), (b+1,s), and (b,s+1)
    for count in count_labels:
        b = int(count)//10
        s = int(count)%10
        transition_matrix.loc[count,count] = grouped_outcomes.loc[count,'Self']
        if s<2:
            transition_matrix.iloc[3*b+s, 3*b+s+1] = grouped_outcomes.loc[count,'Strike']
        if b<3:
            transition_matrix.iloc[3*b+s, 3*(b+1)+s] = grouped_outcomes.loc[count,'Ball']
            
    # Determine the number of times an at-bat ends with some outcome at each count
    for end_outcome in outcome_labels:
        transition_matrix[end_outcome] = grouped_outcomes[end_outcome]    
    transition_matrix.fillna(0,inplace=True)
    
    # Convert number of events at a particular count into percent chances to produce Markov Chain
    # When the at-bat ends, it cannot be started back up, so the outcomes of at-bats have extra conditions
    MC = transition_matrix.div(transition_matrix.sum(axis=1),axis=0).T
    for end_outcome in outcome_labels:
        MC.loc[:,end_outcome] = 0
        MC.loc[end_outcome, end_outcome] = 1
    return MC


# Approximate the steady state solution by sucessive application of the transition matrix
def steady_state(transition_matrix, initial_vector, iterations):
    v0 = initial_vector
    for _ in range(iterations):
        v0 = transition_matrix.dot(v0)
    return v0


# Modify a team's hitting strategy using the above functions.
# The function will return the average steady state outcomes of the team's total at-bats.
def strategy_mod(team_class, swing_changes):
    # Update number of pitch outcomes for the strategy, and split contact outcomes into fouls, outs, and the different hits
    mod_count_outcomes = modify_count_outcomes(team_class, swing_changes)
    
    # Add game logic and contrust stochastic matrix for transitions
    grouped_outcomes = group_pitch_outcomes(mod_count_outcomes)
    markov_chain = transformation_matrix(grouped_outcomes)
    
    # All at-bats start at the 0-0 count
    initial_vector = np.zeros(len(markov_chain.index))
    initial_vector[0] = 1
    # The longest at-bat in MLB history is 21 pitches.  To be safe, we look out to 25 pitch at-bats.
    # While there is non-zero probability that the at-bat continues, it's effect will be negligible at this point.
    outcomes_ss = steady_state(markov_chain, initial_vector, 25)

    # The resulting vector V represents the probability of each outcome,
    # We multiply by the total number of at-bats in the season to get the predicted number of each outcome
    total_ab = team_class.outcomes['Outcome'].value_counts().sum()
    return outcomes_ss[markov_chain.index[12:]]*total_ab


# Apply an aggressive modification to hitting strategy
# Returns the number of pitches that change from balls and called strikes to swinging strikes and contact
def aggressive_modification(pitch_ZO_sep, count_outcomes, swing_per):
    # Conditional probabilities to determine the ratio of balls to called strikes
    pz_swing = pitch_ZO_sep['Zone%']/(pitch_ZO_sep[['S','X']].sum(axis=1)/pitch_ZO_sep['Total'])*pitch_ZO_sep['Z-Swing%']
    po_swing = (1-pitch_ZO_sep['Zone%'])/(pitch_ZO_sep[['S','X']].sum(axis=1)/pitch_ZO_sep['Total'])*pitch_ZO_sep['O-Swing%']

    # How many balls and called strikes will be swung at
    extra_swings = pd.concat([po_swing,pz_swing], axis=1).multiply(swing_per*pitch_ZO_sep['Total'],axis=0)
    extra_swings.columns = ['B', 'C']

    # If swinging at too many of one type of pitch, take the leftover number from the other type
    # If there are not enough total pitches available, do not take anymore.
    extra_swings.loc[(extra_swings['B'] > pitch_ZO_sep['B'])&(extra_swings['C'] > pitch_ZO_sep['C']),'C'] = pitch_ZO_sep['C']
    extra_swings.loc[(extra_swings['B'] > pitch_ZO_sep['B'])&(extra_swings['C'] > pitch_ZO_sep['C']),'B'] = pitch_ZO_sep['B']-count_outcomes['H']

    extra_swings.loc[(extra_swings['B'] > pitch_ZO_sep['B']+count_outcomes['H']),'C'] = np.minimum(pitch_ZO_sep['C'], extra_swings['C']+extra_swings['B']-pitch_ZO_sep['B']+count_outcomes['H'])
    extra_swings.loc[(extra_swings['B'] > pitch_ZO_sep['B']+count_outcomes['H']),'B'] = pitch_ZO_sep['B']-count_outcomes['H']

    extra_swings.loc[(extra_swings['C'] > pitch_ZO_sep['C']),'B'] = np.minimum(pitch_ZO_sep['B']-count_outcomes['H'], extra_swings['B']+extra_swings['C']-pitch_ZO_sep['C'])
    extra_swings.loc[(extra_swings['C'] > pitch_ZO_sep['C']),'C'] = pitch_ZO_sep['C']

    contact_array = np.array([pitch_ZO_sep.loc[pitch_ZO_sep.index[0],'O-Contact%'],pitch_ZO_sep.loc[pitch_ZO_sep.index[0],'Z-Contact%']])
    
    # Calculate how many of the extra swings will result in contact or not
    # Set the number of swinging strikes and contact converted into balls and called strikes to zero
    swing_contact = extra_swings*contact_array
    swing_nocontact = extra_swings*(1-contact_array)
    swing_contact.columns = ['B>X','C>X']
    swing_nocontact.columns = ['B>S','C>S']
    swing_changes = pd.concat([swing_contact, swing_nocontact],axis=1)
    swing_changes[['X>B','X>C','S>B','S>C']] = 0
    swing_changes.fillna(0,inplace=True)
    
    return swing_changes


# Apply an aggressive modification to hitting strategy
# Returns the number of pitches that change from balls and called strikes to swinging strikes and contact
def patient_modification(pitch_ZO_sep, count_outcomes, swing_per):
    # Conditional probabilities to determine how many balls or called strikes will be added to each count.
    pz_noswing = pitch_ZO_sep['C']/pitch_ZO_sep[['B','C']].sum(axis=1)
    po_noswing = pitch_ZO_sep['B']/pitch_ZO_sep[['B','C']].sum(axis=1)
    
    # Convert probabilities to total pitches
    removed_swings = pd.concat([po_noswing,pz_noswing], axis=1).multiply(swing_per*pitch_ZO_sep['Total'],axis=0)
    removed_swings.columns = ['To B', 'To C']
    
    contact_array = np.array([pitch_ZO_sep.loc[pitch_ZO_sep.index[0],'O-Contact%'],pitch_ZO_sep.loc[pitch_ZO_sep.index[0],'Z-Contact%']])
    
    # Determine which pitches will be removed from contact or no contact swings
    removed_contact = removed_swings*contact_array
    removed_nocontact = removed_swings*(1-contact_array)
    removed_contact.columns = ['X>B','X>C']
    removed_nocontact.columns = ['S>B','S>C']
    swing_changes = pd.concat([removed_contact, removed_nocontact],axis=1)
    swing_changes[['B>X','C>X','B>S','C>S']] = 0
    swing_changes.fillna(0,inplace=True)
    
    # If total number of pitches to change exceed the number of pitches available, convert all available but no more
    swing_changes.loc[(removed_swings[['To B','To C']].sum(axis=1)>pitch_ZO_sep[['X','S']].sum(axis=1)+count_outcomes['L']),'X>B'] = pitch_ZO_sep['XO']
    swing_changes.loc[(removed_swings[['To B','To C']].sum(axis=1)>pitch_ZO_sep[['X','S']].sum(axis=1)+count_outcomes['L']),'X>C'] = pitch_ZO_sep['XZ'] - count_outcomes['L']
    swing_changes.loc[(removed_swings[['To B','To C']].sum(axis=1)>pitch_ZO_sep[['X','S']].sum(axis=1)+count_outcomes['L']),'S>B'] = pitch_ZO_sep['SO']
    swing_changes.loc[(removed_swings[['To B','To C']].sum(axis=1)>pitch_ZO_sep[['X','S']].sum(axis=1)+count_outcomes['L']),'S>C'] = pitch_ZO_sep['SZ']
    
    # Cannot convert Z and O pitches between one another
    # Ratio of Si/Xi pitches is controlled by the i-Contact%, as the split above, so both types are saturated simultaneously
    swing_changes.loc[(swing_changes[['X>B','S>B']].sum(axis=1) > pitch_ZO_sep[['SO','XO']].sum(axis=1)),'X>B'] = pitch_ZO_sep['XO']
    swing_changes.loc[(swing_changes[['X>B','S>B']].sum(axis=1) > pitch_ZO_sep[['SO','XO']].sum(axis=1)),'S>B'] = pitch_ZO_sep['SO']
    swing_changes.loc[(swing_changes[['X>C','S>C']].sum(axis=1) > pitch_ZO_sep[['SZ','XZ']].sum(axis=1)+count_outcomes['L']),'X>C'] = pitch_ZO_sep['XZ'] - count_outcomes['L']
    swing_changes.loc[(swing_changes[['X>C','S>C']].sum(axis=1) > pitch_ZO_sep[['SZ','XZ']].sum(axis=1)+count_outcomes['L']),'S>C'] = pitch_ZO_sep['SZ']

    return swing_changes


# Combines multiple different strategy modifications into a single pitch/swing change DataFrame
def custom_strat_mod(team_class, pva_dict):
    # Full list of counts
    counts_str = team_class.count_outcomes.index.to_list()
    
    # Which counts will have aggressive or patient adjustments, and how much
    aggro_counts = list(pva_dict['Aggressive'].keys())
    aggro_percent_changes = list(pva_dict['Aggressive'].values())
    patient_counts = list(pva_dict['Patient'].keys())
    patient_percent_changes = list(pva_dict['Patient'].values())
    
    # For the list of counts where there will be no changes, set all changes in swings to zero.    
    no_change_index = np.setdiff1d(counts_str, aggro_counts + patient_counts)
    full_swing_changes = aggressive_modification(team_class.plate_disc, team_class.count_outcomes, 0).loc[no_change_index]

    # Find pitch/swing adjustments for all aggressive modified counts
    if len(aggro_counts)!= 0:
        full_swing_changes = pd.concat([full_swing_changes, aggressive_modification(team_class.plate_disc.loc[aggro_counts], team_class.count_outcomes.loc[aggro_counts], aggro_percent_changes)])
        
    # Find pitch/swing adjustments for all patient modified counts
    if len(patient_counts)!= 0:
        full_swing_changes = pd.concat([full_swing_changes, patient_modification(team_class.plate_disc.loc[patient_counts], team_class.count_outcomes.loc[patient_counts], patient_percent_changes)])
    
    return full_swing_changes.sort_index()