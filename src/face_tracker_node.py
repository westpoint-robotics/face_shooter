#!/usr/bin/env python

import rospy
import cv2
from geometry_msgs.msg import Vector3
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from os.path import expanduser
home = expanduser("~")

img = Image()

# This callback updates a global variable only
def image_callback(ros_image):
    global img
    img = ros_image

if __name__ == '__main__':
    rospy.init_node("python_cam")
    image_sub = rospy.Subscriber("/usb_cam/image_raw", Image, image_callback)  
    pub = rospy.Publisher('/face_centroid', Vector3, queue_size=10)  
    
    # Load params if provided else use the defaults
    input_image_topic = rospy.get_param("input_image_topic","/usb_cam/image_raw")
    output_image_topic = rospy.get_param("output_image_topic","/face_detector/raw_image")
    haar_file_face = home + "/" + rospy.get_param("haar_file_face","catkin_ws/src/face_shooter/data/face.xml")
    face_tracking = rospy.get_param("face_tracking","1")
    display_original_image = rospy.get_param("display_original_image","1")
    display_tracking_image = rospy.get_param("display_tracking_image","1")
    
    # Create the classifier
    face_cascade=cv2.CascadeClassifier(haar_file_face)

    # Waiting here until first image appears
    rate = rospy.Rate(30) # 30hz
    while not rospy.is_shutdown(): 
        if img.encoding != '':
            break
        rate.sleep()

    # Process the images
    while not rospy.is_shutdown():
        #hello_str = "hello world %s" % rospy.get_time()
        #rospy.loginfo(hello_str)
        #try:
        # Use cv_bridge() to convert the ROS image to OpenCV format
        bridge = CvBridge()
        frame = bridge.imgmsg_to_cv2(img, "bgr8") 
        if (display_original_image): # Dispaly the image if param is set to true       
            cv2.imshow('original',frame)              
        # Gray scale image            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Use the classifier to find faces
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        center=Vector3() 
        for index,(x,y,w,h) in enumerate(faces): # For each face publish the centroid
            #print("Frame is: %d by %d and x,y %d, %d" %(frame.shape[1],frame.shape[0],x,y))
            frame = cv2.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2) # Draw a frame around each face
            # publish center of face
            center.x=x+w/2
            center.y=y+h/2
            center.z=index+1 # unique id for multiple faces, zero indexed
            pub.publish(center)
        if center.z == 0: # No faces found so aim at center
            center.x = 320 # This is the set Point TODO use a param
            pub.publish(center)
        if (display_tracking_image): # Dispaly the image if param is set to true
            cv2.imshow('tracking',frame)     
        #except Exception as e:
        #    print(e)
        
        cv2.waitKey(1) # Needed 
        rate.sleep()
    
    cv2.destroyAllWindows()
