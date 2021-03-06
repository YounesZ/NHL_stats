""" This is a first attempt to implement policy iteration strategy to solve Jack's car rental problem 4.5 found in
Sutton and Barto 2003 p.93

This first version considers two car rental agencies that both cumulate 20 cars. Each rented car makes a 10$/day profit
and overnight car transfers between the two agencies cost 2$ per car. We are trying to find the optimal policy in terms
of total reward

Expected cars rented in agencies 1 and 2 are respectively Poisson random variables with lambda=3 and 4
Expected cars returned to agencies 1 and 2 are respectively Poisson random variables with lambda=3 and 2

"""

import numpy as np
import matplotlib.pyplot as plt
import math
from Utils.programming import ut_sum_diagonals, ut_closest, ut_ind2sub
from Utils.maths import ut_poisson_proba
from random import shuffle
import time


# ===============
# Helper functions
# ===============
def precompute_variables(params):
    # Add vehicles moved according to pi
    carflow     =   list(range(-params.get('total_cars') - 5, 0, 1)) + list(range(params.get('total_cars') + 6))
    params['carflow']   =   carflow

    # Probability of rents and returns - agency1
    proba1_rent =   ut_poisson_proba.main(params.get('expected_rent')[0], list(range(params.get('total_cars') + 1 + 5)))
    proba1_rtrn =   ut_poisson_proba.main(params.get('expected_return')[0], list(range(params.get('total_cars') + 1 + 5)))
    jointProba1 =   np.reshape(proba1_rent, [params.get('total_cars') + 1 + 5, 1]) * proba1_rtrn
    jp1sum      =   ut_sum_diagonals.main(jointProba1)
    params['jp1sum']    =   jp1sum

    # Probability of rents and returns - agency1
    proba2_rent =   ut_poisson_proba.main(params.get('expected_rent')[1], range(params.get('total_cars') + 1 + 5))
    proba2_rtrn =   ut_poisson_proba.main(params.get('expected_return')[1], range(params.get('total_cars') + 1 + 5))
    jointProba2 =   np.reshape(proba2_rent, [params.get('total_cars') + 1 + 5, 1]) * proba2_rtrn
    jp2sum      =   ut_sum_diagonals.main(jointProba2)
    params['jp2sum']    =   jp2sum
    return params


def update_value(moved, state_value, ag_cars, params):
    # Convert state to nb of cars in each agency
    ag2, ag1    =   ag_cars

    # Probability of rents and returns - agency1
    nex_state1  =   ag1 + moved + params.get('carflow')
    idX         =   ut_closest.main([0, params.get('total_cars')], nex_state1)
    proba_ag1   =   params.get('jp1sum')[0, [range(idX[0], idX[1] + 1)]]

    # Probability of rents and returns - agency1
    nex_state2  =   ag2 - moved + params.get('carflow')
    idX         =   ut_closest.main([0, params.get('total_cars')], nex_state2)
    proba_ag2   =   params.get('jp2sum')[0, [range(idX[0], idX[1] + 1)]]

    # State probabilities
    stateProba  =   np.reshape(proba_ag2, [params.get('total_cars') + 1, 1]) * proba_ag1

    # State rewards
    poss_rent1  =   ag1 + moved - list(range(params.get('total_cars') + 1))
    poss_rent1  =   np.maximum(poss_rent1, 0)
    reward1     =   poss_rent1 * 10
    poss_rent2  =   ag2 - moved - list(range(params.get('total_cars') + 1))
    poss_rent2  =   np.maximum(poss_rent2, 0)
    reward2     =   poss_rent2 * 10
    state_reward=   np.reshape(reward2, [params.get('total_cars') + 1, 1]) + reward1 - np.abs(moved) * 2

    # Issue state value
    v = np.sum(np.multiply(stateProba, state_reward + state_value * params.get('gamma')))
    return v


def evaluate_policy(optimal_policy, state_value, params):
    # intialize change

    # Add vehicles moved according to pi
    carflow     =   list(range(-params.get('total_cars')-5, 0, 1)) + list(range(params.get('total_cars') + 6))

    # Probability of rents and returns - agency1
    proba1_rent =   ut_poisson_proba.main(params.get('expected_rent')[0], list(range(params.get('total_cars') + 1 + 5)))
    proba1_rtrn =   ut_poisson_proba.main(params.get('expected_return')[0], list(range(params.get('total_cars') + 1 + 5)))
    jointProba1 =   np.reshape(proba1_rent, [params.get('total_cars') + 1 + 5, 1]) * proba1_rtrn
    jp1sum      =   ut_sum_diagonals.main(jointProba1)
    nex_state1  =   ag1 + moved + carflow
    idX         =   ut_closest.main([0, params.get('total_cars')], nex_state1)
    proba_ag1   =   jp1sum[0, [range(idX[0], idX[1] + 1)]]

    # Probability of rents and returns - agency1
    proba2_rent =   ut_poisson_proba.main(params.get('expected_rent')[1], range(params.get('total_cars') + 1 + 5))
    proba2_rtrn =   ut_poisson_proba.main(params.get('expected_return')[1], range(params.get('total_cars') + 1 + 5))
    jointProba2 =   np.reshape(proba2_rent, [params.get('total_cars') + 1 + 5, 1]) * proba2_rtrn
    jp2sum      =   ut_sum_diagonals.main(jointProba2)
    nex_state2  =   ag2 - moved + carflow
    idX         =   ut_closest.main([0, params.get('total_cars')], nex_state2)
    proba_ag2   =   jp2sum[0, [range(idX[0], idX[1] + 1)]]

    # State probabilities
    stateProba  =   np.reshape(proba_ag2, [params.get('total_cars') + 1, 1]) * proba_ag1

    # State rewards
    poss_rent1  =   ag1 + moved - list(range(params.get('total_cars') + 1))
    poss_rent1  =   np.maximum(poss_rent1, 0)
    reward1     =   poss_rent1 * 10
    poss_rent2  =   ag2 - moved - list(range(params.get('total_cars') + 1))
    poss_rent2  =   np.maximum(poss_rent2, 0)
    reward2     =   poss_rent2 * 10
    state_reward=   np.reshape(reward2, [params.get('total_cars') + 1, 1]) + reward1 - np.abs(moved) * 2

    # Issue state value
    v = np.sum(np.multiply(stateProba, state_reward + state_value * params.get('gamma')))
    return v


def evaluate_policy(optimal_policy, state_value, params):
    # intialize change
    n_passes    =   0
    delta_v     =   float('Inf')
    while delta_v > params.get('theta'):
        delta_v = 0
        VV      = np.zeros([21,21])
        # Shuffle the order of value evaluation
        shufI   =   [[i] for i in range( (params.get('total_cars')+1) ** 2 )]
        shuffle(shufI)
        for sii in shufI:
            r,c     =   ut_ind2sub.main(np.shape(state_value), sii)
            temp    =   state_value[r,c]
            new_v   =   update_value(optimal_policy[r, c], state_value, (r,c), params)
            state_value[r,c]    =   new_v
            delta_v =   np.maximum(delta_v, np.abs(temp - new_v))
            VV[r,c] =   float(np.abs(temp - new_v))
        n_passes += 1
    return state_value, n_passes


def improve_policy(optimal_policy, state_value, params):
    policy_stable   =   True
    n_states        =   (params.get('total_cars')+1) ** 2
    # Predefined actions
    actions_poss    =   np.array( range(-5,6,1) )
    for sii in range(n_states):
        ag2, ag1    =   ut_ind2sub.main(np.shape(state_value), [sii])
        temp        =   optimal_policy[ag2, ag1]
        # Loop on all possible actions and recompute the value
        for sjj in actions_poss:
            new_val =   update_value(sjj, state_value, (ag2, ag1), params)
            if new_val>state_value[ag2, ag1]:
                state_value[ag2, ag1]       =   new_val
                optimal_policy[ag2, ag1]    =   sjj
        if temp!=optimal_policy[ag2, ag1]:
            policy_stable   =   False
    return optimal_policy, policy_stable






# ===============
# Main function
# ===============
def main():

    print("\n\n\t***\tStarted to solve 2D MDP: the car rental problem\n\n")

    start_time  =   time.time()

    # Problem settings
    params  =   {'total_cars'   : 20,       # among the 2 agencies\
                'rental_profit' : 10,       # per car, per day
                'max_transfer'  : 5,        # par night
                'transfer_cost' : 2,        # per car
                'expected_rent' : [3, 4],
                'expected_return':[3, 2],
                'theta'         : 0.1,      # change tolerance, useful in policy evaluation
                'gamma'         : 0.9,      # reward discount exponent
                'stable_policy' : False}

    # Initialization
    state_value     =   np.zeros([params.get('total_cars')+1, params.get('total_cars')+1])
    optimal_policy  =   np.zeros([params.get('total_cars')+1, params.get('total_cars')+1])

    # Pre-compute redundant variables
    params          =   precompute_variables(params)

    # Solve MDP
    stable_policy   =   False
    n_passes        =   0
    while not(stable_policy):
        print("\tPass number ", n_passes+1, )
        state_value, _                  =   evaluate_policy(optimal_policy, state_value, params)
        print("evaluation done, ")
        optimal_policy, stable_policy   =   improve_policy(optimal_policy, state_value, params)
        print("improvement done.\n")
        n_passes    +=  1

    print("\t--- All done in %s seconds ---" % (time.time() - start_time))

    return state_value, optimal_policy, params, n_passes



# Driver
if __name__ == "__main__":
    main()
