import cv2
import sys
import time

# video file reading
src="../../videos/test_baofeng.mp4"
# encode_param=[int(cv2.IMWRITE_JPEG_QUALITY), 100]

# stream = cv2.VideoCapture(src)

# (grabbed, frame_raw) = stream.read()
# print(frame_raw.shape)
# print('编码之前一张图片的大小： {} MB'.format(sys.getsizeof(frame_raw)/1048576))


# result, imgencode = cv2.imencode('.jpg', frame_raw, encode_param)
# print('编码之后一张图片的大小： {} MB'.format(sys.getsizeof(imgencode)/1048576))

# print(cv2.IMREAD_COLOR)



# camera 
stream = cv2.VideoCapture(0)
stream.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # float
stream.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # float

for i in range(10000):
	ret, frame = stream.read()
	cv2.imshow('img', frame)
	if(cv2.waitKey(1) & 0xFF==ord('q')):
		break
