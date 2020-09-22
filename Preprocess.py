from re import findall, sub
from pandas import DataFrame
from emoji import get_emoji_regexp
from string import punctuation
from tqdm.notebook import tqdm

class FeatureExtraction(object):
    """
    Kelas untuk mengecek beberapa feature dalam text yaitu URL, Hashtags, Tags, dan Emojis
    """
    def __init__(self):
        self.labels, self.encoding = [], {}   # Kelas label dan Encoding 
        self.features = {'urls' : [], 'hashtags' : [], 'tags' : [], 'emojis' : []}   # Feature
        self.patterns = {
            'urls' : ['http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),…]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URL Pattern
                      'www[.](?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),…]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
                      r'(?i)\b((?:http[s]?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.])(?:com|net|id|org|info|co)(?:[…/$-_@.&+!*=?]|[0-9a-zA-Z]|[0-9a-zA-Z])+)'],
            'hashtags' : [r'(?i)\#\w+'],  # Hashtag Pattern
            'tags' : [r'(?i)\@\w+'],   # Tags Pattern
            'emojis' : [get_emoji_regexp().pattern]  # Emojis Pattern
        }
    
    @staticmethod
    def search(arr, patterns, labels = None):
        """
        Fungsi Static untuk mencari feature berdasarkan patternya. Jika argument pattern diisi maka akan mengembalikan
        Dictionary dari feature berdasarkan kelasnya.

        params:
        arr     : List atau np.ndarray dari teks
        pattern : List pattern dari feature yang akan di cari
        labels  : List atau np.ndarray label dari teks [Optional]

        return:
        Dictionary dari features yang telah di extract dari texts
        """
        res = {}
        # Loop Through
        for i, text in enumerate(arr):
            temp, temp2 = [], []
            for pattern in patterns: # Loop Through
                features = findall(pattern, text) # Cari dari pattern
                temp += features  # simpan ke temp
            # Remove Duplicates
            for feature in temp:
                if temp2 == []:
                    temp2.append(feature)
                else:
                    if all([feature not in x for x in temp2]):
                        temp2.append(feature)
            # Jika labels tidak diisi
            if labels is None:
                for feature in temp2:
                    if feature in res: res[feature] += 1
                    else: res[feature] = 1
            # Jika labels diisi
            else:
                for feature in temp2:
                    if feature in res: 
                        res[feature][labels[i]] += 1
                    else: 
                        res[feature] = {x : 0 for x in sorted(set(labels))}
                        res[feature][labels[i]] += 1
        return res
    
    def get_table(self, feature, return_prop = False):
        """
        Membuat table dari features

        params:
        feature     : Feature mana yang akan dilakukan tabulasi ['urls', 'hashtags', 'tags', 'emojis']
        return_prop : Akan mengembalikan proporsi feature dari masing" kelas jika True [Auto = False]
                      Jika ingin mengaktifkan feature ini perlu melakukan fitting dengan label.
        return:
        DataFrame dari Feature
        """
        keys = list(self.features[feature].keys())  # Content data
        values = list(self.features[feature].values()) # Frekuensi data
        if self.labels == []: # Jika fitting tanpa labels
            return (DataFrame({feature : keys, 'frekuensi' : values})
                    .sort_values(by=['frekuensi'], ascending = False).reset_index(drop = True))
        else:
            data = DataFrame({feature : keys}) # Init df
            for label in self.labels: # Loop through
                data[label] = [x[label] for x in values]  # Membuat kolom frekuensi tiap kelasnya
            if return_prop:  # Jika return_prop True
                data['frekuensi'] = data[self.labels].sum(axis = 1).values # Frekuensi total per contentnya
                for label in self.labels:
                    data[label] /= data['frekuensi'] # Membagi Frek dengan Frek total untuk proporsi
                data['max_prop'] = data[self.labels].max(axis = 1).values # Mencari proporsi terbesar 
                return (data.sort_values(by=['frekuensi', 'max_prop'], ascending = False) # Sort dari prop terbesar
                        .reset_index(drop = True))
            return data
    
    def fit(self, arr, label = None, search = 'all', return_dict = False):
        """
        Fitting terhadap data text. Proses fitting menggunakan label wajib dilakukan jika ingin menggunakan
        keseluruhan fugsi dari kelas ini.

        params:
        arr         : List atau np.ndarray dari texts data
        label       : List atau np.ndarray dari kelas pada texts data jika diisi
        search      : List dari feature yang akan dilakukan fitting ['urls', 'hashtags', 'tags', 'emojis'] Auto : 'all'
                      Jika 'all' maka akan mencari semua feature yang disediakan
        return_dict : Mengembalikan dalam bentuk dict

        return:
        Dictionary jika return_dict == True
        """
        if search == 'all': # Jika search == 'all'
            search = list(self.features.keys())
        if label is not None:
            self.labels = list(sorted(set(label))) # Mendapatkan kelas
        for feature in search: # Search per-Featurenya
            self.features[feature] = self.search(arr, self.patterns[feature], label)
        if return_dict: # return_dict
            return self.features
        
    def build_mask_code(self, min_prop, features = 'all'):
        """
        Building Mask code dari Feature yang telah di extract.

        params:
        min_prop    : Minimal proporsi dari tiap content yang akan di gunakan(di masking)
        features    : List dari feature
        """
        if self.labels == [] : raise NotImplementedError("Must fit with labels")
        if features == 'all':
            features = list(self.features.keys())
        for feature in features:
            self.encoding[feature] = {}
            data = self.get_table(feature, return_prop = True)
            include = sorted(data[feature][data['max_prop'] >= min_prop].tolist(), key = lambda x : len(x),  reverse=True)
            exclude = data[feature][data['max_prop'] < min_prop].values
            for i, words in enumerate(include):
                self.encoding[feature][words] = f'mask{feature}{i}mask'.upper()
            for i, words in enumerate(exclude):
                self.encoding[feature][words] = ''
        
    def encode(self, array, features = 'all'):
        """
        Encoding data texts dari mask_code yang telah di buat
        """
        if self.encoding == {} : raise NotImplementedError("Must build mask code first")
        if features == 'all':
            features = list(self.features.keys())
        arr = array.copy()
        for feature in features:
            for i in range(len(arr)):
                for word in self.encoding[feature]:
                    arr[i] = arr[i].replace(word, f' {self.encoding[feature][word]} ')
                arr[i] = ' '.join(arr[i].split())
        return arr
    
    def decode(self, array):
        """
        Decoding data texts yang berisi mask_code kembali
        """
        if self.encoding == {} : raise NotImplementedError("Must build mask code first")
        features = list(self.features.keys())
        arr = array.copy()
        for feature in features:
            for i in range(len(arr)):
                for word in self.encoding[feature]:
                    if self.encoding[feature][word] != '':
                        arr[i] = arr[i].replace(self.encoding[feature][word], f' {word} ')
                arr[i] = ' '.join(arr[i].split())
        return arr

class SpellChecker(object):
    """
    Mengecek dan memperbaiki misspelling words / kata - kata yang typo pada kalimat -
    kalimat yang ada.
    """
    def __init__(self):
        self.words = {}    # Words
        
    def fit(self, direc:str):
        """
        Fitting untuk mendapatkan vocab yang salah dan vocab yang benar dari file txt

        param:
        direc   : Direktori file txt yang berisi vocab
        """
        f = open(direc, "r")
        for w in f.readlines():
            if len(w.split()) == 2:
                missed, true = w.split()
                if '_' in true:
                    true = ' '.join(true.split('_'))
                self.words[missed] = true
        f.close()
        
    def transform(self, arr):
        """
        Mengganti kata - kata yang misspell berdasarkan vocab.

        params:
        arr     : List / Numpy array yang berisi kalimat - kalimat yang akan dibenarkan.
        """
        for i in tqdm(range(len(arr))):
            temp = arr[i].split()
            for j in range(len(temp)):
                if temp[j] in self.words.keys():
                    temp[j] = self.words[temp[j]]
            arr[i] = ' '.join(temp)
        return arr