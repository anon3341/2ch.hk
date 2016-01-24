"""
Сагамет 1.0
-------
С 23.01.2016 не работает как раньше
Раньше с айпишников рф и топ-8 стран можно было постить без капчи
Теперь нужно ввести первый раз капчу и айпишник попадает в вайтлист, далее капчу вводить не нужно
Можете запустить скрипт и убедится что он работает, однако сагать он не будет, но будет выводить ошибку по которой ему не получается постить
Так же можно прикрутить разгадывание капчи и скрипт снова заработает, однако придется разгадать 20-50 капч во время работы скрипта

Для работы скрипта необходимо создать пустой файл good_proxies.txt в папке со скриптом
"""

import requests, threading, time, random, re, queue
from bs4 import BeautifulSoup

thread = input('Введите номер треда: \n')
code = '856265569' # Код, необходимый для добывания проксей с hideme.ru

threads_num = 20  # кол-во потоков
post_num = 20     # кол-во постов за поток

with open('good_proxies.txt', 'r') as f: good_proxies = f.read().splitlines()

q = queue.Queue(); qg = queue.Queue()
pn_proxies = []
payload = {
  'task': ('', 'post'),
  'board': ('', 'b'),
  'thread': ('', thread),
  'captcha_type': ('', 'recaptcha'),
  'email': ('', 'sage'),
  'comment': ('', ''),
  'sage': ('', 'on')
  }

# Далее происходит граббинг проксей в зоне РФ

with requests.Session() as s:
  r = s.post('https://hideme.ru/loginn', data={'c': code})
  r1 = s.get('http://hideme.ru/api/proxylist.txt?maxtime=5000&country=BYRUUAGB&out=plain')
  
r2 = requests.get('http://freeproxy-list.ru/api/proxy?accessibility=80&anonymity=false&country=BY%2CRU%2CUA%2CGB&token=demo')
r3 = requests.get('http://dogdev.net/Proxy/api/text/RU/r')
r4 = requests.get('http://txt.proxyspy.net/proxy.txt')
r5 = requests.get('http://www.proxynova.com/proxy-server-list/country-ru/')
r6 = requests.get('http://api.foxtools.ru/v2/Proxy', params={'country': 'RU'})
r7 = requests.get('http://www.idcloak.com/proxylist/russian-proxy-list.html')
r8 = requests.get('http://www.gatherproxy.com/proxylist/country/?c=russia')

soup = BeautifulSoup(r5.content, "html.parser")
tr = soup.findAll('tr')
for td in tr:
  try: pn_proxies.append(td.findAll('span', {'class': "row_proxy_ip"})[0].text + ':' + td.findAll('a', {'href': re.compile('/port')})[0].text)
  except Exception: pass

soup = BeautifulSoup(r7.content, "html.parser")
idcloak_list = ['%s:%s' %(i.findAll('td')[-1].text, i.findAll('td')[-2].text) for i in soup.findAll('tr')[12:]]

soup = BeautifulSoup(r8.content, "html.parser")
gatherproxy_list = ['%s:%s' %(re.findall(r'"PROXY_IP":"([\d\.]+)"', i.text)[0], int(re.findall(r'"PROXY_PORT":"(\w+)"', i.text)[0], 16)) for i in soup.findAll('script', {'type':'text/javascript'})[4:-4]]

proxy_lst = str(r1.text).splitlines() + str(r2.text).splitlines() + str(r3.text).splitlines()[1:] + \
re.findall(r'(\d+\.\d+\.\d+\.\d+:\d+)\sRU', r4.text) + ['%s:%s' %(i['ip'], i['port']) for i in r6.json()['response']['items']] + \
pn_proxies + good_proxies + idcloak_list + gatherproxy_list

proxy_lst = list(set(proxy_lst))
print('Прокси загружено: ' + str(len(proxy_lst)))

lock = threading.Lock()

def req(q, thread):
  while not q.empty():
    try:
      with lock:
        r = requests.get('https://2ch.hk/b/res/%s.json' %(thread), timeout=5)
      posts = [i['comment'].replace('<br>', '\n').replace('</br>', '\n').replace(' (OP)', '') for i in r.json()['threads'][0]['posts']]
      posts = [BeautifulSoup(i, "html.parser").text for i in posts]
      if int(r.json()['posts_count']) >= 500: return
      proxy = q.get()
      time.sleep(random.randint(1,19))
      for i in range(post_num):
        payload['comment']=('', posts[random.randint(1, len(posts)-1)])
        try: r = requests.post('https://2ch.hk/makaba/posting.fcgi',
                          files=payload, params={'json':'1'},
                          proxies=proxy,
                          timeout=5)
        except Exception: continue
        if r.json()['Error'] == None: qg.put(proxy)
        else: print(r.json()); break
        print('Сообщение успешно отправлено с прокси: ' + str(proxy))
        time.sleep(random.randint(16,19))
    except Exception: continue
    finally:
      q.task_done()
      print(q.qsize())
  
for proxy in proxy_lst:
  q.put({'https': 'http://' + proxy})
  
for thr in range(threads_num):
  thr = threading.Thread(target=req, args=(q,thread))
  thr.start()

q.join()

good_proxies = list(set(map(str,qg.queue)))
good_proxies = [re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', i)[0] for i in good_proxies]
with open('good_proxies.txt', 'w') as f: f.write('\n'.join(good_proxies))
