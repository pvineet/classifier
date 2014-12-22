import csv
import nltk

word_list = [
            "options",
            "option",
            "please",
            "please check",
            "please confirm",
            "please find",
            "please send",
            "please book",
            "plz",
            "plz share",
            "pls",
            "hotel",
            "provide",
            "send",
            "confirm",
            "suggest",
            "details",
            "quotation",
            "quotations",
            "booking",
            "book",
            "cancel",
            "this",
            "location",
            "preferred",
            "apartment",
            "provides",
            "quote",
            "quotes",
            "request",
            "request you",
            "requested",
            "forward",
            "check",
            "help",
            "rate",
            "rates",
            "subject",
            "we",
            "availability",
            "card",
            "process",
            "find",
            "share",
            "payment",
            "report",
            "voucher",
            "invoice",
            "confirmation",
            "confirmation voucher",
            "get us",
            ]
def request_features(mail):
    features = {}
    for word in word_list:
        if word in mail.lower().split(' '):
            features["has (%s)" %  word] = True
        else:
            features["has (%s)" % word] = False   
    return features

"""
def train
"""

def classify(test_mail):
    featuresets = []
    with open('train.csv', 'rb') as csvfile:
        train_set = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in train_set:
            featuresets.append((request_features(row[0].lower()), row[1]))
        classifier = nltk.NaiveBayesClassifier.train(featuresets)
    return classifier.classify(request_features(test_mail.lower()))


f_log = open('log', 'rb')

for line in f_log.readlines():
    if line.split(' ')[0] == 'FILE':
        continue
    else:
        print line
        print classify(line)
f_log.close()
