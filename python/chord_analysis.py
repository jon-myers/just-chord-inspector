import numpy as np
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from sympy.utilities.iterables import multiset_permutations
from gspread_formatting import *
import numpy_indexed as npi
from os.path import dirname, abspath
from functools import reduce, lru_cache
import multiprocessing as mp
# from collections import counter
import os, sys, shutil, pickle, copy, gspread, json, jsonpickle, itertools, ray


def memoize(f):
    """ Memoization decorator for functions taking one or more arguments. """
    class memodict(dict):
        def __init__(self, f):
            self.f = f
        def __call__(self, *args):
            return self[args]
        def __missing__(self, key):
            ret = self[key] = self.f(*key)
            return ret
    return memodict(f)


def cartesian_product(*arrays):
    la = len(arrays)
    dtype = np.result_type(*arrays)
    arr = np.empty([len(a) for a in arrays] + [la], dtype=dtype)
    for i, a in enumerate(np.ix_(*arrays)):
        arr[...,i] = a
    return arr.reshape(-1, la)
    

class MyEncoder(json.JSONEncoder):
    def default(self, o):
        return {k.lstrip('_'): v for k, v in vars(o).items()}

class Dyad:


    def __init__(self, origin = [0, 0, 0], vector = [1, 0, 0]):
        self.origin = np.array(origin)
        self.vector = np.array(vector)
        self.terminal = self.origin + self.vector
        self.t_connects = []
        self.o_connects = []

    def __str__(self):
        return str('Dyad: ' + np.str(self.origin) + ' --> ' + np.str(self.terminal))

    def rotate(self, rotation):
        self.vector = np.int16(np.round(R.from_rotvec(rotation).apply(self.vector)))
        self.terminal = self.origin + self.vector
        return self

    def get_id(self):
        return str([self.origin, self.terminal])

    id = property(get_id)

def get_ranks(array):
    temp = array.argsort()
    ranks = np.empty_like(temp)
    ranks[temp] = np.arange(len(array))
    return ranks

class Branch:
    """A unidirectional collection of connected Diads—-no ambiguity in terms of containment"""
    
    def __init__(self, root, dyads, chord):
        self.root = np.array(root)
        self.dyads = dyads
        self.chord = chord
        self.grow_out()
        
    def grow_out(self):
        layer = self.dyads
        index = 0
        while len(layer) > 0:
            next_layer = []
            for dyad in layer:
                for next_dyad in dyad.t_connects:
                    if np.all(next_dyad.origin == dyad.terminal) and next_dyad not in next_layer:
                        next_layer.append(next_dyad)
            self.dyads.extend(next_layer)
            layer = next_layer            
    
    def overlap(self, other_branch):
        """Measures the proportion of branch's dyads that are overlapped 
        by dyads in this other_branch."""
        
        overlapping_dyads = [dyad for dyad in other_branch.dyads if dyad in self.dyads]
        return len(overlapping_dyads) / len(self.dyads)
        
    def get_collective_overlap(self):
        """Measures the proportion of branch's dyads that are overlapped by 
        dyads in all other branches in chord."""
        other_dyads = []
        other_branches = [branch for branch in self.chord.branches if branch != self]
        overlapping_dyads = [dyad for branch in other_branches for dyad in branch.dyads if dyad not in self.dyads]
        return len(overlapping_dyads) / len(self.dyads)
    
    def get_origins(self):
        return np.array([dyad.origin for dyad in self.dyads])
    
    def get_terminals(self):
        return np.array([dyad.terminal for dyad in self.dyads])
        
    def get_proportion(self):
        return round(len(self.dyads) / len(self.chord.dyads), 2)
        
    def get_unique_points(self):
        points = np.vstack((self.origins, self.terminals))
        points = np.unique(points, axis=0)
        points = master_sort(points)
        return points
        
    origins = property(get_origins)
    terminals = property(get_terminals)
    proportion = property(get_proportion)
    collective_overlap = property(get_collective_overlap)
    unique_points = property(get_unique_points)

class Chord:


    def __init__(self, dyads = [Dyad()]):
        self.dyads = dyads
        self.gen_index = None
        self.num = None
        self.layer = None

    def __str__(self):
        dyads = len(self.dyads)
        dims = str(self.dims)
        containers = str(np.shape(self.containers)[0])
        text = 'Chord: {} dyads, {} dimensions, {} roots.'
        return text.format(dyads, dims, containers)

    def print_dyads(self):
        print('\n'.join([dyad.__str__() for dyad in self.dyads]) + '\n')

    def normalize(self):
        mins = np.min(self.origins, axis=0)
        for dyad in self.dyads:
            dyad.origin -= mins
            dyad.terminal -= mins

    def sort_dyads(self):
        unsorted_origin_array = np.array([dyad.origin for dyad in self.dyads])
        unsorted_terminal_array = np.array([dyad.terminal for dyad in self.dyads])
        combined_ranks = np.lexsort((unsorted_origin_array, unsorted_terminal_array), axis = 0)

        for index in range(3)[::-1]:
            unsorted_origin_array = np.array([dyad.origin for dyad in self.dyads])
            unsorted_terminal_array = np.array([dyad.terminal for dyad in self.dyads])
            combined_ranks = np.lexsort((unsorted_origin_array, unsorted_terminal_array), axis = 0)

            self.dyads = [self.dyads[i] for i in combined_ranks[:, index]]




    def get_vecs(self):
        return np.array([dyad.vector for dyad in self.dyads])

    def get_dims(self):
        return np.count_nonzero(np.any(self.vecs.T != 0, axis=1))

    def get_roots(self):
        containers = np.array([dyad.origin for dyad in self.dyads])
        return np.unique(containers, axis=0)

    def get_origins(self):
        return np.array([dyad.origin for dyad in self.dyads])

    def get_terminals(self):
        return np.array([dyad.terminal for dyad in self.dyads])

    def get_id(self):
        return str(np.array([self.origins, self.terminals]))

    def get_unique_points(self):
        points = np.vstack((self.origins, self.terminals))
        points = np.unique(points, axis=0)
        return points

    def get_position_pairs(self):
        out = np.concatenate([self.origins, self.terminals], axis=1)
        shape = np.shape(out)
        return out.reshape((shape[0], 2, int(shape[1]/2)))
        
    def construct_branches(self):
        self.branches = []
        for root in np.unique(self.origins, axis=0):
            dyads = [dyad for dyad in self.dyads if np.all(dyad.origin == root)]
            branch = Branch(root, dyads, self)
            self.branches.append(branch)
            
    def get_branch_nums(self):
        if hasattr(self, 'branches'):
            return [len(branch.dyads) for branch in self.branches]

    def fill_gaps(self):
        """Determine if chord contains a missing connection, and adds appropriate
        dyad"""
        single_inds = np.arange(np.shape(self.unique_points)[0])
        indexes = cartesian_product(single_inds, single_inds)
        diffs = np.subtract(self.unique_points[indexes[:, 0]], self.unique_points[indexes[:, 1]])
        proper_intervals = np.sum(np.abs(diffs), axis=1) == 1 # true if distance between points is 1
        implied_dyads = self.unique_points[indexes[proper_intervals]] # all of the dyads implied by all the points in chord
        implied_dyads = np.sort(implied_dyads, axis=1)
        implied_dyads = np.unique(implied_dyads, axis=0)

        for i_d in implied_dyads:
            test = False
            for dyad in self.dyads:
                if np.all(dyad.origin == i_d[0]) and np.all(dyad.terminal == i_d[1]):
                    test = True
            if not test:
                new_dyad = Dyad(origin = i_d[0], vector = i_d[1] - i_d[0])
                self.connect_points(new_dyad)
                new_dyad.index = len(self.dyads)
                self.dyads.append(new_dyad)


    def connect_points(self, trial_dyad):
        for dyad in self.dyads:
            if np.all(trial_dyad.origin == dyad.origin):
                trial_dyad.o_connects.append(dyad)
                dyad.o_connects.append(trial_dyad)
            elif np.all(trial_dyad.origin == dyad.terminal):
                trial_dyad.o_connects.append(dyad)
                dyad.t_connects.append(trial_dyad)
            elif np.all(trial_dyad.terminal == dyad.origin):
                trial_dyad.t_connects.append(dyad)
                dyad.o_connects.append(trial_dyad)
            elif np.all(trial_dyad.terminal == dyad.terminal):
                trial_dyad.t_connects.append(dyad)
                dyad.t_connects.append(trial_dyad)

    def get_containments(self):
        return sum(self.branch_nums)
    
    def grow_layer(self):
        layer = []
        vectors = [Dyad().vector, Dyad().rotate([0, 0, np.pi / 2]).vector, Dyad().rotate([0, -np.pi / 2, 0]).vector]
        for d, dyad in enumerate(self.dyads):
            for vec in vectors:
                if not np.all(vec == dyad.vector):
                    layer.append(Dyad(origin = dyad.origin, vector = vec))
                if str(vec) not in [str(list(d.vector)) for d in dyad.t_connects]:
                    layer.append(Dyad(origin = dyad.terminal, vector = vec))
                    layer.append(Dyad(origin = dyad.terminal - vec, vector = vec))
                if str(vec) not in [str(list(d.vector)) for d in dyad.o_connects]:
                    layer.append(Dyad(origin = dyad.origin - vec, vector = vec))
        chords = []
        for d, dyad in enumerate(layer):
            if dyad.id  not in [i.id for i in self.dyads]:
                chord = copy.deepcopy(self)
                chord.connect_points(dyad)
                dyad.index = len(chord.dyads)
                chord.dyads.append(dyad)
                chord.fill_gaps()
                chord.sort_dyads()
                chord.normalize()
                chords.append(chord)
        return chords

    def np_multiset_permutations(self, array):
        out = np.array([i for i in multiset_permutations([0, 1, 2])])
        out = array[out]
        return out
    
    
    
    #@property
    def get_rotations(self):
        unique = np.apply_along_axis(self.np_multiset_permutations, 1, self.unique_points)
        unique = np.transpose(unique, (1, 0, 2))
        unique = master_sort(unique)
        return unique
    
    #@property
    def get_distinct_roots(self):
        distinct_roots = []
        for dyad in self.dyads:
            if len(dyad.o_connects) > 0:
                if not False in [np.all(dy.origin == dyad.origin) for dy in dyad.o_connects]:
                    if list(dyad.origin) not in distinct_roots:
                        distinct_roots.append(list(dyad.origin))        
            elif list(dyad.origin) not in distinct_roots:
                    distinct_roots.append(list(dyad.origin)) 
        indexes = npi.indices(self.unique_points, distinct_roots)
        return indexes
    
    #@property
    def get_symmetry(self):
        rots = self.rotations
        compare_indexes = list(itertools.combinations(np.arange(len(rots)), 2))
        ct=0
        for ci in compare_indexes:
            ints = len(npi.intersection(rots[ci[0]], rots[ci[1]]))
            if ints == len(rots[0]):
                ct += 1
        if ct == 0:
            return 0
        elif ct == 3:
            return 1
        elif ct == 15: 
            return 2
    
    #@property        
    def get_stability(self):
        """Number of positions that appear in all six rotations
        divided by the total number of points"""
        if len(self.distinct_roots) == 1:
            rots = self.rotations
            shape = np.shape(rots)
            intersection = npi.intersection(*[i for i in rots])
            return round(len(intersection) / len(self.unique_points), 2)
        else:
            return ''
    
    #@property    
    def get_partial_stability(self):
        """The average of the proportion of rotations in which each unique 
        position is occupied"""
        if len(self.distinct_roots) == 1:
            rots = self.rotations
            shape = np.shape(rots)
            pos_in_rots = np.unique(rots, axis=1)
            pos_tot = npi.union(*[i for i in rots])
            all_pos_occurences = pos_in_rots.reshape((np.int(np.size(pos_in_rots) / 3), 3))
            pos_tot, counts = np.unique(all_pos_occurences, axis=0, return_counts=True)
            out = np.round(np.mean(counts) / 6, 2)
            return out
        else:
            return ''
    
    #@property
    def get_vertices(self):
        """Coordinates of all unique points that are connected to more than one 
        dyad."""
        vertices = [dyad.terminal for dyad in self.dyads if len(dyad.t_connects) > 0]
        vertices += [dyad.origin for dyad in self.dyads if len(dyad.o_connects) > 0]
        if len(vertices) != 0:
            vertices = np.unique(np.array(vertices), axis=0)
        return vertices
    
    #@property
    def get_paths(self):
        intersects = [dyad.terminal for dyad in self.dyads if len(dyad.t_connects) > 1]
        intersects += [dyad.origin for dyad in self.dyads if len(dyad.o_connects) > 1]
        intersects = np.array(intersects)
        if len(intersects) > 0:
            unique = np.unique(intersects, axis=0)
            if self.extremities > 0:
                return self.extremities + self.loops
            else:
                return self.loops + len(intersects) / (3 * self.loops)
        else: 
            return 1
    #@property    
    def get_loops(self):
        """Return the number of dyadic loops in the structure of the chord"""
        return int(len(self.dyads) - self.layer - 1)
        # if len(self.vertices) == len(self.dyads):
        #     return 1
        # elif self.joints == len(self.dyads) - 1:
        #     return 0
        # else:
        #     out = (len(self.dyads) - self.extremities) / 4
        #     return int(np.floor(out))
        
    #@property
    def get_extremities(self):
        """Return the number of dyads that have at least one point unattached to
        any other dyads"""
        return len(self.unique_points) - len(self.vertices)
        
    def get_joints(self):
        """Return the total number of connections between dyads"""
        out = [dyad.t_connects for dyad in self.dyads] + [dyad.o_connects for dyad in self.dyads]
        out = [i for i in out if i != []]
        return out
        
    def get_rotation_shell(self):
        """Return the set of unique points crossed in all possible axis 
        rotations""" 
        rots = self.rotations
        points = rots.reshape((int(np.size(rots)/3), 3))
        return np.unique(points, axis=0)
        

    vecs = property(get_vecs)
    origins = property(get_origins)
    terminals = property(get_terminals)
    dims = property(get_dims)
    containers = property(get_roots)
    id = property(get_id)
    unique_points = property(get_unique_points)
    position_pairs = property(get_position_pairs)
    branch_nums = property(get_branch_nums)
    containments = property(get_containments)
    distinct_roots = property(get_distinct_roots)
    rotations = property(get_rotations)
    symmetry = property(get_symmetry)
    stability = property(get_stability)
    partial_stability = property(get_partial_stability)
    paths = property(get_paths)
    vertices = property(get_vertices)
    loops = property(get_loops)
    extremities = property(get_extremities)
    joints = property(get_joints)
    rotation_shell = property(get_rotation_shell)
    
    
    # chord.dims, len(chord.branches), chord.branch_num_id
    def get_dict(self):
        this_dict = {}
        this_dict['points'] = list([[int(k) for k in list(i)] for i in self.unique_points])
        this_dict['containments'] = int(self.containments)
        this_dict['dims'] = int(self.dims)
        this_dict['numOfBranches'] = len(self.branches)
        this_dict['branchNums'] = [int(i) for i in self.branch_nums]
        this_dict['num_distinct_roots'] = int(len(self.distinct_roots))
        this_dict['distinct_roots'] = [int(i) for i in self.distinct_roots]
        if self.gen_index == None: 
            self.gen_index = 0
        this_dict['gen_index'] = self.gen_index 
        this_dict['symmetry'] = self.symmetry
        this_dict['stability'] = self.stability
        this_dict['partial_stability'] = self.partial_stability
        this_dict['paths'] = self.paths
        this_dict['loops'] = self.loops
        this_dict['rotation_shell'] = [[int(i) for i in j] for j in self.rotation_shell]
        return this_dict
        
        
memo = {}
primes = np.array([2, 3, 5])

def minor_sort(pc_):
    
    # prim_index = np.prod(primes ** pc_, axis=1)

    # sorts = np.argsort(np.prod(primes ** pc_, axis=1))
    sorts = np.lexsort((pc_[:, 2], pc_[:, 1], pc_[:, 0]))

    return pc_[sorts]
    # return pc_

def master_sort(pc):
    for i, p in enumerate(pc):
        pc[i] = minor_sort(p)
    return pc

def mp_get_equal_indexes(rotations, other_chords, pool):
    compare_indexes = cartesian_product(np.arange(len(rotations)), np.arange(len(other_chords)))
    
    rots = rotations[compare_indexes[:,0]] 
    ocs = other_chords[compare_indexes[:, 1]]
    # rots = master_sort(rots)
    # ocs = master_sort(ocs)
    equality_array = np.all(rots == ocs, axis=(1, 2))   
    
     
    # equality_array = np.array(pool.starmap(set_equality, ((rots[i], ocs[i]) for i in range(len(rots)))))
    return compare_indexes[np.nonzero(equality_array)]

def set_equality(rot, oc):
    return np.all(oc == rot)

# def mp_get_unique_points(chord):
    
# @profile
def remove_duplicates(chords, again=False):
    """Gets rid of any chords that are exact duplicates or inverted duplicates"""
    perm_inputs = []
    ids = [chord.id for chord in chords]
    duplicates = [True if id in ids[:i] else False for i, id in enumerate(ids)]
    chords = [chord for i, chord in enumerate(chords) if not duplicates[i]]
    other_chords = np.array([i.unique_points for i in chords])
    removes = []
    if __name__ == '__main__':
        with mp.Pool(processes=16) as pool:
            for chord_index, chord in enumerate(chords):
                rotations = chord.rotations[1:]
                equal_indexes = mp_get_equal_indexes(rotations, other_chords, pool)
                print(chord_index, len(chords), end='\r', flush=True)
                if np.size(equal_indexes) > 0:
                    for ei in equal_indexes:
                        if chord_index != ei[1] and ei[1] > chord_index and  chord_index not in removes:
                            removes.append(ei[1])
                                  
            chords = [chord for i, chord in enumerate(chords) if i not in removes]
            for i, chord in enumerate(chords): 
                chords[i].gen_index = i
            return chords
    
    
    
# @profile
def generate_base_chords(layers):
    # try: 
    #     chords = pickle.load(open('python/pickles/save_' + str(layers-1) + '.p', 'rb'))
    # except: 
    #     chords = [Chord()]
    #     chords[0].construct_branches()
    #     save_json(chords, 0)
    #     pickle.dump(chords, open('python/pickles/save_' + str(layers)+'.p', 'wb'))
    chords = [Chord()]
    for layer in range(layers):
        next_layer = []
        for chord in chords:
            next_layer.extend(chord.grow_layer())
        chords = next_layer
        chords = remove_duplicates(chords)
        next_layer = []
        for i, chord in enumerate(chords):
            chord.construct_branches()
            chord.num = i
            chord.layer = layer + 1
            chord.get_rotation_shell()
        save_json(chords, layer + 1)
        pickle.dump(chords, open('python/pickles/save_' + str(layer+1)+'.p', 'wb'))
        
    assign_branch_num_id(chords)
    return chords



def save_diagrams(chords, path, name='chord', layer=3):
    for i, chord in enumerate(chords):
        fig = plt.figure(figsize=[2, 2])
        ax = fig.add_subplot(111, projection='3d')
        # XYZlim = [0, np.max(chord.unique_points)]
        # ax.set_xlim3d(XYZlim)
        # ax.set_ylim3d(XYZlim)
        # ax.set_zlim3d(XYZlim)
        ax.axis('off')

        ax.scatter(*chord.unique_points.T, color='lightsalmon', depthshade=False) 
        for dyad in chord.dyads:
            ax.plot(*np.array([dyad.origin, dyad.terminal]).T, color='lightsalmon')
        plt.tight_layout()
        plt.savefig(path + name + str(i)+'.svg', transparent=True)
        plt.close()

def save_all_diagrams(chords, layer):
    try:
        shutil.rmtree('src/assets/svgs/layer_'+str(layer))
    except OSError as e:
        pass
    base_path = dirname(dirname(abspath(__file__)))
    os.mkdir(base_path + '/src/assets/svgs/layer_' + str(layer))
    for c, chord in enumerate(chords):
        b_path = base_path + '/src/assets/svgs/layer_' + str(layer) + '/branches_' + str(c)
        if not os.path.isdir(b_path):
            os.mkdir(b_path)
        save_diagrams(chord.branches, base_path + '/src/assets/svgs/layer_' + str(layer) + '/branches_' + str(c), 'branch', layer)
    save_diagrams(chords, base_path + '/src/assets/svgs/chords'+str(layer), 'chord', layer)
    
    
def assign_branch_num_id(chords):
    branch_nums = [str(chord.branch_nums) for chord in chords]
    unique_branch_nums = list(set(branch_nums))
    indexes = [[i for i, x in enumerate(branch_nums) if x == id] for id in unique_branch_nums]
    for i, index_arr in enumerate(indexes):
        for index in index_arr:
            chords[index].branch_num_id = i

def write_sheet(chords, layer):
    gc = gspread.service_account(filename='keys/chord-analysis-5780b5bae94b.json')
    sheets = gc.open("chord-analysis")
    sheet = sheets.worksheet('layer_' + str(layer))
    
    titles = ['Points', 'Containments', 'Dimensions', 'Branches', 'Branch Sizes ID', 'Branch Size', 'Proportion', 'Overlap']
    titles_fmt = cellFormat(textFormat = textFormat(bold=True, fontSize=14))
    chord_fmt = cellFormat(backgroundColor=color(0.352, 0.768, 0.270))
    branch_fmt = cellFormat(backgroundColor=color(0.560, 0.262, 0.098), textFormat=textFormat(foregroundColor=color(1, 1, 1)))
    
    batch = batch_updater(sheets)
    batch.format_cell_range(sheet, '1', titles_fmt)
    sheet.update('B1', [titles])
    data = []
    row_ct = 2
    for c, chord in enumerate(chords):
        chord_text = ', '.join(['('+','.join([str(list(dyad.origin)), str(list(dyad.terminal))])+')' for dyad in chord.dyads])
        data_row = ['Chord ' + str(c), len(chord.unique_points), chord.containments, chord.dims, len(chord.branches), chord.branch_num_id, chord_text]
        data.append(data_row)
        batch.format_cell_range(sheet, 'A' + str(row_ct) + ':I' + str(row_ct), chord_fmt)
        row_ct += 1
        for branch in chord.branches:
            dyad_text = ', '.join(['('+','.join([str(list(dyad.origin)), str(list(dyad.terminal))])+')' for dyad in branch.dyads])
            data_row = ['', '', '', '', '', ''] + [len(branch.dyads), branch.proportion, branch.collective_overlap, dyad_text]
            data.append(data_row)
            batch.format_cell_range(sheet, 'G' + str(row_ct) + ':I' + str(row_ct), branch_fmt)
            row_ct += 1
    sheet.update('A' + str(2), data)
    batch.execute()

def save_json(chords, layer):
    with open('src/json/chords' + str(layer) + '.json', 'w') as outfile:    
        out = [chord.get_dict() for chord in chords]
        json.dump(out, outfile)

all_multiset_perms = {}    
layer = 5
if __name__ == "__main__":
    # import cProfile
    # pr = cProfile.Profile()
    # pr.enable()
    chords = generate_base_chords(layer)



# for layer in range(3, 3):
#     chords = generate_base_chords(layer-1)
#     pickle.dump(chords, open('python/pickles/save_' + str(layer)+'.p', 'wb'))
#     chords = pickle.load(open('python/pickles/save_' + str(layer)+'.p', 'rb'))
# 
#     save_json(chords)
#     save_all_diagrams(chords, layer)

# 
# chords = pickle.load(open('python/pickles/save_' + str(5)+'.p', 'rb'))
