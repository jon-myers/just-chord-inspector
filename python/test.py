import pickle

chords = pickle.load(open('python/pickles/save_' + str(5)+'.p', 'rb'))
print(len(chords))
