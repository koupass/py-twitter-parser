import csv
import json
import time

from tweepy import Cursor
from tweepy.api import API
from tweepy.auth import OAuthHandler
from tweepy.streaming import Stream, StreamListener

# Variables that contains the user credentials to access Twitter API
access_token = ""
access_token_secret = ""
consumer_key = ""
consumer_secret = ""

# Variables that contains the Files path
tweets_data_path = 'abcd.json'
users_tweets_path = 'users_tweets.csv'
users_friends_path = 'users_friends.csv'


class GetTwitterData():
    def __init__(self, auth):
        self.auth = auth
        self.api = API(self.auth)

    def get_all_tweets(self, screen_name, tweet_count):

        # initialize a list to hold all the tweepy Tweets
        alltweets = []

        # make initial request for most recent tweets (200 is the maximum allowed count)
        new_tweets = self.api.user_timeline(screen_name=screen_name, count=tweet_count)

        # save most recent tweets
        alltweets.extend(new_tweets)

        # save the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1

        # keep grabbing tweets until there are no tweets left to grab
        while len(new_tweets) > 0:
            print "getting tweets before %s" % (oldest)

            # all subsiquent requests use the max_id param to prevent duplicates
            new_tweets = self.api.user_timeline(screen_name=screen_name, count=tweet_count, max_id=oldest)

            # save most recent tweets
            alltweets.extend(new_tweets)

            # update the id of the oldest tweet less one
            oldest = alltweets[-1].id - 1

            print "...%s tweets downloaded so far" % (len(alltweets))

        # transform the tweepy tweets into a 2D array that will populate the csv
        out_tweets = [[screen_name, tweet.id_str, tweet.created_at, tweet.text.encode("utf-8")] for tweet in alltweets]

        # write the csv
        with open(users_tweets_path, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(["screen_name", "id", "created_at", "text"])
            writer.writerows(out_tweets)

        pass

    def new_get_all_tweets(self, screen_name, tweet_count):

        # make initial request for most recent tweets (200 is the maximum allowed count)
        new_tweets = self.api.user_timeline(screen_name=screen_name, count=tweet_count)

        # transform the tweepy tweets into a 2D array that will populate the csv
        out_tweets = [[screen_name, tweet.id_str, tweet.created_at, tweet.text.encode("utf-8")] for tweet in new_tweets]
        # write the csv
        with open(users_tweets_path, 'wb') as f:
            writer = csv.writer(f)
            writer.writerow(["screen_name", "id", "created_at", "text"])
            writer.writerows(out_tweets)

    def find_friends(self, screen_name):

        print "screen_name: " + screen_name

        # page = self.api.followers_ids(screen_name=screen_name)

        for id in Cursor(self.api.followers_ids, screen_name=screen_name,count=50).pages():
            print  id
            print "ids are: " + str(len(id))
            # if (len(id) > 90):
            #     array_offset = (len(id) % 90)
            #     friends_list=[]
            #     for x in range(1, array_offset):
            #         print "cutted id is:"
            #         print id[((x - 1) * 90):(x * 90)]
            #         friends = [user.screen_name for user in self.api.lookup_users(user_ids=str(id[((x - 1) * 90):(x * 90)]))]
            #         friends_list.extend(friends)
            #
            # else:
            #     friends_list = [user.screen_name for user in self.api.lookup_users(user_ids=id)]
            friends_list = [user.screen_name for user in self.api.lookup_users(user_ids=id)]
            print "list of users\n"
            print friends_list
            friends_list_output = [[screen_name, id[indx], friend]
                                   for indx, friend in enumerate(friends_list)]
            print friends_list_output
            with open(users_friends_path, 'ab') as f:
                writer = csv.writer(f)
                writer.writerow(["screen_name", "id", "friends"])
                writer.writerows(friends_list_output)

            time.sleep(1)

    def readfile(self):
        tweets_data = []
        tweets_file = open(tweets_data_path, "r")
        for line in tweets_file:
            try:
                tweet = json.loads(line)
                tweets_data.append(tweet)
            except:
                continue

        print len(tweets_data)
        counter = 1
        screen_names = []
        for tweet in tweets_data:
            screen_names.extend(tweet['user']['screen_name'])
            try:
                self.new_get_all_tweets(tweet['user']['screen_name'], 5)
            except Exception, e:
                print "error:\n"
                print str(e)

            try:
                print tweet['user']['screen_name']
                self.find_friends(tweet['user']['screen_name'])
            except Exception, e:
                print "fail:\n"
                print str(e)
            print counter
            # print 'tweet:' + tweet['text'] + "\n"
            # print 'user name:' + tweet['user']['name'] + "\n"
            # print 'user id:' + str(tweet['user']['id_str']) + "\n"
            # print "\nuser is flowing \n"
            # print 'user name:' + tweet['user']['name']
            #
            # print "\n>>>>>>>>>>>>\n"
            counter = counter + 1


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def __init__(self, time_limit=60):
        self.start_time = time.time()
        self.limit = time_limit
        self.saveFile = open(tweets_data_path, 'a')
        super(StdOutListener, self).__init__()

    def on_data(self, data):
        if (time.time() - self.start_time) < self.limit:
            self.saveFile.write(data)
            self.saveFile.write('\n')
            return True
        else:
            self.saveFile.close()
            return False

    def on_error(self, status):
        print status


if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)
    tw_getter = GetTwitterData(auth)
    stream.filter(track=['#'])
    tw_getter.readfile()
