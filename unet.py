# -*- coding: utf-8 -*-
"""unet.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1S5MyYwGgO3_eKKlc1SfPrv7aBabWql4k
"""

import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
import os
import numpy as np

def resizeImages(input_image, height, width):
    input_image = tf.image.resize(input_image, [height, width],
                                method=tf.image.ResizeMethod.NEAREST_NEIGHBOR)
    return input_image

def normalize(input_image):
    input_image = (input_image / 127.5) - 1

    return input_image

def normalize_simple(input_image):
    input_image = (input_image - np.amin(input_image))/(np.amax(input_image)-np.amin(input_image))

    return input_image

## downsampling block

def downsample(filters, kernel_size=3, batch_norm=True):
    initializer = tf.random_normal_initializer(0., 0.02)
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same', 
                                    kernel_initializer=initializer))    
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same', 
                                    kernel_initializer=initializer))
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
        
    return model

## upsampling block

def upsample(filters, kernel_size=3, batch_norm=True, drop_out=True):
    initializer = tf.random_normal_initializer(0., 0.02)
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same', 
                                    kernel_initializer=initializer))
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    if drop_out:
        model.add(tf.keras.layers.Dropout(0.3))
        
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same', 
                                    kernel_initializer=initializer))
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    if drop_out:
        model.add(tf.keras.layers.Dropout(0.3))
    model.add(tf.keras.layers.Conv2DTranspose(filters,3, strides = 2, padding='same'))    
    
    return model

#bottleneck

def bottom(filters, kernel_size=3, batch_norm=True, drop_out=True):
    initializer = tf.random_normal_initializer(0., 0.02)
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same', 
                                   kernel_initializer=initializer))
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    if drop_out:
        model.add(tf.keras.layers.Dropout(0.3))
        
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same', 
                                    kernel_initializer=initializer))
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    if drop_out:
        model.add(tf.keras.layers.Dropout(0.3))
        
    return model

#final block with softmax activation function

def final_layer(filters_out, filters, kernel_size, batch_norm=True, drop_out=True):
    initializer = tf.random_normal_initializer(0., 0.02)
    model = tf.keras.Sequential()
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same',
                                    kernel_initializer=initializer))
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    if drop_out:
        model.add(tf.keras.layers.Dropout(0.3))
    
    model.add(tf.keras.layers.Conv2D(filters, kernel_size, padding='same',
                                    kernel_initializer=initializer))
    
    model.add(tf.keras.layers.ReLU())
    if batch_norm:
        model.add(tf.keras.layers.BatchNormalization())
    if drop_out:
        model.add(tf.keras.layers.Dropout(0.3))
    
    model.add(tf.keras.layers.Conv2D(filters_out, kernel_size, padding='same',
                                    kernel_initializer=initializer))
    model.add(tf.keras.layers.Softmax())
    
    return model

class UNET(tf.keras.Model):
    def __init__(self, classes):
        super(UNET, self).__init__()
        self.classes = classes
        self.down1= downsample(64, 3)
        
        self.m1 = tf.keras.layers.MaxPooling2D(pool_size = (2, 2))
        self.down2 = downsample(128, 3)
        
        self.m2 = tf.keras.layers.MaxPooling2D(pool_size = (2, 2))
        self.down3 = downsample(256, 3)
        
        self.m3 = tf.keras.layers.MaxPooling2D(pool_size = (2, 2))
        self.down4 = downsample(512, 3)
        
        self.m4 = tf.keras.layers.MaxPooling2D(pool_size = (2, 2))
        self.bottom = bottom(1024, 3)
        self.u1 = tf.keras.layers.Conv2DTranspose(512,3, strides = 2, padding='same')
        self.up1 = upsample(512, 3)
        self.up2 = upsample(256, 3)
        self.up3 = upsample(128, 3)
        self.final_layer = final_layer(self.classes, 64, 3)
        
    def call_model(self):
        inputs = tf.keras.layers.Input(shape = [128, 128, 3])
        x = inputs
        print('input', x.shape)
        x = self.down1(x)
        c1 = x
        print('c1', x.shape)
        
        x = self.m1(x)
        x = self.down2(x)
        c2 = x
        print('c2', x.shape)
        
        x = self.m2(x)
        x = self.down3(x)
        c3 = x
        print('c3', x.shape)
        
        x = self.m3(x)
        x = self.down4(x)
        c4 = x
        print('c4', x.shape)
        x = self.m4(x)
        
        x = self.bottom(x)
        print('bottom', x.shape)

        x = self.u1(x)
        print('u1', x.shape)

        x = self.up1(tf.keras.layers.concatenate([x, c4], axis=3))
        print('up1', x.shape)

        x = self.up2(tf.keras.layers.concatenate([x, c3], axis=3))
        print('up2', x.shape)

        x = self.up3(tf.keras.layers.concatenate([x, c2], axis=3))
        print('up3', x.shape)

        x = self.final_layer(tf.keras.layers.concatenate([x, c1], axis=3))
        print('up4', x.shape)
        
        return tf.keras.Model(inputs=inputs, outputs=x)

classes = 4
model = UNET(classes).call_model()
print(type(model))
#model = unet()
model.compile(optimizer='rmsprop',
              loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
              metrics=['accuracy'])
model.summary()

!curl -O http://www.robots.ox.ac.uk/~vgg/data/pets/data/images.tar.gz
!curl -O http://www.robots.ox.ac.uk/~vgg/data/pets/data/annotations.tar.gz
!tar -xf images.tar.gz
!tar -xf annotations.tar.gz

train_input_path = r"/content/images"
train_label_path = r"/content/annotations/trimaps"

from keras.preprocessing import image
height = 128
width = 128
def collectImages(path):
    input_images = []
    i = 1
    for fname in sorted(os.listdir(path)):
      if fname[-4:] == ".jpg":
        print(fname)
        img = image.load_img(os.path.join(path, fname), target_size=(128, 128))
        input_image = image.img_to_array(img)
        input_image = normalize_simple(input_image)
        input_images.append(input_image)
        print("added", i, "entry")
        i = i+1
    print("added all")
    return input_images

input_images = collectImages(train_input_path)

def collectImages(path):
    input_images = []
    i = 1
    for fname in sorted(os.listdir(path)):
      if fname[-4:] == ".png" and not fname.startswith("."):
        print(fname)
        img = image.load_img(os.path.join(path, fname), target_size=(128, 128))
        input_image = image.img_to_array(img)
        input_images.append(input_image)
        print("added", i, "entry")
        i = i+1
    print("added all")
    return input_images

target_images = collectImages(train_label_path)

inputs = np.stack(input_images)
targets = np.stack(target_images)

test_input = inputs[7090:]
test_target = targets[7090:, :, :, 0:1]
train_input = inputs[:6090]
train_target = targets[:6090,  :, :, 0:1]
val_input = inputs[6090:7090]
val_target = targets[6090:7090,  :, :, 0:1]

print(test_input.shape, test_target.shape)
print(train_input.shape, train_target.shape)
print(val_input.shape, val_target.shape)

## randomly picking up the sample from training set
## and displaying input as well as its corresponding groundtruth image

index = random.randint(0,train_input.shape[0]-1)
plt.figure(1)
plt.imshow(train_input[index])
plt.figure(2)
plt.imshow(train_target[index][:, :, 0])

def mask_image(input_mask):
  input_mask = tf.argmax(input_mask, axis=-1)
  input_mask = input_mask[..., tf.newaxis]
  return input_mask[0]

model.fit(train_input, train_target, epochs = 30, batch_size= 25, verbose=1, validation_data=(val_input, val_target), shuffle=True)

## randomly picking up the sample from test set
## and displaying input as well as its corresponding groundtruth image

index = random.randint(0,test_input.shape[0]-1)
plt.figure(1)
plt.imshow(test_input[index])
plt.figure(2)
plt.imshow(test_target[index][:, :, 0])

from google.colab import drive
drive.mount('/content/drive')

import random
def display_predictions(path):
  sample = image.load_img(path=path, target_size=(128, 128))
  sample = image.img_to_array(sample)
  sampled_image = sample[tf.newaxis, ...]
  sampled_image = normalize_simple(sampled_image)
  sampled_image.shape

  pred = model.predict(sampled_image)
  pred = mask_image(pred)
  pred.shape

  plt.figure(random.randint(0,100))
  plt.subplot(121)
  plt.title("Predicted Image")
  plt.imshow(pred[:, :, 0])
  plt.subplot(122)
  plt.title("Input Image")
  plt.imshow(sampled_image[0])

## Upload images from anywhere into the
## drive and run the model

display_predictions("/content/drive/My Drive/download_4.jpeg")
display_predictions("/content/drive/My Drive/download_3.jpeg")
display_predictions("/content/drive/My Drive/download_2.jpeg")
display_predictions("/content/drive/My Drive/download_1.jpeg")

