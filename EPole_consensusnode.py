# -*- coding: utf-8 -*-
'''
E2Pole Consensus Node Demo
'''
import sys  
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QTextBrowser
from PyQt5.QtCore import *
import time
import random
import hashlib
import threading
import requests
from flask import *
import sklearn.datasets as set
from sklearn.ensemble import VotingClassifier
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import log_loss

X, y = set.make_moons(noise=0.5)
X_train, X_test,y_train, y_test = train_test_split(X,y,train_size=0.2, test_size=0.2)
rewards = []
class Worker(QThread):
    sinOut = pyqtSignal(str) 
    def __init__(self, parent=None):
        global app
        super(Worker, self).__init__(parent)
        self.app = app
        self.working = True
        self.port = -1
        self.addr = ''
        self.ipaddr = ''
        self.num = 0
        self.block = []
        self.node_list = []
        self.taskhashlist = []
        self.requestli_cache = []
        self.flag=1
        self.block_cache = []
        self.base_model_cache = []
        self.contribute_dict= []
        self.balance=0
    def register(self):
        print('NODE LIST {}'.format(self.node_list))
        for ip in self.node_list:
            if ip == self.ipaddr:
                continue
            try:
                requests.post('{}/pole/protocol/addnode'.format(ip), json={'ipaddr':self.ipaddr, 'selfaddr': self.addr})
            except Exception as e:
                print('[E1]:{}'.format(e))

    def configargs(self, port, nodes, addr, blocks):
        self.flag=1
        self.port = port
        self.node_list = nodes
        self.addr = addr
        self.ipaddr = 'http://127.0.0.1:{}'.format(self.port)
        self.node_list.append(self.ipaddr)
        print(self.node_list)
        self.block = blocks
        self.register()

    def train_base_model(self):
        print("Money ")
        print(self.balance)
        '''
        if not self.base_model_cache:
            self.base_model_cache = [{'acc': None,'bases model': None, 'ipaddr': None, 'selfaddr': None}]
        '''
        t= time.time()
        '''
        generate_base_model()

        '''
        choice = ['lbfgs', 'sgd', 'adam']
        solver = choice[random.randint(0, 2)]
        model = MLPClassifier(activation='relu', solver=solver, max_iter=3000, hidden_layer_sizes=(random.randint(2,4), random.randint(250,500)))
        model.fit(X_train,y_train)
        score = model.score(X_test, y_test)
        #传入
        basemodel=model
        acc=score
        '''
        filename = './1.txt'                              #写入文件并提取
        with open(filename, 'w') as file_object:
            file_object.write("Add a word")
        '''
        s=time.time()-t
        if s<30:      
            for ip in self.node_list:              #全网广播base model
                if ip == self.ipaddr:
                    continue
                try:
                    requests.post('{}/consensus/v2/get_base_model'.format(ip), files=basemodel, json={'ipaddr':self.ipaddr, 'selfaddr': self.addr,'acc':acc})
                except Exception as e:
                    print('[E1]:{}'.format(e))
            
            base_model = {'acc': acc, 'base model':basemodel,'ipaddr':self.ipaddr, 'selfaddr': self.addr}
            print(base_model)
            self.base_model_cache.append(base_model)
            print(self.base_model_cache)
            print(len(self.base_model_cache))
            return base_model
        else:
            return
    
    def generate_ensemble_model(self,t,basemodel_list):
        choice = ['lbfgs', 'sgd', 'adam']
        ini_weight = [0 for i in range(0,len(basemodel_list))]
        add_weight_dic = {}
        before_weight = ini_weight
        after_weight = ini_weight
        before_loss = 0
        # 这次 调整过后的权重列表
        after_loss = 0
        # 上次增加权重的模型编号 第一次可以变为 0
        model_number = -1
        score = 0
        #一个是loss  一个是字典key排序
        model = VotingClassifier(estimators=basemodel_list, voting='hard', weights=ini_weight)
        model.fit(X_train,y_train)
        pre_list = model.predict(X_test)
        before_loss = log_loss(y_test, pre_list) #计算 model 的 loss
        print(model.score(X_test,y_test))
        print(before_loss)
        while time.time()-t<50:
            # 轮次对模型进行 +1
            # 循环内代码：
            if after_loss < before_loss and model_number!= -1:
                before_weight = after_weight
                after_weight[model_number] += 0.1
            else:
                after_weight = before_weight
                if model_number < len(basemodel_list)-1:
                    model_number += 1
                else:
                    model_number = 0

                after_weight[model_number] += 0.1
            #计算 loss
            model = VotingClassifier(estimators=basemodel_list,voting='hard',weights=after_weight)
            model.fit(X_train,y_train)
            #befor_loss 计算未改变权重前的loss值
            before_loss = after_loss
            pre_list = model.predict(X_test)
            after_loss = log_loss(y_test, pre_list)  # 计算 model 的 loss
            print('loss: ')
            print(after_loss)
            print('score: ')
            print(model.score(X_test,y_test))
        # i是地址 j是模型
        num = 0
        for i,j in basemodel_list:
            add_weight_dic[i] = before_weight[num]
            num += 1
        # 返回 准确率 模型 权重-地址对应 字典
        score = model.score(X_test,y_test)
        return score,model,add_weight_dic

    def train_ensemble_model(self,t):
        print(t)
        acc=0
        base_models=[]
        for i in range(len(self.base_model_cache)):
            base_models.append((self.base_model_cache[i]['selfaddr'],self.base_model_cache[i]['base model']))
        print(base_models)
        '''
        train_ensemble_model()

        '''
        acc,ensemble_model,contribute_dict=self.generate_ensemble_model(t,base_models)

        return ensemble_model,contribute_dict,acc
    
    def generate_block(self):
        print('BASE MODEL CACHE: {}'.format(self.base_model_cache))
        self.flag=2
        if not self.requestli_cache:
           self.requestli_cache = [{'balance': 0, 'data': 'Default', 'model': None, 'addr': None, 'taskhash': None}]
        
        t=time.time()
        print(len(self.base_model_cache))
        ensemble_model, self.contribute_dict, acc = self.train_ensemble_model(t)
        self.contribute_dict[self.addr] = 1./(len(self.base_model_cache)+1)
        #奖励机制
        
        self_block = {'acc':acc,'timestamp':time.time(),'addr': self.addr,'donetask': self.requestli_cache[0],'body':{'msg': self.requestli_cache},'contributor':self.contribute_dict, 'coinbase':10, 'ensemble model': ensemble_model}
        if time.time()-t<60:                
            for ip in self.node_list:              #全网广播 block
                if ip == self.ipaddr:
                    continue
                try:
                    requests.post('{}/v2/consensus/'.format(ip), json=self_block)
                except Exception as e:
                    print('[E1]:{}'.format(e))
        self.block_cache.append(self_block)
        self.flag=1
        return 
            

    def get_winner(self):
        self.flag=0
        print('BLOCK CACHE: {}'.format(self.block_cache))
        # use local block cache
        if not self.block_cache:
            return
        maxacc = -1
        winner_addr = ''
        bidx = None
        for idx in range(len(self.block_cache)):
            print('SEE', idx, self.block_cache[idx]['acc'], maxacc)
            if self.block_cache[idx]['acc'] > maxacc:
                maxacc = self.block_cache[idx]['acc']
                winner_addr = self.block_cache[idx]['addr']
                bidx = idx
        # select the best performance one
        if winner_addr == self.addr:
            print('[Winner]:{}'.format(self.block_cache[bidx]))
            self.sinOut.emit('TOKENS:{}'.format(self.block_cache[bidx]['body']['msg'][0]['balance']))
        if len(self.requestli_cache) >= 1:
            self.requestli_cache = self.block_cache[bidx]['body']['msg'][1:]
        else:
            self.requestli_cache = [{'balance': 0, 'data': 'Default', 'model': None, 'addr': None, 'taskhash': None}]
        self.block.append(self.block_cache[bidx])
        self.block_cache = []
        self.base_model_cache = []
        self.contribute_dict = []
        self.sinOut.emit('4')
        self.flag=1
        return
    
    def run(self):
        app = Flask(__name__)

        @app.route('/')
        def index():
            return '<h1>Welcome using E2PoLe Demo</h1>', 200

        @app.route('/pole/protocol/V1')
        def protocol():
            return jsonify({'port': self.port, 'status': 'working', 'addr': self.addr, 'msg':200, 'nodes': self.node_list, 'blocks': self.block}), 200

        @app.route('/pole/protocol/addnode', methods=['POST'])
        def add_node():
            self.sinOut.emit('1')   #sin==signal emit==发出
            jsondata = json.loads(request.get_data())
            self.node_list.append('{}'.format(jsondata['ipaddr']))
            print(self.node_list)
            return jsonify({'msg': 200}), 200

        @app.route('/get-request', methods=['POST'])
        def get_request():
            self.sinOut.emit('2')
            datanoderequest = json.loads(request.get_data())
            taskhash = datanoderequest['taskhash']
            if taskhash in self.taskhashlist:
                return jsonify({'msg': 200}), 200
            self.requestli_cache.append(datanoderequest)
            self.taskhashlist.append(taskhash)
            t1 = threading.Thread(target=broadcastinvf, args=(self.node_list, datanoderequest, self.ipaddr))
            t1.start()

            return ({'msg': 200}), 200

        def broadcastinvf(nodelist, requestdata, selfip):
            for ip in nodelist:
                try:
                    if ip == selfip:
                        continue
                    requests.post('{}/get-request'.format(ip), json=requestdata)
                except Exception as e:
                    print('[E4]:{}'.format(e))

        @app.route('/explore')
        def explore():
            return jsonify(self.block), 200
        
        @app.route('/datanode/ifdone/<taskhash>', methods=['GET'])
        def datanoderequest(taskhash):
            for idx in range(len(self.block)-1, 0, -1):
                if self.block[idx]['donetask']['taskhash'] == taskhash:
                    return jsonify({'code': 200, 'blockidx': idx, 'msg': 'task is done', 'hash': taskhash, 'content': '<Model><Weight></Weight></Model>'}), 200
            return jsonify({'code': 500, 'msg': 'task wait in queue.'})
        
        @app.route('/consensus/v2/get_base_model', methods=['POST', ])
        def getbasemodel():
            if self.flag==2:
                return 500
            self.sinOut.emit('5')
            basemodel=request.files['files']
            jsondata=json.loads(request.get_data())
            ipaddr=jsondata['ipaddr']
            addr=jsondata['addr']
            acc=jsondata['acc']
            base_model={'acc': acc, 'base model':basemodel,'ipaddr':ipaddr, 'selfaddr': addr}
            self.base_model_cache.append(base_model)
            return jsonify({'code': 200, 'msg': 'get base models.'})
        
        @app.route('/v2/consensus', methods=['POST',])
        def consensus():
            self.sinOut.emit('3')
            #增加时间是否超过590s
            if self.flag==0:
                return 500
            
            self.block_cache.append(json.loads(request.get_data()))
            return jsonify({'msg': 'get consensus.'}), 200
        
        @app.route('/v2/consensus',methods=['POST'])
        def getrewards():
            jsondata=json.loads(request.get_data())
            contribute=jsondata['contributor']
            money=jsondata['coinbase']
            balance=contirbute[self.addr]*money
            self.balance=self.balance+balance
            return jsonify({'msg': 'get rewards'}), 200

        app.run(port=self.port, threaded=True)

        
class FirstUi(QMainWindow): 

    def __init__(self, port, extnodeli, extblockli):
        super(FirstUi, self).__init__()
        self._echo = ''
        self._count = 2253
        self.r = None
        self.b = 1000
        self.language = 0
        self.port = port
        self.extnodeli = extnodeli
        self.thread = Worker()
        r = hashlib.sha256(bytes(str(random.random()), encoding='utf8')).hexdigest()
        print('self addr: {}'.format(r))
        self.r = r
        self.thread.sinOut.connect(self.interrupt1)
        self.thread.configargs(port=self.port, addr=r, nodes=extnodeli, blocks=extblockli)
        self.thread.start()
        self.c1 = 100      #总进程
        self.c2 = 20      #集成模型训练时间点
        self.c3 = 90      #达成共识时间点
        self.countdown1 = self.c1 
        self.countdown2 = self.c2 
        self.countdown3 = self.c3

        '''
        self.dataset_b = 
        self.dataset_e = 
        '''

        self.model = 'model'
        self.role = random.choice([1, 2]) # train base model only; 1 train emssemble model also; 2 train emsemble only
        print(self.role)

        self.init_ui()
        if self.role <= 2:
            self.do_at_first()
    
    def do_at_first(self):
        # train base model at first ()
        self.thread.train_base_model()
        
        pass

    def init_ui(self):

        self.resize(800, 400)  
        self.setWindowTitle('Consensus Node') 

        self.lable1 = QLabel('<h1>E2PoLe Demo</h1>', self)
        self.lable1.setGeometry(330, 20, 300, 25)

        self.lable3 = QLabel('<h2>Consensus Node</h2>', self)
        self.lable3.setGeometry(320, 50, 300, 25)

        self.lable4 = QLabel('IP : http://127.0.0.1:{}'.format(self.port), self)
        self.lable4.setGeometry(550, 15, 300, 25)

        self.lable5 = QLabel('Console:', self)
        self.lable5.setGeometry(240, 70, 300, 25)

        self.lable6 = QLabel('<h2>Balance:</h2>', self)
        self.lable6.setGeometry(30, 50, 300, 25)

        self.lable7 = QLabel('<h2>Address:</h2>', self)
        self.lable7.setGeometry(30, 200, 300, 25)

        self.lable8 = QLabel('<h1>{}</h1>'.format(self.b), self)
        self.lable8.setGeometry(30, 90, 300, 25)
        a=self.r[:8]+'**'
        self.lable9 = QLabel('<h1>{}</h1>'.format(a), self)
        self.lable9.setGeometry(30, 240, 300, 25)

        self.lable10 = QLabel('<h2>Status:</h2>', self)
        self.lable10.setGeometry(30, 320, 300, 25)

        self.lable11 = QLabel('<h1>Working</h1>', self)
        self.lable11.setGeometry(30, 340, 300, 50)

        self._echo = """      Event       |   Entity  |       Time       |  IP Addr"""

        self.tb = QTextBrowser(self)
        self.tb.setText(self._echo)
        self.tb.setGeometry(240, 100, 500, 220)

        self.btn5 = QPushButton('Refresh', self)  
        self.btn5.setGeometry(320, 320, 100, 25)  
        self.btn5.clicked.connect(self.slot_btn_function)  

        self.lable2 = QLabel('Status: Collecting Requests...', self)
        self.lable2.setGeometry(450, 320, 300, 25)

        self.btn6 = QPushButton('ZH/EN', self)
        self.btn6.setGeometry(10, 10, 70, 25)
        self.btn6.clicked.connect(self.changeLanguage)

        self.timer = QBasicTimer()  
        self.timer.start(1000, self)


    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            if self.countdown1 == 0: # 600s
                self.role = random.choice([1,2,3])
                self.countdown1 = self.c1
                self.countdown2 = self.c2
                self.countdown3 = self.c3
                if self.role == 1:
                    self.thread.train_base_model()
                    self.lable2.setText("Start training base model.")
                if self.role == 2:
                    self.thread.train_base_model()
                    self.lable2.setText("Start training base model.")
                if self.role == 3:
                    self.lable2.setText("Waiting for another task.")
            else:
                self.countdown1 -= 1
                #print(self.countdown1)

            if self.countdown2 == 0: # 480s
                if self.role == 1:
                    self.countdown2 = self.c1
                    self.lable2.setText("Waiting for another task.")
                if self.role == 2:
                    self.countdown2 = self.c1
                    self.thread.generate_block()
                    self.append_echo('Have received base models.')
                    self.lable2.setText("Start training ensemble model and generating block.")
                if self.role == 3:
                    self.countdown2 = self.c1
                    self.thread.generate_block()
                    self.append_echo('Have received base models.')
                    self.lable2.setText("Start training ensemble model and generating block.")
            else:

                self.countdown2 -= 1
                #print(self.countdown2)

            if self.countdown3 == 0: # 590s
                self.countdown3 = self.c1
                self.thread.get_winner()
                self.lable2.setText("Getting Winner.")
            else:
                self.countdown3 -= 1
                #print(self.countdown3)
            
    def slot_btn_function(self):

        pass

    def changeLanguage(self):

        if self.language == 1:
            self.language = 0
            self.lable1.setText('<h1>E2PoLe Demo</h1>')
            self.lable3.setText('<h2>Consensus Node</h2>')
            self.lable4.setText('IP : http://127.0.0.1:{}'.format(self.port))
            self.lable5.setText('Console:')
            self.lable6.setText('<h2>Balance:</h2>')
            self.lable7.setText('<h2>Address:</h2>')
            self.lable10.setText('<h2>Status:</h2>')
            self.lable11.setText('<h1>Working</h1>')

            self.btn5.setText('refresh')

        elif self.language == 0:
            self.language = 1
            self.lable1.setText('<h2>E2PoLe 示例</h2>')
            self.lable3.setText('<h2>共识节点</h2>')
            self.lable4.setText('IP地址 : http://127.0.0.1:{}'.format(self.port))
            self.lable5.setText('控制台:')
            self.lable6.setText('<h2>余额:</h2>')
            self.lable7.setText('<h2>地址:</h2>')
            self.lable10.setText('<h2>状态:</h2>')
            self.lable11.setText('<h1>正在工作</h1>')

            self.btn5.setText('刷新')

    def append_echo(self, msg):

        self._echo += """{}      | {}|  {} |  127.0.0.1:{}
-----------------------------------------------------------------------
        """.format(msg, hashlib.md5(bytes(msg+str(time.time()), encoding='utf8')).hexdigest()[:10], time.time(), self.port)
        self.tb.setText(self._echo)

    def interrupt1(self, sig):
        if sig == '1':
            self.append_echo('A new node registered.')

        if sig == '2':
            self.append_echo('Receive new request.')

        if sig == '3':
            self.append_echo('Received new block.')

        if sig == '4':
            self.append_echo('Consensus reached.')
            self.lable2.setText("Status: Collecting Requests...")
 
        if sig == '5':
            self.append_echo('Base model training finished.')

        if 'TOKENS' in sig:
            self.append_echo('Became winner.')
            fee = str(sig)
            print('[FEE]:{}'.format(fee))
            self.lable8.setText("<h1>{}</h1>".format(self.b + int(fee.split(':')[-1])))
            print('[NOW FEE]:{}'.format(self.b + int(fee.split(':')[-1])))
            self.b += int(fee.split(':')[-1])

def get_a_port():
    originp = 7000
    FLAG = True
    nodelist = []
    blocklist = []

    while FLAG:
        try:
            req = requests.get('http://127.0.0.1:{}/pole/protocol/V1'.format(originp))
            jsondata = json.loads(req.content)
            nodelist = jsondata['nodes']
            blocklist = jsondata['blocks']
            originp += 1
        except:

            FLAG = False

    return originp, nodelist, blocklist


if __name__ == '__main__': 

    appmain = QApplication(sys.argv)
    w = FirstUi(*get_a_port())  # 将第一和窗口换个名字
    w.show()  # 将第一和窗口换个名字显示出来
    sys.exit(appmain.exec_())  # app.exet_()是指程序一直循环运行直到主窗口被关闭终止进程（如果没有这句话，程序运行时会一闪而过）
