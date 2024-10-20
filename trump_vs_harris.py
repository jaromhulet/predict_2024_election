import pandas as pd
import numpy as np

state_info = pd.read_csv('state_info.csv')

def simulate_votes(df):

    '''
        Takes state election information, simulates and sums individual votes
        by state and determines if Trump of Harris won the state.

        input:
            df (DataFrame) : dataframe containing (1) simulated voter turnout
                             (2) Harris poll numbers and (3) Trump poll numbers

        returns: 
            winner_list (list) : list, ordered by original state ordering in input df
                                 of all 'Harris' and 'Trump' strings - representing
                                 the winner of the corresponding state

    '''

    voter_turnout_arr = df['Voter Turnout'].values
    harris_vote_poll_arr = df['Poll Numbers for Harris'].values/100
    trump_vote_poll_arr = df['Poll Numbers for Trump'].values/100

    winner_list = []

    # loop through all states 
    for voter_turnout, harris_poll, trump_poll in zip(voter_turnout_arr, harris_vote_poll_arr, trump_vote_poll_arr):
        
        # get random number from uniform distritbution with min = 0 and max = 1
        random_votes = np.random.uniform(0, 1, size=voter_turnout)

        # compare random number to Harris polling numbers and assign vote according
        harris_votes = np.where(random_votes <= harris_poll, 1, 0)
        total_harris_votes = np.sum(harris_votes)

        # compare random number to Trump polling numbers and assign vote according
        # note we add Trump poll #'s to Harris poll numbers so they are on different places in the number line
        trump_votes = np.where((random_votes > harris_poll) &
                               ((trump_poll + harris_poll) >= random_votes), 1, 0)
        total_trump_votes = np.sum(trump_votes)   

        # compare state-wide votes for Trump and Harris to determine winner of state election
        if total_harris_votes > total_trump_votes:
            winner = 'Harris'
        else:
            winner = 'Trump'

        winner_list.append(winner)

    return winner_list


def simulate_election(df, add_random_error = False):

    '''
        Runs a full national election simulation given a dataframe with
        historical voting information, electoral information and polling
        information by state.
        
        inputs:
            df (dataframe) : contains state specific info needed to simulate
                            election
            add_random_error (bool) : indicates if margin of error should be 
                                    used to modify polling numbers randomly

        outputs:
            election_winner (list) : list ordered by state of winners
            df_copy_short (dataframe) : dataframe with a row for each state 
                                        and simulation and a column indicating
                                        the winner
        '''    

    df_copy = df.copy()
    
    df_copy['Voter Turnout'] = df_copy.apply(lambda x: sum(np.random.binomial(n = 1,
                                                                             p = x['Voter Turnout Percent (2020)']/100,
                                                                             size = x['Total Registered Voters'])), 
                                                                             axis=1)
    
    if add_random_error:

        # add error for Harris
        harris_errors = np.random.normal(loc=0, scale=df_copy['Margin of Error']/100, size=len(df_copy))
        df_copy['error adj Harris poll'] = df_copy['Poll Numbers for Harris']/100 + harris_errors

        # add error for Trump
        trump_errors = np.random.normal(loc=0, scale=df_copy['Margin of Error']/100, size=len(df_copy))
        df_copy['error adj Trump poll'] = df_copy['Poll Numbers for Trump']/100 + trump_errors

        # rescale if Harris and Trump add up to more than 1
        df_copy['error adj Harris poll'] = np.where((df_copy['error adj Harris poll'] + df_copy['error adj Trump poll']) > 1, 
                                                     df_copy['error adj Harris poll']/(df_copy['error adj Harris poll'] + df_copy['error adj Trump poll']),
                                                     df_copy['error adj Harris poll'])
        
        df_copy['error adj Trump poll'] = np.where((df_copy['error adj Harris poll'] + df_copy['error adj Trump poll']) > 1, 
                                                     df_copy['error adj Trump poll']/(df_copy['error adj Harris poll'] + df_copy['error adj Trump poll']),
                                                     df_copy['error adj Trump poll'])        
    
    df_copy['State Winner'] = simulate_votes(df_copy)

    df_copy['Harris Electoral Votes'] = np.where(df_copy['State Winner'] == 'Harris', df_copy['Electoral Votes'], 0)

    df_copy['Trump Electoral Votes'] = np.where(df_copy['State Winner'] == 'Trump', df_copy['Electoral Votes'], 0)


    # get the states that each candidate won
    df_copy['harris_wins_bool'] = np.where(df_copy['Harris Electoral Votes'] != 0, 'Harris', None)
    df_copy['trump_wins_bool'] = np.where(df_copy['Trump Electoral Votes'] != 0, 'Trump', None)
    df_copy['state_winner'] = df_copy['harris_wins_bool'].fillna(df_copy['trump_wins_bool'] )


    if df_copy['Harris Electoral Votes'].sum() > df_copy['Trump Electoral Votes'].sum():
        election_winner = 'Harris'
    else:
        election_winner = 'Trump'

    df_copy_short = df_copy[['State', 'state_winner']]

    return election_winner, df_copy_short

# simulate multiple elections
election_winner_list = []

iter_count = 0
for _ in range(1000):

    iter_count += 1
    if iter_count % 100 == 0:
        print(f'running iteration {iter_count}')

    winner, temp_df = simulate_election(state_info, add_random_error = True)
    temp_df['iter'] = iter_count

    if iter_count == 1:
        winner_df = temp_df
    else:
        winner_df = pd.concat([winner_df, temp_df], axis = 0)

    election_winner_list.append(winner)


winner_df.to_csv('winner_results_error_100.csv')

results_dict = {'winner' : election_winner_list}
results_df = pd.DataFrame(results_dict)
results_df.to_csv('simulation_results_error_100.csv')

harris_wins = np.sum(np.where(results_df['winner'] == 'Harris', 1, 0))
trump_wins = np.sum(np.where(results_df['winner'] == 'Trump', 1, 0))

print(f'Harris won {harris_wins} times, Trump won {trump_wins} times')

