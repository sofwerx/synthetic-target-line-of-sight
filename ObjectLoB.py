####################### Summary################################
#
# Overview
# ------------------------------------------------------------
# Function to identify person line of bearing from the device in an
# image. The person object is identified by highest object person confidence.
# Google states SSD:(Single Shot MultiBox Detector) is a little better Yolo and 
# faster than Yolo
# 
# Model 
#-----------------------------------------------------0--------
# SSD:(Single Shot MultiBox Detector)
#
# Pros
# - Fast
# - Robust to different resolutions and aspect ratios 
# - Easy to train
# Cons
# - Less Accuracy
# - Difficult to classify categories that a similar like animals
# 
# Input
# -----------------------------------------------------------
# image = image location( test only with jpg format)
# fov = field of view of camera
# coh = compass heading
#
# Output
# -----------------------------------------------------------
# AOB - person of highest confidence angle of bearing
#
################################################################



#image = '/root/models/research/object_detection/test_images/image1.jpg'


# for image_path in TEST_IMAGE_PATHS:

# # Imports
import numpy as np
import os
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import zipfile
import pandas as  pd
import math

from collections import defaultdict
from io import StringIO
from matplotlib import pyplot as plt
from PIL import Image
from io import BytesIO
import cStringIO

import json
import base64

import logging

logger = logging.getLogger("django")

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from object_detection.protos import string_int_label_map_pb2

class PersonLoB:

    # ## Env setup

    # In[ ]:

    # What model to download.
    MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
    MODEL_FILE = MODEL_NAME + '.tar.gz'
    DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join( os.environ["TENSORFLOW_MODELS"],'research','object_detection','data','mscoco_label_map.pbtxt')

    NUM_CLASSES = 90

    # ## Download Model

    # In[ ]:
    if not os.path.isdir(MODEL_NAME):
      logger.info("The model directory %s does not yet exist", MODEL_NAME)
      if not os.path.isfile(MODEL_FILE) :
        logger.info("The model file %s does not yet exist", MODEL_FILE)
        opener = urllib.request.URLopener()
        opener.retrieve(DOWNLOAD_BASE + MODEL_FILE, MODEL_FILE)
      logger.info("The model file %s has been downloaded", MODEL_FILE)
      tar_file = tarfile.open(MODEL_FILE)
      for file in tar_file.getmembers():
        file_name = os.path.basename(file.name)
        if 'frozen_inference_graph.pb' in file_name:
          tar_file.extract(file, os.getcwd())
          logger.info("The model %s has been extracted", file)

    # ## Load a (frozen) Tensorflow model into memory.

    # In[ ]:
    logger.info("tf.Graph()")
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        logger.info("tf.GraphDef()")
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            logger.info("serialized_graph")
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

    # ## Loading label map
    # Label maps map indices to category names, so that when our convolution network predicts `5`, we know that this corresponds to `airplane`.  Here we use internal utility functions, but anything that returns a dictionary mapping integers to appropriate string labels would be fine

    # In[ ]:
    logger.info("Loading label maps")
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                                use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    logger.info("PersonLoB class ready")

    # In[ ]:
    def lob(self, ins): # inputData is image, fov, compass hdg

        fov = ins['fov']
        ch = ins['compass']
        #image = str(ins['image'].split(",")[1].decode('base64'))
        #image = Image.open(BytesIO(ins['image'].split(",")[1].decode('base64'))) 
        image_string = cStringIO.StringIO(ins['image'].split(",")[1].decode('base64'))
        image = Image.open(image_string)

        # Allocate GPU memory
        logger.info("Initializing TensorFlow")
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = True
        logger.info("Creating Tensorflow session")
        session = tf.Session(config=config)
        logger.info("Tensorflow session created")
    
        # This is needed to display the images.
        # get_ipython().magic(u'matplotlib inline')
    
        # This is needed since the notebook is stored in the object_detection folder.
#        sys.path.append("..")
    
        # ## Object detection imports
        # Here are the imports from the object detection module.
    
        # In[ ]:
    
        # # Model preparation
    
        # ## Variables
        #
        # Any model exported using the `export_inference_graph.py` tool can be loaded here simply by changing `PATH_TO_CKPT` to point to a new .pb file.
        #
        # By default we use an "SSD with Mobilenet" model here. See the [detection model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) for a list of other models that can be run out-of-the-box with varying speeds and accuracies.
    
        # ## Helper code
    
        # In[ ]:
    
        def load_image_into_numpy_array(image):
            logger.info("Loading image into numpy array")
            (im_width, im_height) = image.size
            return np.array(image.getdata()).reshape(
                (im_height, im_width, 3)).astype(np.uint8)
    
        # # Detection
    
        # Size, in inches, of the output images.
        IMAGE_SIZE = (12, 8)
    
        # In[ ]:
    
        # Apply algorithm to images
    
        with self.__class__.detection_graph.as_default():
            logger.info("Applying algorithm to images")
            with tf.Session(graph=self.__class__.detection_graph) as sess:
                logger.info("Opened TensorFlow detection_graph session")
                # Definite input and output Tensors for detection_graph
                image_tensor = self.__class__.detection_graph.get_tensor_by_name('image_tensor:0')
                # Each box represents a part of the image where a particular object was detected.
                detection_boxes = self.__class__.detection_graph.get_tensor_by_name('detection_boxes:0')
                # Each score represent how level of confidence for each of the objects.
                # Score is shown on the result image, together with the class label.
                detection_scores = self.__class__.detection_graph.get_tensor_by_name('detection_scores:0')
                detection_classes = self.__class__.detection_graph.get_tensor_by_name('detection_classes:0')
                num_detections = self.__class__.detection_graph.get_tensor_by_name('num_detections:0')
                # Open Image and get height and width for angle of object
                #image = Image.open(image)
                width, height = image.size
                logger.info("Loading image of size %d by %d",width,height)

                # the array based representation of the image will be used later in order to prepare the
                # result image with boxes and labels on it.
                image_np = load_image_into_numpy_array(image)
                # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
                image_np_expanded = np.expand_dims(image_np, axis=0)
                # Actual detection.
                (boxes, scores, classes, num) = sess.run(
                    [detection_boxes, detection_scores, detection_classes, num_detections],
                    feed_dict={image_tensor: image_np_expanded})
                # Visualization of the results of a detection.
                # vis_util.visualize_boxes_and_labels_on_image_array(
                # image_np,
                # np.squeeze(boxes),
                # np.squeeze(classes).astype(np.int32),
                # np.squeeze(scores),
                # category_index,
                # use_normalized_coordinates=True,
                # line_thickness=8)
                # plt.figure(figsize=IMAGE_SIZE)
                # plt.imshow(image_np)
    
        # Angle of view, image height, image width, image height center pixel, image width center pixel,
        # and pixel degree,
        fov = fov
        imageHeight = height
        imageWidth = width
        imageHeightCenter = imageHeight / 2
        imageWidthCenter = imageWidth / 2
        pixelDegree = float(fov) / imageWidth
    
        # Convert tensorflow data to pandas data frams
        df = pd.DataFrame(boxes.reshape(100, 4), columns=['y_min', 'x_min', 'y_max', 'x_max'])
        df1 = pd.DataFrame(classes.reshape(100, 1), columns=['classes'])
        df2 = pd.DataFrame(scores.reshape(100, 1), columns=['scores'])
        df5 = pd.concat([df, df1, df2], axis=1)
    
        # Transform box bound coordinates to pixel coordintate
        df5['y_min_t'] = df5['y_min'].apply(lambda x: x * imageHeight)
        df5['x_min_t'] = df5['x_min'].apply(lambda x: x * imageWidth)
        df5['y_max_t'] = df5['y_max'].apply(lambda x: x * imageHeight)
        df5['x_max_t'] = df5['x_max'].apply(lambda x: x * imageWidth)
        
        # Create objects pixel location
        
        # Create objects pixel location x and y
        # X
        df5['ob_wid_x'] = df5['x_max_t'] - df5["x_min_t"]
        df5['ob_mid_x'] = df5['ob_wid_x'] / 2
        df5['x_loc'] = df5["x_min_t"] + df5['ob_mid_x']
        # Y
        df5['ob_hgt_y'] = df5['y_max_t'] - df5["y_min_t"]
        df5['ob_mid_y'] = df5['ob_hgt_y'] / 2
        df5['y_loc'] = df5["y_min_t"] + df5['ob_mid_y']

    
        # Find object degree of angle, data is sorted by score, select person with highest score
        df5['object_angle'] = df5['x_loc'].apply(lambda x: -(imageWidthCenter - x) * pixelDegree)
        df6 = df5.loc[df5['classes'] == 1]
        df7 = df6.iloc[0]['object_angle']
        AOB = df7 + ch
    
        # Print AOB
        #print AOB
    
        resp = {
          "aob": AOB
        }

        return resp
    
    #objectAOB(image, 122, 180)
    
    # In[ ]:





