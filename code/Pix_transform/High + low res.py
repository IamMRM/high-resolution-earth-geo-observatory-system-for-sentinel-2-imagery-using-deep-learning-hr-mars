#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import os
os.environ["OMP_PROC_BIND"] = os.environ.get("OMP_PROC_BIND", "true")
import numpy as np
from pix_transform.pix_transform import PixTransform
import scipy.interpolate
#new
import matplotlib.pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
from PIL import Image
#newer
from baselines.baselines import bicubic
from utils.plots import plot_result


# In[ ]:


data_dir = '../SEN12MS/processed/'
validation_states = ['ROIs13_high_roshan_s2']


# In[ ]:


validation_patches=[]
for state in validation_states:
    fn= os.path.join(data_dir,'%s_val_patches/' %state)
    #print(fn)
    with os.scandir(fn) as entries:
        for entry in entries:
            #print(entry.name)
            with os.scandir(fn+entry.name) as folders:
                for folder in folders:
                    #print(folder.name)
                    with os.scandir(fn+entry.name+'/'+folder.name) as files:
                        for file in files:
                            #print(file.name)
                            validation_patches.append((os.path.join(fn+entry.name+'/'+folder.name+'/',file.name),state))


# In[ ]:


print(validation_patches[0][0])
dataset = np.load(validation_patches[0][0])
print(dataset.shape)


# In[ ]:


target_imgs=np.zeros(shape=(len(validation_patches),256,256))
targethigh_imgs=np.zeros(shape=(len(validation_patches),256,256))
guide_imgs =np.zeros(shape=(len(validation_patches),3,256,256))
for i,(fn,state) in enumerate(validation_patches):
    dataset = np.load(fn)
    guide_imgs[i]=dataset[:,:,0:3].reshape(3,256,256)
    target_imgs[i]=dataset[:,:,4].squeeze()
    targethigh_imgs[i]=dataset[:,:,5].squeeze()
#print(len(validation_patches))


# In[ ]:


####  define parameters  ########################################################
params = {'img_idxs' : [], # idx images to process, if empty then all of them
            
          'scaling': 8,
          'greyscale': False, # Turn image into grey-scale
          'channels': -1,
          
          'spatial_features_input': True,
          'weights_regularizer': [0.0001, 0.001, 0.0001], # spatial color head
          'loss': 'l1',
 
          'optim': 'adam',
          'lr': 0.001,
                  
          'batch_size': 32,
          'iteration': 1024*32*32//32,
                  
          'logstep': 64,
          
          'final_TGV' : False, # Total Generalized Variation in post-processing
          'align': False, # Move image around for evaluation in case guide image and target image are not perfectly aligned
          'delta_PBP': 1, # Delta for percentage of bad pixels 
         }


# In[ ]:


def normalize(array):
    array_min, array_max = array.min(), array.max()
    return ((array - array_min) / (array_max - array_min))


# In[ ]:


a = guide_imgs[0]
b = normalize(a)
plt.imshow(b.reshape(256,256,3))
plt.show()


# In[ ]:


for n_image,idx in enumerate(range(0,target_imgs.shape[0])):
    print("####### image {}/{} - image idx {} ########".format(n_image+1,(target_imgs.shape[0]),idx))
    
    guide_imgg = guide_imgs[idx].copy()#3x256x256
    guide_img=normalize(guide_imgg)
    
    #low res source image
    source_img = target_imgs[idx].copy()#256x256  
    source_img[source_img == 1] = 0#forest
    source_img[source_img == 2] = 0
    source_img[source_img == 3] = 0
    source_img[source_img == 4] = 0
    source_img[source_img == 5] = 0
    source_img[source_img == 6] = 1#shrublands
    source_img[source_img == 7] = 1
    source_img[source_img == 8] = np.random.choice(np.arange(0, 8), p=[0.1, 0.15, 0.1, 0, 0, 0.15, 0.5, 0])#savannas
    source_img[source_img == 9] = np.random.choice(np.arange(0, 8), p=[0.1, 0.15, 0.1, 0, 0, 0.15, 0.5, 0])
    source_img[source_img == 10] = 2#grassland
    source_img[source_img == 11] = 3#wetlands
    source_img[source_img == 12] = 4#croplands
    source_img[source_img == 13] = 5#builtup to impervious
    source_img[source_img == 14] = 4#cropland
    source_img[source_img == 15] = 7#ice
    source_img[source_img == 16] = 6#barren
    source_img[source_img == 17] = 7#water
    
    #high res target image
    target_img = targethigh_imgs[idx].copy()
    target_img[target_img==1]=0
    target_img[target_img==2]=1
    target_img[target_img==4]=2
    target_img[target_img==5]=3
    target_img[target_img==6]=4
    target_img[target_img==7]=5
    target_img[target_img==9]=6
    target_img[target_img==10]=7

    #source_img = downsample(target_img,params['scaling'])
    
    bicubic_target_img = bicubic(source_img=source_img, scaling_factor=params['scaling'])
    
    predicted_target_img = PixTransform(guide_img=guide_img,source_img=source_img,params=params,target_img=target_img).round()
    predicted_target_img[predicted_target_img > 7.0] = 7
    
    f, ax = plot_result(guide_img,source_img,predicted_target_img,bicubic_target_img,target_img)
    plt.show()
    
    if target_img is not None:
        # compute metrics and plot results
        MSE = np.mean((predicted_target_img - target_img) ** 2)
        MAE = np.mean(np.abs(predicted_target_img - target_img))
        PBP = np.mean(np.abs(predicted_target_img - target_img) > params["delta_PBP"])

        print("MSE: {:.3f}  ---  MAE: {:.3f}  ---  PBP: {:.3f}".format(MSE,MAE,PBP))
        print("\n\n")


# In[ ]:




