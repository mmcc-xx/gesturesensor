import numpy as np
import tensorflow as tf
import cv2 as cv
import mediapipe as mp
import csv
import copy
import itertools
import config

max_value = None


def normalize_(n):
    return n / max_value


def _calc_bounding_rect(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_array = np.empty((0, 2), int)

    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)

        landmark_point = [np.array((landmark_x, landmark_y))]

        landmark_array = np.append(landmark_array, landmark_point, axis=0)

    x, y, w, h = cv.boundingRect(landmark_array)

    return [x, y, x + w, y + h]


def _calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]

    landmark_point = []

    # Keypoint
    for _, landmark in enumerate(landmarks.landmark):
        landmark_x = min(int(landmark.x * image_width), image_width - 1)
        landmark_y = min(int(landmark.y * image_height), image_height - 1)
        # landmark_z = landmark.z

        landmark_point.append([landmark_x, landmark_y])

    return landmark_point


def _pre_process_landmark(landmark_list):
    temp_landmark_list = copy.deepcopy(landmark_list)

    # Convert to relative coordinates
    base_x, base_y = 0, 0
    for index, landmark_point in enumerate(temp_landmark_list):
        if index == 0:
            base_x, base_y = landmark_point[0], landmark_point[1]

        temp_landmark_list[index][0] = temp_landmark_list[index][0] - base_x
        temp_landmark_list[index][1] = temp_landmark_list[index][1] - base_y

    # Convert to a one-dimensional list
    temp_landmark_list = list(
        itertools.chain.from_iterable(temp_landmark_list))

    # Normalization
    global max_value
    max_value = max(list(map(abs, temp_landmark_list)))

    temp_landmark_list = list(map(normalize_, temp_landmark_list))

    return temp_landmark_list


interpreter = tf.lite.Interpreter(model_path='keypoint_classifier.tflite', num_threads=1)
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

with open('keypoint_classifier_label.csv',
          encoding='utf-8-sig') as f:
    keypoint_classifier_labels = csv.reader(f)
    keypoint_classifier_labels = [
        row[0] for row in keypoint_classifier_labels
    ]

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)


def gesturemodelmatch(image):
    image = cv.flip(image, 1)
    debug_image = copy.deepcopy(image)

    gesture_id = -1
    image = cv.cvtColor(image, cv.COLOR_BGR2RGB)

    image.flags.writeable = False

    results = hands.process(image)

    if results.multi_hand_landmarks is not None:
        for hand_landmarks, handedness in zip(results.multi_hand_landmarks,
                                              results.multi_handedness):
            # Bounding box calculation
            brect = _calc_bounding_rect(debug_image, hand_landmarks)
            # make sure hand is big enough
            width = brect[2]-brect[0]
            height = brect[3]-brect[1]
            area = width * height
            if area > config.config['gesture']['handsize']:
                # Landmark calculation
                landmark_list = _calc_landmark_list(debug_image, hand_landmarks)

                # Conversion to relative coordinates / normalized coordinates
                pre_processed_landmark_list = _pre_process_landmark(
                    landmark_list)

                # Hand sign classification
                input_details_tensor_index = input_details[0]['index']
                interpreter.set_tensor(
                    input_details_tensor_index,
                    np.array([pre_processed_landmark_list], dtype=np.float32))
                interpreter.invoke()

                output_details_tensor_index = output_details[0]['index']

                result = interpreter.get_tensor(output_details_tensor_index)

                hand_sign_id = np.argmax(np.squeeze(result))
                confidence = np.squeeze(result)[hand_sign_id]
                if confidence > config.config['gesture']['confidence']:
                    return keypoint_classifier_labels[hand_sign_id]
                else:
                    return ""
            else:
                return ""
    else:
        return ""
