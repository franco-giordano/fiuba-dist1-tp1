from threading import Thread

class Data():
    def __init__(self, data):
        self.data = data

    def thread(self):
        thread1 = Thread(target = self.change)
        thread1.start()
        thread1.join()

    def change(self):
        print("before internal ", self.data)

        self.data += 10

def change(data):
    data.data += 100
    print("thread ", data.data)


def change2(data):
    print("before thread2 ", data.data)

    data.data += 1000
    print("thread2 ", data.data)
    

data = Data(1)
thread1 = Thread(target = change, args = (data, ))
thread2 = Thread(target = change2, args = (data, ))
thread1.start()
thread1.join()
data.thread()
thread2.start()
thread2.join()

print("main ", data.data)
