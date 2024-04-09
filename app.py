from flask import Flask, render_template, Response
import cv2
import face_recognition
import numpy as np
import csv
from datetime import datetime, timedelta
import random
import mysql.connector as connector

# Establishing connection to MySQL database
try:
    con = connector.connect(
        host='localhost',  # Host where MySQL server is running
        port='3306',  # Port on which MySQL server is listening (default is 3306)
        user='root',  # Username for MySQL server
        password='dbms',  # Password for MySQL server
        database='Citizen'  # Name of the database to connect to
    )
    print("Connected to MySQL database successfully!")

    # Now you can perform operations on the database using the connection object 'con'
    cursor = con.cursor()

    # Creating table if not exists
    create_table_query = '''
    CREATE TABLE IF NOT EXISTS Citizen_record (
        id INT AUTO_INCREMENT PRIMARY KEY,
        Name_of_Citizen VARCHAR(255) NOT NULL,
        Spotted_time DATETIME NOT NULL
    )
    '''
    cursor.execute(create_table_query)
    con.commit()

except connector.Error as e:
    print(f"Error while connecting to MySQL database: {e}")

app = Flask(__name__)
camera = cv2.VideoCapture(0)

# Load known faces and their encodings
known_faces = {
    "Krish": face_recognition.face_encodings(face_recognition.load_image_file("Krish/krish.jpg"))[0],
    "Bradly": face_recognition.face_encodings(face_recognition.load_image_file("Bradley/bradley.jpg"))[0],
    "Yeshu": face_recognition.face_encodings(face_recognition.load_image_file("Yeshu/yeshu.jpg"))[0]
}

# CSV file path for storing attendance
csv_file = 'attendance.csv'

# Dictionary to track the last entry time for each detected person
last_entry_times = {}

# Array of Hindu names
hindu_names = [
    'Unknown man Ramesh', 
    'Unknown man Suresh', 
    'Unknown man Mukesh', 
    'Unknown man Rajesh', 
    'Unknown man Manish', 
    'Unknown man Vishal', 
    'Unknown man Nilesh', 
    'Unknown man Dinesh', 
    'Unknown man Kamlesh', 
    'Unknown man Mahesh',
    'Unknown man Arjun Sharma',
    'Unknown man Priya Patel',
    'Unknown man Neeta Gupta',
    'Unknown man Rahul Desai',
    'Unknown man Aarti Singh',
    'Unknown man Rajiv Jain',
    'Unknown man Nisha Kapoor',
    'Unknown man Anil Verma',
    'Unknown man Pooja Shah',
    'Unknown man Vivek Tiwari',
    'Unknown man Meera Mishra',
    'Unknown man Rohit Chatterjee',
    'Unknown man Kavita Reddy',
    'Unknown man Sunil Malhotra',
    'Unknown man Deepika Trivedi',
    'Unknown man Karan Khanna',
    'Unknown man Nidhi Agrawal',
    'Unknown man Siddharth Kapoor',
    'Unknown man Anjali Das',
    'Unknown man Aditya Sharma',
    'Unknown man Swati Joshi',
    'Unknown man Sameer Saxena',
    'Unknown man Jyoti Mehra',
    'Unknown man Sandeep Kumar',
    'Unknown man Renuka Bhatia',
    'Unknown man Vikram Singhania',
    'Unknown man Shalini Iyer',
    'Unknown man Sanjay Gupta',
    'Unknown man Geeta Sharma',
    'Unknown man Nitin Kapoor',
    'Unknown man Preeti Rao',
    'Unknown man Manoj Dixit',
    'Unknown man Ritu Singh',
    'Unknown man Arvind Bajaj',
    'Unknown man Shikha Yadav',
    'Unknown man Anupam Singh',
    'Unknown man Kiran Mehrotra',
    'Unknown man Deepak Malhotra',
    'Unknown man Sunita Trivedi',
    'Unknown man Tarun Joshi'
]

# Function to add entry to CSV file
def add_entry_to_csv(name):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        # Update the last entry time for the person
        last_entry_times[name] = datetime.now()
        print(name)
        query = "INSERT INTO Citizen_record (Name_of_Citizen, Spotted_time) VALUES (%s, %s)"
        cursor.execute(query, (name, datetime.now()))
        con.commit()
        print("Name insert into Database")

# Function to generate a random Hindu name for an unknown person
def generate_random_hindu_name():
    return random.choice(hindu_names)

# Function to remember an unknown face and assign a Hindu name
def remember_unknown_face(face_encoding):
    # Generate a random Hindu name for the unknown person
    name = generate_random_hindu_name()
    # Add the new face encoding to known_faces dictionary with the Hindu name
    known_faces[name] = face_encoding
    # Add an entry to the CSV file with the Hindu name
    add_entry_to_csv(name)
    return name

def gen_frames():
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            # Resize frame of video to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = small_frame[:, :, ::-1]

            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            face_names = []

            for face_encoding in face_encodings:
                # Check if the face matches any known face
                matches = face_recognition.compare_faces(list(known_faces.values()), face_encoding)
                name = "Unknown"

                if True in matches:
                    # If the face matches a known face, get the name
                    matched_name = list(known_faces.keys())[matches.index(True)]
                    # Check if enough time has passed since the last entry for this person
                    if matched_name not in last_entry_times or (datetime.now() - last_entry_times[matched_name]).seconds > 60:
                        add_entry_to_csv(matched_name)
                    name = matched_name
                else:
                    # If the face is unknown, remember it and assign a Hindu name
                    name = remember_unknown_face(face_encoding)

                face_names.append(name)

            # Display the results
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/admin')
def admin():
    try:
        # Fetching data from the database
        cursor.execute("SELECT * FROM Citizen_record")
        records = cursor.fetchall()
        return render_template('admin.html', records=records)
    except connector.Error as e:
        return f"Error fetching data from database: {e}"



if __name__ == '__main__':
    app.run(debug=True)
