import pandas as pd
import numpy as np

state_info = pd.read_csv('state_info.csv')

def simulate_votes(df):

    voter_turnout_arr = df['Voter Turnout'].values
    harris_vote_poll_arr = df['Poll Numbers for Harris'].values/100
    trump_vote_poll_arr = df['Poll Numbers for Trump'].values/100

    # print(f'harris poll #s')
    # print(harris_vote_poll_arr[0:9])

    # print(f'trump poll #s')
    # print(trump_vote_poll_arr[0:9])

    winner_list = []

    for voter_turnout, harris_poll, trump_poll in zip(voter_turnout_arr, harris_vote_poll_arr, trump_vote_poll_arr):
        
        random_votes = np.random.uniform(0, 1, size=voter_turnout)

        # print('votes')
        # print(random_votes)

        harris_votes = np.where(random_votes <= harris_poll, 1, 0)
        total_harris_votes = np.sum(harris_votes)

        # print('harris votes')
        # print(harris_votes)

        trump_votes = np.where((random_votes > harris_poll) &
                               ((trump_poll + harris_poll) >= random_votes), 1, 0)
        total_trump_votes = np.sum(trump_votes)   

        # print('Trump votes')
        # print(trump_votes)


        if total_harris_votes > total_trump_votes:
            winner = 'Harris'
        else:
            winner = 'Trump'

        winner_list.append(winner)

    return winner_list


def simulate_voter_turnout(df, add_random_error = False):

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

    # print(f'Harris electoral votes = {df_copy['Harris Electoral Votes'].sum()}')
    # print(f'Trump electoral votes = {df_copy['Trump Electoral Votes'].sum()}')
    # print(len(df_copy))

    # get the states that each candidate won
    df_copy['harris_wins_bool'] = np.where(df_copy['Harris Electoral Votes'] != 0, 'Harris', np.nan)
    df_copy['trump_wins_bool'] = np.where(df_copy['Trump Electoral Votes'] != 0, 'Trump', np.nan)
    df_copy['state_winner'] = df_copy['harris_wins_bool'].fillna(df_copy['trump_wins_bool'] )


    if df_copy['Harris Electoral Votes'].sum() > df_copy['Trump Electoral Votes'].sum():
        election_winner = 'Harris'
    else:
        election_winner = 'Trump'

    return election_winner, df_copy

# simulate multiple elections
election_winner_list = []

iter_count = 0
for _ in range(100):

    iter_count += 1
    if iter_count % 10 == 0:
        print(f'running iteration {iter_count}')

    winner, _ = simulate_voter_turnout(state_info, add_random_error = True)

    election_winner_list.append(winner)

results_dict = {'winner' : election_winner_list}
results_df = pd.DataFrame(results_dict)
results_df.to_csv('simulation_results_error_100.csv')

harris_wins = np.sum(np.where(results_df['winner'] == 'Harris', 1, 0))
trump_wins = np.sum(np.where(results_df['winner'] == 'Trump', 1, 0))

print(f'Harris won {harris_wins} times, Trump won {trump_wins} times')

