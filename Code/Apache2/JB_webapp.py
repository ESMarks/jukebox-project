from flask import Flask, render_template, request, Markup
import sqlite3
#import Jukebox
#from board import SCL, SDA
#import busio
#from PIL import Image, ImageDraw, ImageFont
#import adafruit_ssd1306


app = Flask(__name__)

#Initialize display based on ADAFruit tutorial
#i2c = busio.I2C(SCL, SDA)
#disp = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
#disp.fill(0)
#disp.show()
#width = disp.width
#height = disp.height
#image = Image.new("1", (width, height))
#draw = ImageDraw.Draw(image)
#draw.rectangle((0, 0, width, height), outline=0, fill=0)
#padding = -2
#top = padding
#bottom = height - padding
#x = 0
#font = ImageFont.load_default()

#Load songs from text file
f = open("/var/www/Jukebox/JBtitlesCurrent2.txt", "r", encoding='cp1252')
songs = ""
# for row in range(0,800):
#     next = f.readline().rstrip()
#     next = next.strip("\"")
#     songs = songs + next + "\n"#"<br />"
radio = ""
f.seek(0)
for row in range(0,800):
    next = f.readline().rstrip()
    next = next.strip("\"")
    radio = radio + "<input type=\"radio\" name=\"selection\" value=\"" + next[41:] + "\" /> " + next[0:41] + "<br />"
f.close()
songs = Markup(songs)
radio = Markup(radio)

#songsDict = Jukebox.altLoadTitles()


@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        # machine = int(request.form['machine'])
        # column = int(request.form["column"])
        # row = int(request.form["row"])
        selection = request.form["selection"]
        connection = sqlite3.connect('/var/databases/Jukebox/jukebox.db')
        cursor = connection.cursor()
        cursor.execute("INSERT INTO selection (code) VALUES (?)", (selection,))
        connection.commit()
        connection.close()
        #reply = makeSelection(int(selection[0]), int(selection[1]), int(selection[2]))
        #if (reply == "0" or reply == "5"):
        return render_template("input_received.html")
        #else:
            #return render_template("error.html")
    else:
        return render_template("selection_form.html", titles=songs, radio=radio)


@app.route("/alexa")
def alexa_data():
    if request.method == "POST":
        selection = request.form["selection"].upper()
        print("Data to function:", selection)
        songCode = songsDict[selection]
        reply = makeSelection(int(songCode[0]), int(songCode[1]), int(songCode[2]))
        return ' ', 204
    else:
        return "Incorrect method (expected POST)", 404

@app.route("/status")
def status():
    return render_template("status.html")

@app.route("/api/status")
def stats():
    conn = sqlite3.connect('/var/databases/Jukebox/jukebox.db')
    cur=conn.cursor()
    cur.execute("SELECT status FROM jukeboxes")
    re_value = cur.fetchall()
    conn.close()
    return_val = {"status": re_value[0][0]}
    return return_val


def makeSelection(machine, column, row):
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    disp.image(image)
    disp.show()
    draw.text((x, top + 0), "Got song request", font=font, fill=255)
    draw.text((x, top + 8), "Sending " + str(machine) + str(row) + str(column) + " to base", font=font, fill=255)
    disp.image(image)
    disp.show()
    reply = Jukebox.select(machine, column, row)
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    draw.text((x, top + 0), "Got song request", font=font, fill=255)
    draw.text((x, top + 8), "Sending " + str(machine) + str(row) + str(column) + " to base", font=font, fill=255)
    draw.text((x, top + 16), "Song Selected!", font=font, fill=255)
    draw.text((x, top + 24), "Reply = " + reply, font=font, fill=255)
    disp.image(image)
    disp.show()
    return reply

if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0')
