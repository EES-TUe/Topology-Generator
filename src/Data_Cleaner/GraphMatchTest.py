from networkx import graph_edit_distance, graph_atlas
import random
import time

def calculate_graph_edit_distance_between_two_random_graphs(range_1, range_2):
    g1 = graph_atlas(random.randint(range_1[0], range_1[1]))
    g2 = graph_atlas(random.randint(range_2[0], range_2[1]))
    start = time.time()
    distance = graph_edit_distance(g2, g1)
    end = time.time()
    elapsed_time = end - start
    # print(f"Distance: {distance}, elapsed time: {elapsed_time}")
    return elapsed_time

def main():
    range_g3 = (4, 7)
    range_g4 = (8, 18)
    range_g5 = (19, 52)
    range_g6 = (53, 208)
    range_g7 = (209, 1252)
    
    total_time_g5_g7 = 0
    total_time_g3_g5 = 0
    total_time_g3_g7 = 0
    total_time_g4_g7 = 0
    total_time_g6_g7 = 0
    n_of_iterations = 100
    for i in range(0,n_of_iterations):
        # print("Calculating distance between g4 and g5")
        total_time_g5_g7 += calculate_graph_edit_distance_between_two_random_graphs(range_g5, range_g7)
        # print("Calculating distance between g8 and g10")
        total_time_g3_g5 += calculate_graph_edit_distance_between_two_random_graphs(range_g3, range_g5)
        # print("Calculating distance between g3 and g7")
        total_time_g3_g7 += calculate_graph_edit_distance_between_two_random_graphs(range_g3, range_g7)
        # print("Calculating distance between g4 and g7")
        total_time_g4_g7 += calculate_graph_edit_distance_between_two_random_graphs(range_g4, range_g7)
        # print("Calculating distance between g6 and g7")
        total_time_g6_g7 += calculate_graph_edit_distance_between_two_random_graphs(range_g6, range_g7)

    
    print(f"Average time for g3 and g5: {total_time_g3_g5 / n_of_iterations}")
    print(f"Average time for g5 and g7: {total_time_g5_g7 / n_of_iterations}")
    print(f"Average time for g3 and g7: {total_time_g3_g7 / n_of_iterations}")
    print(f"Average time for g4 and g7: {total_time_g4_g7 / n_of_iterations}")
    print(f"Average time for g6 and g7: {total_time_g6_g7 / n_of_iterations}")


if __name__ == '__main__':
    main()