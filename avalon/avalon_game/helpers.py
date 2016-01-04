def mission_size(num_players, round_num):
    if num_players == 5:
        if round_num == 1:
            return (2, 1)
        elif round_num == 2:
            return (3, 1)
        elif round_num == 3:
            return (2, 1)
        elif round_num == 4:
            return (3, 1)
        elif round_num == 5:
            return (3, 1)
    elif num_players == 6:
        if round_num == 1:
            return (2, 1)
        elif round_num == 2:
            return (3, 1)
        elif round_num == 3:
            return (4, 1)
        elif round_num == 4:
            return (3, 1)
        elif round_num == 5:
            return (4, 1)
    elif num_players == 7:
        if round_num == 1:
            return (2, 1)
        elif round_num == 2:
            return (3, 1)
        elif round_num == 3:
            return (3, 1)
        elif round_num == 4:
            return (4, 2)
        elif round_num == 5:
            return (4, 1)
    elif num_players > 7 and num_players < 11:
        if round_num == 1:
            return (3, 1)
        elif round_num == 2:
            return (4, 1)
        elif round_num == 3:
            return (5, 1)
        elif round_num == 4:
            return (5, 2)
        elif round_num == 5:
            return (5, 1)
    else:
        raise ValueError("Invalid # of players %d or round number %d" %\
                         (num_players, round_num))

def mission_size_string(mission_size):
    if mission_size[1] == 2:
        return "%d*" % mission_size[0]
    else:
        return "%d" % mission_size[0]
