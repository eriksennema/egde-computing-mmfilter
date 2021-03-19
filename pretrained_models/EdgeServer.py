import threading
import time
import numpy as np
import socket
import cv2
import os
import requests
from collections import deque
from PretrainedModels import PretrainedModels
from MultithreadServer import MultithreadServer


def frame_to_bytes(frame):
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50] # Image quality ranges from 0 to 100
    frame_encode = cv2.imencode('.jpg', frame, encode_param)[1]
    bytes_data = frame_encode.tobytes()
    return bytes_data


def send_to_cloud(frames, port, host="localhost"):
    print("Making connection to cloud server...")
    if host == "localhost":
        for frame in frames:
            for channel in frame:
                pload = np.array2string(channel, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", "").replace("\r", "")
                r = requests.post(f'http://127.0.0.1:{port}/request', data=pload)
                print("Cloud server returen status: ", r.status_code)
    else:
        for frame in frames:
            for channel in frame:
                pload = np.array2string(channel, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", "").replace("\r", "")
                r = requests.post(f'{host}:{port}/request', data=pload)
                print("Cloud server returen status: ", r.status_code)


def start_processing(q, scala_port, cloud_port, host="localhost", threshold=0.9, dir_path="./selected_imgs"):
    while True:
        if len(q) > 0:
            score_q = deque()
            frames = q.popleft()  # original frames
            video_feature = pretrainedModel.featureExtractor.run(frames)
            query_feature = pretrainedModel.wordEncoder.run("My cat is scratching the sofa.")
            print("Pretrained features got.")

            thread = threading.Thread(target=get_cosine_score, args=(query_feature, video_feature, scala_port, score_q))
            thread.start()
            thread.join()  # priority
            score = score_q.pop()
            score = float(score.strip().replace("[", "").replace("]", ""))
            print("Cosine score: ", score)

            if score > threshold:
                filepath = os.path.join(dir_path, f"img{str(time.time())}.jpg")
                print(frames.shape)
                cv2.imwrite(filepath, np.transpose(frames[0], (1, 2, 0)))
                thread2 = threading.Thread(target=send_to_cloud, args=(frames, cloud_port))
                thread2.start()
                thread2.join()  # priority

        time.sleep(5)


def get_cosine_score(query_feature, video_feature, port, score_q, host="localhost"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))

        # sending query feature
        data = np.array2string(query_feature, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", "").replace("\r", "")
        try:
            s.sendall(bytes(data + "\r\n", encoding="utf-8"))
        except IOError as e:
            print("ERROR in pretrained model sending!!!")

        # sending video feature
        for frame in video_feature:
            data = np.array2string(frame, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", "").replace("\r", "")
            try:
                s.sendall(bytes(data+"\r\n", encoding="utf-8"))
            except IOError as e:
                print("ERROR in pretrained model sending!!!")

        score = s.recv(1024).decode('utf-8')
        score_q.append(score)


if __name__ == "__main__":
    pretrainedModel = PretrainedModels()

    EDGEDEVICE_PORT = 10001
    SCALA_SEND_PORT = 10002
    CLOUD_PORT = 8080

    server = MultithreadServer("localhost", EDGEDEVICE_PORT)
    thread1 = threading.Thread(target=server.listen)
    thread1.start()

    thread2 = threading.Thread(target=start_processing, args=(server.q, SCALA_SEND_PORT, CLOUD_PORT))
    thread2.start()

    # frames = np.random.rand(12, 3, 256, 256)
    # send_to_cloud(frames, CLOUD_PORT)

    # frames = np.random.rand(1, 32, 1, 1).reshape(-1)
    # query = np.random.rand(1, 32).reshape(-1)
    # # frames = np.random.rand(12).reshape(-1)
    # # query = np.random.rand(1).reshape(-1)
    # # print(frames, np.array2string(frames, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", ""))
    # # print(query)
    # tmp = os.popen("java -cp /Users/jennyxu/Desktop/Delft/Q3/Distributed\ Systems/mmfilter/mmfilter.jar example.Main " +
    #                np.array2string(frames, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", "") + " " +
    #                np.array2string(query, precision=2, separator=',', suppress_small=False).replace("[", "").replace("]", "").replace(" ", "").replace("\n", "")).readlines()
    #
    # print(tmp)