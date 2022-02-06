from flask import Flask, render_template,request,redirect,url_for,abort
import os.path
import yaml
import requests
import json
import pandas as pd

app = Flask(__name__)
app.secret_key = 'h432hi5ohi3h5i5hi3o2hi'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/token-holders-info',methods=['GET','POST'])
def token_holders_info():
    if request.method=='POST':
        with open('config.yaml') as configfile:
            config_para = yaml.load(configfile,Loader=yaml.FullLoader)
        api_key = config_para['ethplorer']['api_key']
        getTopTokenHolders_url = config_para['ethplorer']['getTopTokenHolders']
        getTopTokenHolders_url = getTopTokenHolders_url + request.form['token']
        r1 = requests.get(getTopTokenHolders_url,params={'apiKey':api_key,'limit':config_para['ethplorer']['limit']})
        getTokenInfo_url = config_para['ethplorer']['getTokenInfo']
        getTokenInfo_url = getTokenInfo_url + request.form['token']
        r11 = requests.get(getTokenInfo_url,params={'apiKey':api_key,'limit':config_para['ethplorer']['limit']})
        if (r1.status_code != 200) or (r11.status_code != 200):
            return abort(404)
        else:
            data = json.loads(r1.text)
            tokeninfo = json.loads(r11.text)['name']
            df = pd.DataFrame.from_dict(data['holders'])
            df['Requested_Token_Name'] = tokeninfo
            list_of_addr = df['address'].to_list()
            i = 0
            othertokens_list = []
            while i < len(list_of_addr):
                getAddressInfo_url = config_para['ethplorer']['getAddressInfo']
                getAddressInfo_url = getAddressInfo_url + list_of_addr[i]
                r2 = requests.get(getAddressInfo_url,params={'apiKey':api_key,'showETHTotals':False})
                if r2.status_code == 200:
                    addressinfo = json.loads(r2.text)
                    j = 0
                    holdertokens = []
                    possession_limit = min(config_para['ethplorer']['holdings'],len(addressinfo['tokens']))
                    while j < possession_limit:
                        eachtoken = []
                        if 'address' in addressinfo['tokens'][j]['tokenInfo']:
                            eachtoken.append(addressinfo['tokens'][j]['tokenInfo']['address']) 
                        if 'name' in addressinfo['tokens'][j]['tokenInfo']:
                            eachtoken.append(addressinfo['tokens'][j]['tokenInfo']['name'])
                        if 'balance' in addressinfo['tokens'][j]:
                            eachtoken.append(addressinfo['tokens'][j]['balance'])
                        if 'balance' in addressinfo['tokens'][j] and 'totalSupply' in addressinfo['tokens'][j]['tokenInfo']:
                            if int(addressinfo['tokens'][j]['tokenInfo']['totalSupply']) > 0:
                                eachtoken.append(round(int(addressinfo['tokens'][j]['balance']) / int(addressinfo['tokens'][j]['tokenInfo']['totalSupply'] ),2))
                        holdertokens.append(eachtoken)
                        j += 1
                    othertokens_list.append(holdertokens)
                else:
                    othertokens_list.append(r2.text)
                i += 1
            df['temp'] = othertokens_list
            data = list(zip(df["address"].to_list(), df["Requested_Token_Name"].to_list(),df["balance"].to_list(), df["share"].to_list(), df["temp"].to_list()))
            return render_template('token-holders-info.html',users=data)
    else:
        return redirect(url_for('home'))

@app.route('/compare-holders',methods=['GET','POST'])
def compare_holders():
    if request.method=='POST':
        with open('config.yaml') as configfile:
            config_para = yaml.load(configfile,Loader=yaml.FullLoader)
        api_key = config_para['ethplorer']['api_key']
        getTopTokenHolders_url = config_para['ethplorer']['getTopTokenHolders']
        getTopTokenHolders_url = getTopTokenHolders_url + request.form['token1']
        r3 = requests.get(getTopTokenHolders_url,params={'apiKey':api_key,'limit':config_para['ethplorer']['compareaddresses']})
        getTopTokenHolders_url = config_para['ethplorer']['getTopTokenHolders']
        getTopTokenHolders_url = getTopTokenHolders_url + request.form['token2']
        r4 = requests.get(getTopTokenHolders_url,params={'apiKey':api_key,'limit':config_para['ethplorer']['compareaddresses']})
        if (r3.status_code != 200) or (r4.status_code != 200):
            print(r3.status_code)
            print(r4.status_code)
            return abort(404)
        else:
            r3_data = json.loads(r3.text)
            r4_data = json.loads(r4.text)
            w = 0
            r3_holders_list = []
            r4_holders_list = []
            while w < len(r3_data['holders']):
                r3_holders_list.append(r3_data['holders'][w]['address'])
                w += 1
            w = 0 
            count_common_addr = 0
            while w < len(r4_data['holders']):
                r4_holders_list.append(r4_data['holders'][w]['address'])
                if r4_data['holders'][w]['address'] in r3_holders_list:
                    count_common_addr += 1
                w += 1
            return render_template('compare-holders.html',users=count_common_addr)
    else:
        return redirect(url_for('home'))

@app.errorhandler(404)
def data_not_found(error):
    return render_template('data_not_found.html'),404