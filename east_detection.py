#help of chatgpt was partially used for the generation of this example

import cv2
import numpy as np
from imutils.object_detection import non_max_suppression
import pytesseract

def decode_predictions(scores, geometry):
	# grab the number of rows and columns from the scores volume, then
	# initialize our set of bounding box rectangles and corresponding
	# confidence scores
	(numRows, numCols) = scores.shape[2:4]
	rects = []
	confidences = []

	# loop over the number of rows
	for y in range(0, numRows):
		# extract the scores (probabilities), followed by the
		# geometrical data used to derive potential bounding box
		# coordinates that surround text
		scoresData = scores[0, 0, y]
		xData0 = geometry[0, 0, y]
		xData1 = geometry[0, 1, y]
		xData2 = geometry[0, 2, y]
		xData3 = geometry[0, 3, y]
		anglesData = geometry[0, 4, y]

		# loop over the number of columns
		for x in range(0, numCols):
			# if our score does not have sufficient probability,
			# ignore it
			if scoresData[x] < 0.5:#(min_confidence == 0.2)
				continue

			# compute the offset factor as our resulting feature
			# maps will be 4x smaller than the input image
			(offsetX, offsetY) = (x * 4.0, y * 4.0)

			# extract the rotation angle for the prediction and
			# then compute the sin and cosine
			angle = anglesData[x]
			cos = np.cos(angle)
			sin = np.sin(angle)

			# use the geometry volume to derive the width and height
			# of the bounding box
			h = xData0[x] + xData2[x]
			w = xData1[x] + xData3[x]

			# compute both the starting and ending (x, y)-coordinates
			# for the text prediction bounding box
			endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
			endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
			startX = int(endX - w)
			startY = int(endY - h)

			# add the bounding box coordinates and probability score
			# to our respective lists
			rects.append((startX, startY, endX, endY))
			confidences.append(scoresData[x])

	# return a tuple of the bounding boxes and associated confidences
	return (rects, confidences)

# Load pre-trained EAST text detector model
#https://github.com/oyyd/frozen_east_text_detection.pb/blob/master/frozen_east_text_detection.pb
net = cv2.dnn.readNet("./frozen_east_text_detection.pb")

# Load the input image and grab the image dimensions
image = cv2.imread("test_slide.png")
orig = image.copy()
(H, W) = image.shape[:2]

# set the new width and height
(newW, newH) = (320, 320)

# calculate the ratio of the old dimensions
# compared to the new dimensions
rW = W / float(newW)
rH = H / float(newH)

# resize the image and grab the new dimensions
image = cv2.resize(image, (newW, newH))
(H, W) = image.shape[:2]

# construct a blob from the image
blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
    (123.68, 116.78, 103.94), swapRB=True, crop=False)

# pass the blob through the network and obtain the detections and predictions
net.setInput(blob)
(scores, geometry) = net.forward(["feature_fusion/Conv_7/Sigmoid", "feature_fusion/concat_3"])

# decode the predictions, then  apply non-maxima suppression to suppress weak, overlapping bounding boxes
rects, confidences = decode_predictions(scores, geometry)
boxes = non_max_suppression(np.array(rects), probs=confidences)

# loop over the bounding boxes
for (startX, startY, endX, endY) in boxes:
    # scale the bounding box coordinates based on the respective ratios
    startX = int(startX * rW)
    startY = int(startY * rH)
    endX = int(endX * rW)
    endY = int(endY * rH)

    # draw the bounding box on the image
    cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)

    # use PyTesseract to perform OCR on the cropped region
    if(startY < 0):
        startY = 0
    roi = orig[startY:endY, startX:endX]
    print(f"{startY},{endY} : {startX},{endX}")
    text = pytesseract.image_to_string(roi)
    print(text)


# show the output image
cv2.imshow("Text Detection", orig)
cv2.waitKey(0)