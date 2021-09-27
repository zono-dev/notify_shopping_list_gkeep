import gkeepapi
import os
import pickle
import requests
import argparse

LAST_DATA_PATH="last_list.pickle"
WISHLIST_NOTE_NAME="買い物リスト"
LINE_NOTIFY_URL="https://notify-api.line.me/api/notify"
MESSAGE_TEMPLATE="""New update: Shopping List 
%s"""

# dump_all_list print all list
def dump_all_list(target):
    for i in target:
        print(i.text)

# make_message makes massage with template
def make_message(tmpl, src_list):
    tmp = [i.text for i in src_list]
    return tmpl%("\n".join(tmp))

# send_message_to_line send message to LINE NOTIFY
def send_message_to_line(token, message):
    headers = {
        "Authorization": "Bearer %s"%token,
    }

    files = {
        "message": (None, message)
    }
    res = requests.post(LINE_NOTIFY_URL, headers=headers, files=files)
    return res

# is_updated check last wish list and current wish list
def is_updated(last, current):
    for i in current:
        isFounded = False
        for j in last:
            if i.text == j.text:
                isFounded = True
                break
        if not isFounded:
            return True
    return False

# getnotes checks last and current wish list and returns True if any updates are there.
def getnotes(setup_info):
    keep = gkeepapi.Keep()

    success = keep.login(setup_info["g_email"], setup_info["g_passwd"])

    if not success:
        print("Login Error")
        return False

    gnotes = keep.all()
    notify_flag = False
    for i in gnotes:
        if(i.title == WISHLIST_NOTE_NAME):
            print("Current list")
            dump_all_list(i.unchecked)
        
            # force_notify is True -> notify
            # Last data exists is not None and any updates are there -> notify
            if(setup_info["f_notify"] or ( setup_info["last_data"] != None and is_updated(setup_info["last_data"], i.unchecked ))):
                message = make_message(MESSAGE_TEMPLATE, i.unchecked)
                res = send_message_to_line(setup_info["line_token"], message)
                print(res)

            # save current data
            fp = open(LAST_DATA_PATH, "wb")
            pickle.dump(i.unchecked, fp)
            fp.close()
            break

# setup_args define arguments of this program
def setup_args():
    parser = argparse.ArgumentParser(description="Google Keepの買い物リストをLINE通知してくれるよ")
    parser.add_argument("g_email")
    parser.add_argument("g_passwd")
    parser.add_argument("l_token")
    parser.add_argument("-f", "--force_notify", type=bool, default=False)
    args = parser.parse_args()
    return args

# setup 
def setup():
    args = setup_args()
    g_email = args.g_email
    g_passwd = args.g_passwd
    l_token = args.l_token
    f_notify = args.force_notify

    last_checked_list = None

    if(os.path.exists(LAST_DATA_PATH)):
        fp = open(LAST_DATA_PATH, "rb")
        last_checked_list = pickle.load(fp)
        fp.close()
        print("Last time list")
        dump_all_list(last_checked_list)

    return {"g_email": g_email, "g_passwd": g_passwd, "last_data": last_checked_list, "line_token": l_token, "f_notify": f_notify}

if __name__ == "__main__":
    setup_info = setup()
    getnotes(setup_info)