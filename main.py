import cstrattyw

if __name__ =='__main__':

    with open("token.txt", "r") as f:
        token = f.readlines()[0].strip()

    cstrattyw.runBot(token)
