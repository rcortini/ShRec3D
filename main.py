"""
Python implementation of the ShRec3D algorithm
"""

import numpy as np
import numpy.linalg as npl

import networkx as nx

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def contacts2distances(contacts):
    """ Infer distances from contact matrix
    """
    # create graph
    graph = nx.Graph()
    graph.add_nodes_from(range(contacts.shape[0]))

    for row in range(contacts.shape[0]):
        for col in range(contacts.shape[1]):
            freq = contacts[row, col]
            if freq != 0:
                graph.add_edge(col, row, weight=1/freq)

    # find shortest paths
    spaths = nx.shortest_path_length(graph, weight='weight')

    # create distance matrix
    distances = np.zeros(contacts.shape)
    for row in range(contacts.shape[0]):
        for col in range(contacts.shape[1]):
            try:
                distances[row, col] = spaths[row][col]
            except KeyError:
                # no path in graph is infinite distance
                distances[row, col] = 1000000

    return distances

def distances2coordinates(distances):
    """ Infer coordinates from distances
    """
    N = distances.shape[0]
    d_0 = []

    # compute distances from center of mass
    for i in range(N):
        sum1 = sum([distances[i, j]**2 for j in range(N)])
        sum2 = sum([sum([distances[j, k]**2 for k in range(j+1, N)]) for j in range(N)])

        val = 1/N * sum1 - 1/N**2 * sum2
        d_0.append(val)

    # generate gram matrix
    gram = np.zeros(distances.shape)
    for row in range(distances.shape[0]):
        for col in range(distances.shape[1]):
            dists = d_0[row]**2 + d_0[col]**2 - distances[row, col]**2
            gram[row, col] = 1/2 * dists

    # extract coordinates from gram matrix
    coordinates = []
    vals, vecs = npl.eigh(gram)

    vals = vals[N-3:]
    vecs = vecs.T[N-3:]

    #print('eigvals:', vals) # must all be positive for PSD (positive semidefinite) matrix

    # same eigenvalues might be small -> exact embedding does not exist
    # fix by replacing all but largest 3 eigvals by 0
    # better if three largest eigvals are separated by large spectral gap

    for val, vec in zip(vals, vecs):
        coord = vec * np.sqrt(val)
        coordinates.append(coord)

    return np.array(coordinates).T

def deconstruct(coordinates, epsilon=0.2):
    """ Derive contact matrix from given set of coordinates
    """
    dimension = coordinates.shape[1]

    # get distances
    distances = np.zeros((coordinates.shape[0], coordinates.shape[0]))
    for row in range(coordinates.shape[0]):
        for col in range(coordinates.shape[0]):
            comp_sum = sum([(coordinates[row, d] - coordinates[col, d])**2 for d in range(dimension)])
            distances[row, col] = np.sqrt(comp_sum)

    # get contacts
    contacts = distances <= epsilon
    return contacts.astype(int)

def apply_shrec3d(contacts):
    """ Apply algorithm to data in given file
    """
    distances = contacts2distances(contacts)
    coordinates = distances2coordinates(distances)

    return coordinates

def visualize(coords, rec_coords):
    """ Plot 3D coordinates
    """
    fig = plt.figure()
    ax = fig.gca(projection='3d')

    ax.scatter(*zip(*coords), color='blue', label='original points')
    ax.scatter(*zip(*rec_coords), color='red', label='reconstructed points')

    ax.legend()

    plt.show()

def main():
    """ Main function
    """
    coords = np.array([
        [1.2,0,0],
        [1.4,0,0],  [1.4,0.2,0], [1.4,0.4,0],
        [1.6,0,0],              [1.6,0.4,0],
        [1.8,0,0],              [1.8,0.4,0],
        [2,0,0],    [2,0.2,0],     [2,0.4,0]
    ])

    contacts = deconstruct(coords, epsilon=0.21)
    rec_coords = apply_shrec3d(contacts)

    visualize(coords, rec_coords)

if __name__ == '__main__':
    main()