import json
import os
import tkinter as tk


def cancelclick():
    exit(0)


class GUI:
    def okclick(self):
        data = {"keyword": self.urlentry.get(),
                "telegramAPIKEY": self.apikeyentry.get(),
                "telegramCHATID": self.chatidentry.get(),
                "databaseFile": self.databaseentry.get(),
                "sleepDay": self.sleepDayeentry.get(),
                "sleepNight": self.sleepNighteentry.get()
                }
        with open(self.file_name, 'w') as config_file:
            json.dump(data, config_file)
        config_file.close()
        self.window.destroy()
        pass

    def __init__(self, file_name):
        self.file_name = file_name
        self.window = tk.Tk()
        self.window.geometry('905x600')

        keywordlabel = tk.Label(text="keyword")
        self.urlentry = tk.Entry(width=100, justify=tk.CENTER)

        databaselabel = tk.Label(text="databaseFile")
        self.databaseentry = tk.Entry(width=100, justify="center")

        apikeylabel = tk.Label(text="telegramAPIKEY")
        self.apikeyentry = tk.Entry(width=100, justify="center")

        chatidlabel = tk.Label(text="telegramCHATID")
        self.chatidentry = tk.Entry(width=100, justify="center")

        sleepDaylabel = tk.Label(text="sleepDay")
        self.sleepDayeentry = tk.Entry(width=100, justify="center")

        sleepNightlabel = tk.Label(text="sleepNight")
        self.sleepNighteentry = tk.Entry(width=100, justify="center")

        okbutton = tk.Button(self.window, text="OK", command=self.okclick)
        cancelbutton = tk.Button(self.window, text="Cancel", command=cancelclick)

        keywordlabel.grid(column=0, row=0)
        self.urlentry.grid(column=0, row=1)

        databaselabel.grid(column=0, row=2)
        self.databaseentry.grid(column=0, row=3)

        apikeylabel.grid(column=0, row=4)
        self.apikeyentry.grid(column=0, row=5)

        chatidlabel.grid(column=0, row=6)
        self.chatidentry.grid(column=0, row=7)

        sleepDaylabel.grid(column=0, row=8)
        self.sleepDayeentry.grid(column=0, row=9)

        sleepNightlabel.grid(column=0, row=10)
        self.sleepNighteentry.grid(column=0, row=11)

        okbutton.grid(column=0, row=12)
        cancelbutton.grid(column=0, row=13)

        if os.path.isfile(file_name):
            with open(file_name) as config_file:
                config = json.load(config_file)
                self.urlentry.insert(0, config["keyword"])
                self.apikeyentry.insert(0, config["telegramAPIKEY"])
                self.chatidentry.insert(0, config["telegramCHATID"])
                self.databaseentry.insert(0, config["databaseFile"])
                self.sleepDayeentry.insert(0, config["sleepDay"])
                self.sleepNighteentry.insert(0, config["sleepNight"])
            config_file.close()
        else:
            self.databaseentry.insert(0, "database.db")
            self.sleepDayeentry.insert(0, "10")
            self.sleepNighteentry.insert(0, "30")

        self.window.mainloop()
