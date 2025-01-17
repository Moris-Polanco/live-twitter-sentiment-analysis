import streamlit as st
from PIL import Image
import sys
import tweepy as tw
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from wordcloud import WordCloud
from textblob import TextBlob
import re
import time
import os
from dotenv import load_dotenv

load_dotenv()
nltk.download('all')

extra_stopwords = ["The", "It", "it", "in", "In", "wh"]

class SA:
    st.set_page_config(
        page_title="Live Twitter Sentiment Analysis",
        layout="wide", page_icon="favcurt.png"
    )

    def __init__(self):
        self.api_key = 'CXjWqbqODoTLR8hNwe1h352jX'
        self.api_key_secret = '5e0c1NR5aQGkHsixpPxxBZulRzxPvRLrMFHI1E3fT0jQnOe7Wh'
        self.access_token = '113763054-c0ULFNs4rrXthT9FRnooFDVx8C81HVLZJFYBrctG'
        self.access_token_secret = 'ZKyUofCpqNRJMfe28xi3pqOCwJ5Pee4e0psIizBZiHXNK'
        self.auth = tw.OAuthHandler(self.api_key, self.api_key_secret)
        self.auth.set_access_token(self.access_token, self.access_token_secret)
        self.api = tw.API(self.auth, wait_on_rate_limit=True)

        st.title('Live Twitter Sentiment Analysis')
        st.markdown('Get the sentiment labels of live tweets!')

    def get_tweets(self, user_name, tweet_count):
        tweets_list = []
        img_url = ""
        name = ""

        try:
            for tweet in self.api.user_timeline(
                id=user_name, count=tweet_count, tweet_mode="extended",include_rts=False
            ):
                tweets_dict = {}
                tweets_dict["date_created"] = tweet.created_at
                tweets_dict["tweet_id"] = tweet.id
                tweets_dict["tweet"] = tweet.full_text

                tweets_list.append(tweets_dict)

            img_url = tweet.user.profile_image_url
            name = tweet.user.name
            screen_name = tweet.user.screen_name
            desc = tweet.user.description

        except BaseException as e:
            st.exception(
                "Failed to retrieve the Tweets. Please check if the twitter handle is correct. "
            )
            sys.exit(1)

        return tweets_list, img_url, name, screen_name, desc

    def prep_data(self, tweet):

        # cleaning the data
        # replacing url with domain name
        tweet = re.sub("https?:\/\/\S+", "", tweet)
        tweet = re.sub("#[A-Za-z0–9]+", " ", tweet)  # removing #mentions
        tweet = re.sub("#", " ", tweet)  # removing hash tag
        tweet = re.sub("\n", " ", tweet)  # removing \n
        tweet = re.sub("@[A-Za-z0–9]+", "", tweet)  # removing @mentions
        tweet = re.sub("RT", "", tweet)  # removing RT
        # removing 1-2 char long words
        tweet = re.sub("^[a-zA-Z]{1,2}$", "", tweet)
        # removing words containing digits
        tweet = re.sub("\w*\d\w*", "", tweet)
        for word in extra_stopwords:
            tweet = tweet.replace(word, "")

        # lemmitizing
        lemmatizer = WordNetLemmatizer()
        new_s = ""
        for word in tweet.split(" "):
            lemmatizer.lemmatize(word)
            if word not in stopwords.words("english"):
                new_s += word + " "

        return new_s[:-1]

    def wordcloud(self, clean_tweet):
        # remove the old wordcloud
        if os.path.exists("cloud.png"):
            os.remove("cloud.png")
        wordcloud_words = " ".join(clean_tweet)
        wordcloud = WordCloud(
            height=300, width=500, background_color="black", random_state=100,
        ).generate(wordcloud_words)
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        plt.savefig("cloud.jpg")
        img = Image.open("cloud.jpg")
        return img

    def getPolarity(self, tweet):
        sentiment_polarity = TextBlob(tweet).sentiment.polarity
        return sentiment_polarity

    def getAnalysis(self, polarity_score):
        if polarity_score < 0:
            return "Negative"
        elif polarity_score == 0:
            return "Neutral"
        else:
            return "Positive"

    def getSubjectivity(self, tweet):
        sentiment_subjectivity = TextBlob(tweet).sentiment.subjectivity
        return sentiment_subjectivity

    def getSubAnalysis(self, subjectivity_score):
        if subjectivity_score <= 0.5:
            return "Objective"
        else:
            return "Subjective"

    def plot_sentiments(self, tweet_df):
        sentiment_df = (
            pd.DataFrame(tweet_df["sentiment"].value_counts())
            .reset_index()
            .rename(columns={"index": "sentiment_name"})
        )
        fig = go.Figure(
            [go.Bar(x=sentiment_df["sentiment_name"],
                    y=sentiment_df["sentiment"])]
        )
        fig.update_layout(
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False, title="Sentiment Score"),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig

    def plot_subjectivity(self, tweet_df):

        colors = ["mediumturquoise", "blue"]

        fig = go.Figure(
            data=[
                go.Pie(
                    values=tweet_df["subjectivity"].values,
                    labels=tweet_df["sub_obj"].values,
                )
            ]
        )
        fig.update_traces(
            hoverinfo="label",
            textinfo="percent",
            textfont_size=18,
            marker=dict(colors=colors, line=dict(color="#000000", width=2)),
        )
        return fig

    def app(self):

        tweet_count = st.empty()
        user_name = st.empty()

        st.sidebar.header("Enter the Details Here!!")

        user_name = st.sidebar.text_area("Enter the Twitter Handle without @")

        tweet_count = st.sidebar.slider(
            "Select the number of Latest Tweets to Analyze", 0, 50, 1
        )

        st.sidebar.markdown(
            "#### Press Ctrl+Enter or Use the Slider to initiate the analysis."
        )
        st.sidebar.markdown(
            "*****************************************************************"
        )

        st.markdown("Created By: [Zaid Mukaddam](https://twitter.com/zaidmukaddam)")
        st.markdown(
            """# Twitter Sentiment Analyzer :slightly_smiling_face: :neutral_face: :angry: """
        )
        st.write(
            "This app analyzes the Twitter tweets and returns the most commonly used words, associated sentiments and the subjectivity score!! Note that Private account / Protected Tweets will not be accessible through this app."
        )
        st.write(
            ":bird: All results are based on the number of Latest Tweets selected on the Sidebar. :point_left:"
        )

        # main
        if user_name != "" and tweet_count > 0:

            with st.spinner("Please Wait!! Analysis is in Progress......:construction:"):
                time.sleep(1)

            tweets_list, img_url, name, screen_name, desc = self.get_tweets(
                user_name, tweet_count
            )

            # adding the retrieved tweet data into a dataframe
            tweet_df = pd.DataFrame([tweet for tweet in tweets_list])
            st.sidebar.success("Twitter Handle Details:")
            st.sidebar.markdown("Name: " + name)
            st.sidebar.markdown("Screen Name: @" + screen_name)
            st.sidebar.markdown("Description: " + desc)

            # calling the function to prep the data
            tweet_df["clean_tweet"] = tweet_df["tweet"].apply(self.prep_data)

            # calling the function to create sentiment scoring
            tweet_df["polarity"] = tweet_df["clean_tweet"].apply(self.getPolarity)
            tweet_df["sentiment"] = tweet_df["polarity"].apply(self.getAnalysis)
            tweet_df["subjectivity"] = tweet_df["clean_tweet"].apply(self.getSubjectivity)
            tweet_df["sub_obj"] = tweet_df["subjectivity"].apply(self.getSubAnalysis)

            # calling the function for plotting the sentiments
            senti_fig = self.plot_sentiments(tweet_df)
            st.success(
                "Sentiment Analysis for Twitter Handle @"
                + user_name
                + " based on the last "
                + str(tweet_count)
                + " tweet(s)!!"
            )
            st.plotly_chart(senti_fig, use_container_width=True)

            # calling the function for plotting the subjectivity
            subjectivity_fig = self.plot_subjectivity(tweet_df)

            if sum(tweet_df["subjectivity"].values) > 0:
                st.success(
                    "Tweet Subjectivity vs. Objectivity for Twitter Handle @"
                    + user_name
                    + " based on the last "
                    + str(tweet_count)
                    + " tweet(s)!!"
                )
                st.plotly_chart(subjectivity_fig, use_container_width=True)
            else:
                st.error(
                    "Sorry, too few words to analyze for Subjectivity & Objectivity Score. Please increase the tweet count using the slider on the sidebar for better results."
                )

            # calling the function to create the word cloud
            img = self.wordcloud(tweet_df["clean_tweet"])
            st.success(
                "Word Cloud for Twitter Handle @"
                + user_name
                + " based on the last "
                + str(tweet_count)
                + " tweet(s)!!"
            )
            st.image(img)

            # displaying the latest tweets
            st.subheader(
                "Latest Tweets (Max 10 returned if more than 10 selected using the sidebar)!"
            )
            st.markdown("*****************************************************************")
            st.success("Latest Tweets from the Twitter Handle @" + user_name)

            length = 10 if len(tweet_df) > 10 else len(tweet_df)

            for i in range(length):
                st.write(
                    "Tweet Number: "
                    + str(i + 1)
                    + ", Tweet Date: " # making the date readable from 2022-05-16 20:26:52+00:00 to May 16, 2022 at 20:26:52
                    + tweet_df["date_created"].iloc[i].strftime("%b %d, %Y at %H:%M:%S")
                )
                st.info(tweet_df["tweet"][i])
        else:
            st.info(
                ":point_left: Enter the Twitter Handle & Number of Tweets to Analyze on the SideBar :point_left:"
            )


if __name__ == '__main__':
    t = SA()
    st.cache(persist=False)
    st.empty()
    t.app()
