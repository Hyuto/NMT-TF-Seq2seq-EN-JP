import os
import tensorflow as tf
import numpy as np
from tqdm.notebook import tqdm

def ApplyAUG(df, PATH, LP, data_aug, up_sample_ratio = 0.2,
            up_sample_class = None):
    """
    Fungsi untuk mengaplikasikan Preprocess dan Augmentation ke dalam data gambar untuk disimpan
    kedalam direktori/file yang baru.

    Params
    df              : Dataframe yang menyimpan nama file pada kolom 'nama file gambar' dan label pada kolom
                     'label'
    PATH            : Direktori data gambar
    LP              : Load & Preprocess image function
    data_aug        : Augmentation function
    up_sample_ratio : Rasio up sampling yang dikehendaki.
    up_sample_class : Spesifikasi kelas yang akan dilakukan Augmentasi. Jika ini di isi maka n_AUG
                      akan dihitung secara otomatis tergantung up_sample_ratio.

    Return
    List item pada direktori baru dan Labelnya.
    """

    def __up_sampling(up_sample_ratio, N) -> list:      
        if up_sample_ratio >= 1:
            n_AUG = [up_sample_ratio] * N
        else:
            n_sample = int(N * up_sample_ratio)
            n_AUG = [1] * n_sample + [0] * (N - n_sample)
        return n_AUG

    if up_sample_class != None:
        print(f'[INFO] Up Sampling Kelas {up_sample_class} Sebesar {up_sample_ratio * 100}%')
    else:
        print(f'[INFO] Up Sampling Setiap Kelas Sebesar {up_sample_ratio * 100}%')
    
    DIR = './Prep Data + AUG'
    os.makedirs(DIR)
    X, Y = [], []
    for i in range(2):
        print(f'[INFO] Memproses Kelas {i}..')
        CHILD_DIR = os.path.join(DIR, f'{i}')
        os.makedirs(CHILD_DIR)
        data = df['nama file gambar'][df.label.values == i].values
        if up_sample_class != None:
            if str(i) == up_sample_class:
                n_AUG = __up_sampling(up_sample_ratio, len(data))
            else:
                n_AUG = [0] * len(data)
        else:
            n_AUG = __up_sampling(up_sample_ratio, len(data))
        for k, file in enumerate(tqdm(data)):
            IMAGE_DIR = os.path.join(CHILD_DIR, f'{file[:-4]}.png')
            img = LP(PATH + file)
            tf.keras.preprocessing.image.save_img(IMAGE_DIR, img)
            X.append(IMAGE_DIR); Y.append(i)
            for j in range(n_AUG[k]):
                AUG_DIR = os.path.join(CHILD_DIR, f'AUG {j + 1}_{file[:-4]}.png')
                aug = data_aug(np.expand_dims(img, 0))
                tf.keras.preprocessing.image.save_img(AUG_DIR, aug[0])
                X.append(AUG_DIR); Y.append(i)
        print(f'[INFO] Selesai Memproses Kelas {i}')
        print('[INFO] ' + f'Banyak Data Kelas {i} setelah proses sebanyak {len(os.listdir(CHILD_DIR))} gambar\n'.title())
    print(f'[INFO] Saved to {DIR}')
    print('[INFO] Done :)')
    return X, Y