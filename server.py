import socket
from statistics import mode 
from threading import Lock
import threading

import pandas as pd
import numpy as np
import random

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER,PORT)
FORMAT = 'utf-8'
DISCONNECT_MSG = "!DISCONNECT"

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):



    print(f"[NEW CONNECTION] {addr} connected.")

    connected = True
    lock = Lock()
    while connected:

        
        #Receive Message

        # get the text via the scoket
        encodedMessage = conn.recv(HEADER)

        # if we didn't get anything, log an error and bail
        if not encodedMessage:
            print('error: encodedMessage was received as None')
            return None
        # end i

        # decode the received text message
        msg = encodedMessage.decode(FORMAT)

        #msg = conn.recv(HEADER).decode(FORMAT)

        #Filtering
        msg = msg.strip('\n')
        msg = msg.strip('\r')

        print(f"[{addr} {msg}]")

        if msg == DISCONNECT_MSG:
            connected = False

        if msg == 'check Thread':

            print("Check")

            # output = threading.currentThread.__name__
            # print(output)
            # return

        if (msg == 'Send Message' or msg == 'Send Message\r\n'):

            print("Sending")
            # encode the text message
            model_data = compute()
            print(model_data)
            # print(type(model_data))
            # print("!!!!!")
            model_data = str(model_data) + "\r\n"
            encodedMessage = bytes(model_data, FORMAT)

            # send the data via the socket to the server
            conn.send(encodedMessage)

            #  # receive acknowledgment from the server
            # encodedAckText = conn.recv(1024)
            # ackText = encodedAckText.decode(FORMAT)
            

            # # log if acknowledgment was successful
            # if ackText == ACK_TEXT:
            #     print('server acknowledged reception of text')
            # else:
            #     print('error: server has sent back ' + ackText)
        # end if
            
            
            
    
    conn.close()


def direction_prediction(time, direction,traffic_df):
    northDirections = ["NORTH", "North", "north", "N", "n"]
    southDirections = ["SOUTH", "South", "south", "S", "s"]
    westDirections = ["WEST", "West", "west", "W", "w"]
    eastDirections = ["EAST", "East", "east", "E", "e"]
    listOfTimes = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]
    #check if direction is valid
    if (direction in northDirections):
        DIR = "NB"
        LEFT = "EB"
        RIGHT = "WB"
    elif (direction in southDirections):
        DIR = "SB"
        LEFT = "EB"
        RIGHT = "WB"
    elif (direction in eastDirections):
        DIR = "EB"
        LEFT = "NB"
        RIGHT = "SB"
    elif (direction in westDirections):
        DIR = "WB"
        LEFT = "NB"
        RIGHT = "SB"
    else:
        return ("enter a valid direction")
    
    #check if time is valid
    if (time not in listOfTimes):
        return("enter a valid time")
    else: 
        TIME = time
        if (TIME == 0):
            PAST = 23
        else:
            PAST = TIME -1

        if (TIME == 23):
            NEXT = 0
        else:
            NEXT = TIME +1
        
        

#predict a value for a direction and time
    def predict_count(TIME, DIR,traffic_df):
        #filter to same direction and time
        data = traffic_df[traffic_df['Direction'] == DIR]
        data = data[data['Time'] == TIME]
        count_array = data['Count'].to_numpy()
        
        #check that all directions and times are called
        #print("average for", TIME, DIR, "is" , np.average(count_array))
        
        #split data at 3000
        above_array = count_array[count_array >= 3000]
        below_array = count_array[count_array < 3000]
    
        #select point either above or below 3K 
        prob_above = len(above_array) / len(below_array)
        random_number = random.uniform(0, 1)
        if (prob_above > random_number):
            count = random.choice(above_array)
        else:
            count = random.choice(below_array)
        return count
    
    
    #predict a count value 3 directions and 3 different hours
    #directions needed are DIR + 2 perpendicular directions
    
    #predict DIR for each time
    forward_now = predict_count(TIME, DIR,traffic_df)
    forward_next = predict_count(NEXT, DIR,traffic_df)
    forward_past = predict_count(PAST, DIR,traffic_df)
    forward_predict = np.mean(forward_now + forward_next + forward_past)
    
    #predict DIR for each time
    left_now = predict_count(TIME, LEFT,traffic_df)
    left_next = predict_count(NEXT, LEFT,traffic_df)
    left_past = predict_count(PAST, LEFT,traffic_df)
    left_predict = np.mean(left_now + left_next + left_past)
    
    #predict DIR for each time
    right_now = predict_count(TIME, RIGHT,traffic_df)
    right_next = predict_count(NEXT, RIGHT,traffic_df)
    right_past = predict_count(PAST, RIGHT,traffic_df)
    right_predict = np.mean(right_now + right_next + right_past)
    
    
    final_prediction = (0.1*(right_predict) + 0.1*(left_predict) + 0.8*(forward_predict))
    return final_prediction   

def compute():
    #save the CSV file as a pandas dataframe 
    traffic_df = pd.read_csv ('traffic-volume-counts-2012-2013.csv')

    #current traffic_df has hours as a entry. we can use DF.melt() to preserve the "id_vars" and convert each hour to an entry in the row
    traffic_df = traffic_df.melt(id_vars=["ID", "Segment ID", "Roadway Name","From", "To", "Direction", "Date"], 
    var_name="Time", 
    value_name="Count")
    traffic_df = traffic_df.astype({'Time':'int'})

    #check the resulting dataframe (remove "#" to view)
    #print(traffic_df)


    #lets try to visualize the data to see what features might be available
    #fig = px.scatter(traffic_df, x="Time", y="Count", color = "Direction", title="Cars Counted vs Time of Day")
    #fig.show()
    #print("       *you can select which points are present on the plot by clicking each direction on the legend")


    #begin the prediction algorithm 

    #this prediction algorithm takes a direction and time as arguements
    #    1) Then all points with the same direction are selected.
    #    2) next we determine the probability that a point is above or below the 3000 level that we observed from the data
    #    3) select a random point based on the prediction at time = time
    #    4) repeat the point selection process at time +- 1
    #    5) return the average of these 3 points
    #    6) repeat steps 2-5 with perpendicular directions
    #    7) return the prediction of a sum of all three direction predictions 
    #    ex: time = 4, direction = North
    #    return 0.6(north @ 4) + 0.2(east @ 4) + 0.2(west @ 4)

    return direction_prediction(0,"w",traffic_df)




def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

    
        


print("[STARTING] Server starts...")
start()

